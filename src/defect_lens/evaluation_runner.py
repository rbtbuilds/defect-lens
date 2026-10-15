import json
import sys
import time
from pathlib import Path

from defect_lens.contracts import DatasetManifest
from defect_lens.evaluation import evaluate_one


def api_timing(
    dataset: DatasetManifest, root: Path, directory: Path, output: Path, token: str
) -> None:
    from uuid import uuid4

    from fastapi.testclient import TestClient

    from defect_lens.api import create_app
    from defect_lens.config import Settings
    from defect_lens.models import read_model_manifest

    model = read_model_manifest(directory)
    settings = Settings(output / "api-run", directory, feature_lease_token=token)
    timings: list[float] = []
    with TestClient(create_app(settings)) as client:
        deadline = time.monotonic() + 30
        while client.get("/readyz").status_code != 200:
            if time.monotonic() > deadline:
                raise RuntimeError("Benchmark API worker failed readiness")
            time.sleep(0.05)
        chosen = {sample.label: sample for sample in dataset.samples if sample.split == "test"}
        for sample in chosen.values():
            started = time.perf_counter_ns()
            with (root / sample.image_path).open("rb") as image:
                response = client.post(
                    "/api/jobs",
                    files={"image": ("image", image, "image/png")},
                    data={"model_revision": model.revision, "data_mode": dataset.mode},
                    headers={"Idempotency-Key": str(uuid4())},
                )
            if response.status_code != 202:
                raise RuntimeError("Benchmark upload failed")
            job = response.json()
            deadline = time.monotonic() + 60
            while job["status"] in {"queued", "running"}:
                if time.monotonic() > deadline:
                    raise RuntimeError("Benchmark API deadline")
                time.sleep(0.02)
                job = client.get(f"/api/jobs/{job['id']}").json()
            if job["status"] != "succeeded":
                raise RuntimeError("Benchmark API inspection failed")
            client.get(f"/api/inspections/{job['inspection_id']}").raise_for_status()
            timings.append((time.perf_counter_ns() - started) / 1e6)
    (output / "api-timing.json").write_text(json.dumps(timings))


if __name__ == "__main__":
    data = DatasetManifest.model_validate_json(Path(sys.argv[1]).read_bytes())
    root, model, output = map(Path, sys.argv[2:5])
    if "--api" in sys.argv:
        api_timing(data, root, model, output, sys.argv[5])
    else:
        report = evaluate_one(data, model, root, output, sys.argv[5])
        (output / "method-report.json").write_text(report.model_dump_json(indent=2) + "\n")
