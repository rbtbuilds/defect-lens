import asyncio
import hashlib
import threading
from collections.abc import Generator
from contextlib import contextmanager
from typing import Annotated, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from defect_lens.config import Settings
from defect_lens.contracts import (
    AcceptedInput,
    Contract,
    DataMode,
    Inspection,
    Job,
    JobError,
    Method,
    ModelStatus,
    Review,
    ReviewCreate,
    UploadForm,
)
from defect_lens.errors import DomainError
from defect_lens.imaging import decode_image, inspect_input
from defect_lens.models import canonical
from defect_lens.repository import Repository
from defect_lens.supervisor import Supervisor


def error_response(
    code: str, message: str, status: int, request_id: str | None = None, retryable: bool = False
) -> JSONResponse:
    return JSONResponse(
        {
            "error": JobError(
                code=code,
                message=message,
                retryable=retryable,
                request_id=request_id or str(uuid4()),
            ).model_dump()
        },
        status_code=status,
    )


class UploadGate:
    def __init__(self) -> None:
        self.active = 0
        self.lock = threading.Lock()

    @contextmanager
    def enter(self) -> Generator[None]:
        with self.lock:
            if self.active >= 2:
                raise DomainError(
                    "UPLOAD_BUSY", "Two uploads are already active; retry later", 429, True
                )
            self.active += 1
        try:
            yield
        finally:
            with self.lock:
                self.active -= 1


class BodyLimit:
    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings
        self.gate = UploadGate()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] != "/api/jobs":
            await self.app(scope, receive, send)
            return
        try:
            with self.gate.enter():
                body = bytearray()
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > self.settings.max_body_bytes:
                        raise DomainError("BODY_TOO_LARGE", "Multipart body exceeds 9 MiB", 413)
                    if not message.get("more_body", False):
                        break
                offset = 0

                async def bounded_receive() -> Message:
                    nonlocal offset
                    if offset >= len(body):
                        return {"type": "http.request", "body": b"", "more_body": False}
                    part = bytes(body[offset : offset + 65536])
                    offset += len(part)
                    return {"type": "http.request", "body": part, "more_body": offset < len(body)}

                await self.app(scope, bounded_receive, send)
        except DomainError as error:
            await error_response(
                error.code, error.message, error.status, retryable=error.retryable
            )(scope, receive, send)


class BoundedMultipartParser(MultiPartParser):
    # Body admission precedes this parser; the bounded spool stays in RAM.
    spool_max_size = 10 * 1024 * 1024

    def close_files(self) -> None:
        for file in self._files_to_close_on_error:
            file.close()


async def stream_upload(request: Request, settings: Settings) -> AcceptedInput:
    parser = BoundedMultipartParser(
        request.headers, request.stream(), max_files=1, max_fields=2, max_part_size=1024
    )
    raw = settings.runtime / "tmp" / f"{uuid4()}.upload"
    normalized = settings.runtime / "inputs" / f"{uuid4()}.png"
    raw.parent.mkdir(parents=True, exist_ok=True)
    normalized.parent.mkdir(parents=True, exist_ok=True)
    try:
        form = await parser.parse()
        pairs = form.multi_items()
        if len(pairs) != 3 or {name for name, _ in pairs} != {
            "image",
            "model_revision",
            "data_mode",
        }:
            raise DomainError(
                "INVALID_REQUEST", "Provide exactly one image, model_revision and data_mode", 400
            )
        image = form["image"]
        if (
            not isinstance(image, UploadFile)
            or not isinstance(form["model_revision"], str)
            or not isinstance(form["data_mode"], str)
        ):
            raise DomainError("INVALID_REQUEST", "Invalid upload fields", 400)
        upload_form = UploadForm.model_validate(
            {"model_revision": form["model_revision"], "data_mode": form["data_mode"]}
        )
        request.scope["defect_lens.form"] = upload_form
        total = 0
        with raw.open("wb") as stream:
            while chunk := await image.read(65536):
                total += len(chunk)
                if total > settings.max_image_bytes:
                    raise DomainError("BODY_TOO_LARGE", "Image exceeds 8 MiB", 413)
                stream.write(chunk)

        def normalize() -> AcceptedInput:
            metadata = inspect_input(raw)
            Image.fromarray(decode_image(raw)).save(normalized, format="PNG")
            return AcceptedInput(normalized_path=normalized, metadata=metadata)

        return await asyncio.to_thread(normalize)
    except MultiPartException as error:
        raise DomainError("INVALID_REQUEST", "Malformed multipart upload", 400) from error
    except BaseException:
        normalized.unlink(missing_ok=True)
        raise
    finally:
        raw.unlink(missing_ok=True)
        parser.close_files()


