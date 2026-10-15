import json
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx

from defect_lens.contracts import DatasetManifest, Job
from defect_lens.manifests import contained


@dataclass(frozen=True)
class BatchSummary:
    submitted: int
    succeeded: int
    failed: int

    @property
    def exit_code(self) -> int:
        return 4 if self.failed else 0


def run_batch(manifest: Path, api_url: str, output: Path) -> BatchSummary:
    data = DatasetManifest.model_validate_json(manifest.read_bytes())
    if len(data.samples) > 100:
        raise ValueError("Batch maximum is 100 samples")
    if api_url != "http://127.0.0.1:8111":
        raise ValueError("Batch v1 targets the reserved loopback API")
    output.parent.mkdir(parents=True, exist_ok=True)
    succeeded = 0
    failed = 0
    submitted = 0
    with httpx.Client(base_url=api_url, timeout=15) as client, output.open("w") as stream:
        metadata = client.get("/api/models").json()
        for sample in data.samples:
            record: dict[str, object] = {"sample_id": sample.id}
            try:
                path = contained(manifest.parent, sample.image_path)
                with path.open("rb") as image:
                    response = client.post(
                        "/api/jobs",
                        files={"image": ("image", image, "application/octet-stream")},
                        data={"model_revision": metadata["model_revision"], "data_mode": data.mode},
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
                record["error"] = (
                    "Submission or processing failed; inspect API status and input manifest"
                )
            stream.write(json.dumps(record, allow_nan=False) + "\n")
            stream.flush()
    return BatchSummary(submitted, succeeded, failed)
