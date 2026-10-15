import json
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx

from defect_lens.contracts import DatasetManifest, Job, JobError
from defect_lens.manifests import contained
from defect_lens.routes import ModelMetadata


@dataclass(frozen=True)
class BatchSummary:
    submitted: int
    succeeded: int
    failed: int

    @property
    def exit_code(self) -> int:
        return 4 if self.failed else 0


def create_client(api_url: str) -> httpx.Client:
    return httpx.Client(base_url=api_url, timeout=15)


def run_batch(manifest: Path, api_url: str, output: Path) -> BatchSummary:
    data = DatasetManifest.model_validate_json(manifest.read_bytes())
    if len(data.samples) > 100:
        raise ValueError("Batch maximum is 100 samples")
    if api_url != "http://127.0.0.1:8111":
        raise ValueError("Batch v1 targets the reserved loopback API")
    output.parent.mkdir(parents=True, exist_ok=True)
    succeeded = failed = submitted = 0
    with create_client(api_url) as client, output.open("w") as stream:
        discovery_error: JobError | None = None
        metadata: ModelMetadata | None = None
        try:
            response = client.get("/api/models")
            response.raise_for_status()
            metadata = ModelMetadata.model_validate(response.json())
            if (
                metadata.status != "ready"
                or metadata.model_revision is None
                or metadata.data_mode != data.mode
            ):
                discovery_error = JobError(
                    code="MODEL_UNAVAILABLE",
                    message="Selected model is not ready for this data mode",
                    retryable=True,
                )
        except (ValueError, httpx.HTTPError):
            discovery_error = JobError(
                code="MODEL_UNAVAILABLE",
                message="API model discovery failed; check local server health",
                retryable=True,
            )
        for sample in data.samples:
            record: dict[str, object] = {"sample_id": sample.id}
            if discovery_error is not None or metadata is None:
                failed += 1
                record["error"] = (
                    discovery_error
                    or JobError(code="MODEL_UNAVAILABLE", message="No selected model")
                ).model_dump()
            else:
                try:
                    path = contained(manifest.parent, sample.image_path)
                    with path.open("rb") as image:
                        response = client.post(
                            "/api/jobs",
                            files={"image": ("image", image, "application/octet-stream")},
                            data={
                                "model_revision": metadata.model_revision,
                                "data_mode": data.mode,
                            },
                            headers={"Idempotency-Key": str(uuid4())},
                        )
                    response.raise_for_status()
                    submitted += 1
                    job = Job.model_validate(response.json())
                    deadline = time.monotonic() + 60
                    while job.status in {"queued", "running"} and time.monotonic() < deadline:
                        time.sleep(0.1)
                        response = client.get(f"/api/jobs/{job.id}")
                        response.raise_for_status()
                        job = Job.model_validate(response.json())
                    record["job"] = job.model_dump()
                    if job.status == "succeeded":
                        succeeded += 1
                    else:
                        failed += 1
                except (OSError, ValueError, httpx.HTTPError):
                    failed += 1
                    record["error"] = JobError(
                        code="BATCH_ITEM_FAILED",
                        message="Submission or processing failed; inspect API status and input manifest",
                        retryable=True,
                    ).model_dump()
            stream.write(json.dumps(record, allow_nan=False) + "\n")
            stream.flush()
    return BatchSummary(submitted, succeeded, failed)
