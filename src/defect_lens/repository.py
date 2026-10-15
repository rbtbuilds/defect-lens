import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from defect_lens.config import Settings
from defect_lens.contracts import (
    AcceptedInput,
    Inspection,
    Job,
    JobError,
    Review,
    ReviewCreate,
    StoredResult,
    UploadForm,
)
from defect_lens.db import connect, migrate, transaction
from defect_lens.errors import DomainError
from defect_lens.manifests import contained
from defect_lens.models import ModelManifest, canonical

RESERVATION = 1024 * 1024


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def job_from(row: sqlite3.Row) -> Job:
    return Job(
        id=row["id"],
        status=row["status"],
        model_revision=row["model_revision"],
        data_mode=row["data_mode"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        inspection_id=row["inspection_id"],
        error=JobError.model_validate_json(row["error_json"]) if row["error_json"] else None,
    )


def review_from(row: sqlite3.Row) -> Review:
    return Review.model_validate({key: row[key] for key in Review.model_fields})


JOB_SELECT = "SELECT jobs.*, inspections.id AS inspection_id FROM jobs LEFT JOIN inspections ON inspections.job_id=jobs.id"


class Repository:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.active_revision: str | None = None
        migrate(settings.database_path)

    def set_ready(self, revision: str | None) -> None:
        self.active_revision = revision

    def register_model(self, manifest: ModelManifest) -> None:
        with transaction(self.settings.database_path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO models VALUES(?,?,?,?,?)",
                (
                    manifest.revision,
                    manifest.method,
                    manifest.data_mode,
                    manifest.model_dump_json(),
                    now(),
                ),
            )

    def enqueue(
        self, accepted: AcceptedInput, form: UploadForm, key: str, request_hash: str
    ) -> tuple[Job, bool]:
        relative = str(accepted.normalized_path.resolve().relative_to(self.settings.runtime))
        with transaction(self.settings.database_path) as connection:
            existing = connection.execute(
                JOB_SELECT + " WHERE idempotency_key=?", (key,)
            ).fetchone()
            if existing:
                if existing["request_hash"] != request_hash:
                    raise DomainError(
                        "IDEMPOTENCY_CONFLICT", "Key was used for a different request", 409
                    )
                return job_from(existing), True
            if self.active_revision is None:
                raise DomainError("MODEL_UNAVAILABLE", "Selected model is not ready", 503, True)
            model = connection.execute(
                "SELECT * FROM models WHERE revision=?", (self.active_revision,)
            ).fetchone()
            if (
                form.model_revision != self.active_revision
                or model is None
                or form.data_mode != model["data_mode"]
            ):
                raise DomainError(
                    "MODEL_CHANGED", "Refresh the selected model revision and data mode", 409
                )
            count, pending, used = connection.execute(
                "SELECT COUNT(*), COALESCE(SUM(status IN ('queued','running')),0), COALESCE(SUM(reserved_bytes),0) FROM jobs"
            ).fetchone()
            if pending >= self.settings.max_pending:
                raise DomainError("QUEUE_FULL", "Queue is full; retry later", 429, True)
            if (
                count >= self.settings.max_jobs
                or used + RESERVATION > self.settings.max_storage_bytes
            ):
                raise DomainError("STORAGE_LIMIT", "Local storage quota reached", 507)
            job_id = str(uuid4())
            connection.execute(
                "INSERT INTO jobs(id,idempotency_key,request_hash,status,model_revision,data_mode,input_relpath,raw_sha256,metadata_json,created_at,reserved_bytes) VALUES(?,?,?,'queued',?,?,?,?,?,?,?)",
                (
                    job_id,
                    key,
                    request_hash,
                    form.model_revision,
                    form.data_mode,
                    relative,
                    accepted.metadata.raw_sha256,
                    accepted.metadata.model_dump_json(),
                    now(),
                    RESERVATION,
                ),
            )
            row = connection.execute(JOB_SELECT + " WHERE jobs.id=?", (job_id,)).fetchone()
            return job_from(row), False

    def get_job(self, job_id: str) -> Job:
        with connect(self.settings.database_path) as connection:
            row = connection.execute(JOB_SELECT + " WHERE jobs.id=?", (job_id,)).fetchone()
        if row is None:
            raise DomainError("NOT_FOUND", "Job not found", 404)
        return job_from(row)

    def list_jobs(self, limit: int = 30, cursor: str | None = None) -> tuple[list[Job], str | None]:
        if not 1 <= limit <= 100:
            raise DomainError("INVALID_REQUEST", "Limit must be between 1 and 100", 422)
        with connect(self.settings.database_path) as connection:
            rows = connection.execute(
                JOB_SELECT
                + " WHERE jobs.rowid < COALESCE((SELECT rowid FROM jobs WHERE id=?),9223372036854775807) ORDER BY jobs.rowid DESC LIMIT ?",
                (cursor, limit + 1),
            ).fetchall()
        items = [job_from(row) for row in rows[:limit]]
        return items, items[-1].id if len(rows) > limit else None

    def claim_next(self) -> Job | None:
        with transaction(self.settings.database_path) as connection:
            row = connection.execute(
                "SELECT id FROM jobs WHERE status='queued' AND model_revision=? ORDER BY rowid LIMIT 1",
                (self.active_revision,),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "UPDATE jobs SET status='running',started_at=? WHERE id=? AND status='queued'",
                (now(), row["id"]),
            )
            claimed = connection.execute(JOB_SELECT + " WHERE jobs.id=?", (row["id"],)).fetchone()
            return job_from(claimed)

    def input_for(self, job_id: str) -> tuple[Path, str]:
        with connect(self.settings.database_path) as connection:
            row = connection.execute(
                "SELECT input_relpath,metadata_json FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
        if row is None:
            raise DomainError("NOT_FOUND", "Job not found", 404)
        return contained(self.settings.runtime, row["input_relpath"]), row["metadata_json"]

    def complete(self, job_id: str, result: StoredResult) -> Inspection:
        path, _ = self.input_for(job_id)
        size = path.stat().st_size + result.artifact_bytes
        if size > RESERVATION:
            raise DomainError("STORAGE_LIMIT", "Inspection artifacts exceed reservation", 507)
        for relative in result.artifacts.values():
            contained(self.settings.runtime, relative)
        inspection_id = str(uuid4())
        with transaction(self.settings.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE id=? AND status='running'", (job_id,)
            ).fetchone()
            if row is None:
                raise DomainError("STATE_CONFLICT", "Job is not running", 409)
            connection.execute(
                "INSERT INTO inspections VALUES(?,?,?,?,?,?,?,?,0,?)",
                (
                    inspection_id,
                    job_id,
                    row["model_revision"],
                    result.decision,
                    result.score,
                    json.dumps(result.reasons),
                    json.dumps(result.artifacts),
                    json.dumps([r.model_dump() for r in result.regions]),
                    now(),
                ),
            )
            changed = connection.execute(
                "UPDATE jobs SET status='succeeded',finished_at=?,reserved_bytes=? WHERE id=? AND status='running'",
                (now(), size, job_id),
            ).rowcount
            if changed != 1:
                raise DomainError("STATE_CONFLICT", "Job transition failed", 409)
        return self.get_inspection(inspection_id)

    def fail(self, job_id: str, error: JobError) -> None:
        path, _ = self.input_for(job_id)
        # Retained artifacts count even when a crash prevented their database promotion.
        directory = self.settings.runtime / "outputs" / job_id
        stored = (path.stat().st_size if path.exists() else 0) + sum(
            p.stat().st_size for p in directory.glob("*") if p.is_file()
        )
        with transaction(self.settings.database_path) as connection:
            changed = connection.execute(
                "UPDATE jobs SET status='failed',finished_at=?,error_json=?,reserved_bytes=? WHERE id=? AND status IN ('running','queued')",
                (now(), error.model_dump_json(), stored, job_id),
            ).rowcount
            if changed != 1:
                raise DomainError("STATE_CONFLICT", "Job is already terminal", 409)

    def fail_incompatible_queued(self, revision: str) -> int:
        with connect(self.settings.database_path) as connection:
            rows = connection.execute(
                "SELECT id FROM jobs WHERE status='queued' AND model_revision!=?", (revision,)
            ).fetchall()
        for row in rows:
            self.fail(
                row["id"],
                JobError(
                    code="MODEL_CHANGED",
                    message="Queued input belongs to another frozen revision; deliberately resubmit for the selected model",
                ),
            )
        return len(rows)

    def recover_interrupted(self) -> int:
        with connect(self.settings.database_path) as connection:
            rows = connection.execute("SELECT id FROM jobs WHERE status='running'").fetchall()
        for row in rows:
            self.fail(
                row["id"],
                JobError(
                    code="INTERRUPTED",
                    message="Processing interrupted; deliberately resubmit to retry",
                ),
            )
        return len(rows)

    def count_inspections(self, job_id: str) -> int:
        with connect(self.settings.database_path) as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM inspections WHERE job_id=?", (job_id,)
                ).fetchone()[0]
            )

    def reviews(self, inspection_id: str) -> list[Review]:
        with connect(self.settings.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM reviews WHERE inspection_id=? ORDER BY version", (inspection_id,)
            ).fetchall()
        return [review_from(row) for row in rows]

    def get_inspection(self, inspection_id: str) -> Inspection:
        with connect(self.settings.database_path) as connection:
            row = connection.execute(
                "SELECT inspections.*, jobs.data_mode FROM inspections JOIN jobs ON jobs.id=inspections.job_id WHERE inspections.id=?",
                (inspection_id,),
            ).fetchone()
        if row is None:
            raise DomainError("NOT_FOUND", "Inspection not found", 404)
        artifacts: dict[str, str] = json.loads(row["artifacts_json"])
        base = f"/api/inspections/{inspection_id}/artifacts/"
        history = self.reviews(inspection_id)
        return Inspection(
            id=row["id"],
            job_id=row["job_id"],
            model_revision=row["model_revision"],
            data_mode=row["data_mode"],
            original_decision=row["original_decision"],
            score=row["score"],
            reasons=json.loads(row["reasons_json"]),
            normalized_image_url=base + "normalized",
            aligned_image_url=base + "aligned" if "aligned" in artifacts else None,
            heatmap_url=base + "heatmap" if "heatmap" in artifacts else None,
            regions=json.loads(row["regions_json"]),
            latest_review=history[-1] if history else None,
        )

    def artifact(self, inspection_id: str, kind: str) -> Path:
        self.get_inspection(inspection_id)
        with connect(self.settings.database_path) as connection:
            row = connection.execute(
                "SELECT job_id,artifacts_json FROM inspections WHERE id=?", (inspection_id,)
            ).fetchone()
        if kind == "normalized":
            return self.input_for(row["job_id"])[0]
        artifacts: dict[str, str] = json.loads(row["artifacts_json"])
        if kind not in {"aligned", "heatmap"} or kind not in artifacts:
            raise DomainError("NOT_FOUND", "Artifact not available", 404)
        return contained(self.settings.runtime, artifacts[kind])

    def review_replay(self, inspection_id: str, request: ReviewCreate, key: str) -> Review | None:
        digest = hashlib.sha256(canonical(request.model_dump())).hexdigest()
        with connect(self.settings.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM reviews WHERE inspection_id=? AND idempotency_key=?",
                (inspection_id, key),
            ).fetchone()
        if row is None:
            return None
        if row["request_hash"] != digest:
            raise DomainError("IDEMPOTENCY_CONFLICT", "Key was used for a different request", 409)
        return review_from(row)

    def add_review(self, inspection_id: str, request: ReviewCreate, idempotency_key: str) -> Review:
        digest = hashlib.sha256(canonical(request.model_dump())).hexdigest()
        with transaction(self.settings.database_path) as connection:
            replay = connection.execute(
                "SELECT * FROM reviews WHERE inspection_id=? AND idempotency_key=?",
                (inspection_id, idempotency_key),
            ).fetchone()
            if replay:
                if replay["request_hash"] != digest:
                    raise DomainError(
                        "IDEMPOTENCY_CONFLICT", "Key was used for a different request", 409
                    )
                return review_from(replay)
            row = connection.execute(
                "SELECT * FROM inspections WHERE id=?", (inspection_id,)
            ).fetchone()
            if row is None:
                raise DomainError("NOT_FOUND", "Inspection not found", 404)
            if row["review_version"] != request.expected_version:
                raise DomainError(
                    "REVIEW_CONFLICT",
                    "Refresh the latest review before resubmitting; your note is retained",
                    409,
                )
            version = request.expected_version + 1
            review = Review(
                id=str(uuid4()),
                inspection_id=inspection_id,
                version=version,
                decision=request.decision,
                note=request.note,
                operator_alias=request.operator_alias,
                model_revision=row["model_revision"],
                created_at=now(),
            )
            changed = connection.execute(
                "UPDATE inspections SET review_version=? WHERE id=? AND review_version=?",
                (version, inspection_id, request.expected_version),
            ).rowcount
            if changed != 1:
                raise DomainError("REVIEW_CONFLICT", "Refresh the latest review", 409)
            connection.execute(
                "INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    review.id,
                    inspection_id,
                    idempotency_key,
                    digest,
                    version,
                    review.decision,
                    review.note,
                    review.operator_alias,
                    review.model_revision,
                    review.created_at,
                ),
            )
            return review