class JobList(Contract):
    items: list[Job]
    next_cursor: str | None


class ReviewList(Contract):
    items: list[Review]


class ModelMetadata(Contract):
    status: ModelStatus
    model_revision: str | None
    method: Method | None
    data_mode: DataMode | None
    low: float | None
    high: float | None
    heatmap_display_max: float | None


def build_router(settings: Settings, repository: Repository, supervisor: Supervisor) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/models", response_model=ModelMetadata)
    def models() -> ModelMetadata:
        manifest = supervisor.manifest
        return ModelMetadata(
            status=supervisor.ready.status,
            model_revision=manifest.revision if manifest else None,
            method=manifest.method if manifest else None,
            data_mode=manifest.data_mode if manifest else None,
            low=manifest.calibration.low if manifest else None,
            high=manifest.calibration.high if manifest else None,
            heatmap_display_max=manifest.calibration.heatmap_display_max if manifest else None,
        )

    @router.post(
        "/jobs",
        response_model=Job,
        status_code=202,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "required": ["image", "model_revision", "data_mode"],
                            "properties": {
                                "image": {"type": "string", "format": "binary"},
                                "model_revision": {"type": "string"},
                                "data_mode": {"enum": ["procedural", "owned_capture"]},
                            },
                        }
                    }
                },
            }
        },
    )
    async def submit(
        request: Request, idempotency_key: Annotated[str | None, Header()] = None
    ) -> JSONResponse:
        accepted = await stream_upload(request, settings)
        retained = False
        try:
            if idempotency_key is None:
                raise DomainError("INVALID_REQUEST", "UUID Idempotency-Key is required", 400)
            key = str(UUID(idempotency_key))
            form = cast(UploadForm, request.scope["defect_lens.form"])
            digest = hashlib.sha256(
                canonical(
                    {
                        "raw_sha256": accepted.metadata.raw_sha256,
                        "model_revision": form.model_revision,
                        "data_mode": form.data_mode,
                    }
                )
            ).hexdigest()
            job, repeated = await asyncio.to_thread(repository.enqueue, accepted, form, key, digest)
            retained = not repeated
            return JSONResponse(job.model_dump(), status_code=200 if repeated else 202)
        except ValueError as error:
            raise DomainError("INVALID_REQUEST", "UUID Idempotency-Key is required", 400) from error
        finally:
            if not retained:
                accepted.normalized_path.unlink(missing_ok=True)

    @router.get("/jobs", response_model=JobList)
    def jobs(
        limit: Annotated[int, Query(ge=1, le=100)] = 30, cursor: UUID | None = None
    ) -> JobList:
        items, next_cursor = repository.list_jobs(limit, str(cursor) if cursor else None)
        return JobList(items=items, next_cursor=next_cursor)

    @router.get("/jobs/{job_id}", response_model=Job)
    def job(job_id: UUID) -> Job:
        return repository.get_job(str(job_id))

    @router.get("/inspections/{inspection_id}", response_model=Inspection)
    def inspection(inspection_id: UUID) -> Inspection:
        return repository.get_inspection(str(inspection_id))

    @router.get("/inspections/{inspection_id}/artifacts/{kind}")
    def artifact(
        inspection_id: UUID, kind: Literal["normalized", "aligned", "heatmap"]
    ) -> FileResponse:
        return FileResponse(repository.artifact(str(inspection_id), kind), media_type="image/png")

    @router.post("/inspections/{inspection_id}/reviews", response_model=Review, status_code=201)
    def review(
        inspection_id: UUID, body: ReviewCreate, idempotency_key: Annotated[UUID, Header()]
    ) -> JSONResponse:
        replay = repository.review_replay(str(inspection_id), body, str(idempotency_key))
        saved = replay or repository.add_review(str(inspection_id), body, str(idempotency_key))
        return JSONResponse(saved.model_dump(), status_code=200 if replay else 201)

    @router.get("/inspections/{inspection_id}/reviews", response_model=ReviewList)
    def reviews(inspection_id: UUID) -> ReviewList:
        repository.get_inspection(str(inspection_id))
        return ReviewList(items=repository.reviews(str(inspection_id)))

    return router
