import time
from pathlib import Path
from uuid import uuid4

import httpx
import psutil

from defect_lens.fixtures import generate_fixtures
from scripts.dev import ROOT, load_records, start, stop


def wait_ready(client: httpx.Client) -> str:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        response = client.get("/readyz")
        if response.status_code == 200:
            return str(response.json()["model_revision"])
        time.sleep(0.1)
    raise AssertionError("API not ready")


def test_real_restart_correction_and_interrupted_worker() -> None:
    stop(ROOT)
    data = generate_fixtures(ROOT / ".runtime/data/fixtures", 20261015)
    good = next(s for s in data.samples if s.split == "test" and s.label == "good")
    image = (ROOT / ".runtime/data/fixtures" / good.image_path).read_bytes()
    model = Path(".runtime/models/demo-difference")
    start(ROOT, model)
    try:
        with httpx.Client(base_url="http://127.0.0.1:8111", timeout=20) as client:
            revision = wait_ready(client)
            key = str(uuid4())

            def submit(body: bytes, request_key: str) -> httpx.Response:
                return client.post(
                    "/api/jobs",
                    files={"image": ("file", body, "image/png")},
                    data={"model_revision": revision, "data_mode": "procedural"},
                    headers={"Idempotency-Key": request_key},
                )

            first = submit(image, key)
            assert first.status_code == 202
            job = first.json()
            deadline = time.monotonic() + 30
            while job["status"] != "succeeded" and time.monotonic() < deadline:
                time.sleep(0.1)
                job = client.get(f"/api/jobs/{job['id']}").json()
            assert job["status"] == "succeeded"
            inspection = client.get(f"/api/inspections/{job['inspection_id']}").json()
            review_key = str(uuid4())
            review = {
                "decision": "review",
                "note": "Restart persistence verified",
                "operator_alias": "e2e",
                "expected_version": 0,
            }
            saved = client.post(
                f"/api/inspections/{inspection['id']}/reviews",
                json=review,
                headers={"Idempotency-Key": review_key},
            )
            assert saved.status_code == 201
            assert submit(b"corrupt", str(uuid4())).status_code == 422
            assert submit(b"x" * (8 * 1024 * 1024 + 1), str(uuid4())).status_code == 413
            api_record = next(
                record for record in load_records(ROOT).processes if record.name == "api"
            )
            children = psutil.Process(api_record.pid).children()
            worker = next(child for child in children if "spawn_main" in " ".join(child.cmdline()))
            identity = worker.create_time()
            worker.suspend()
            interrupted = submit(image, str(uuid4())).json()
            deadline = time.monotonic() + 5
            while (
                client.get(f"/api/jobs/{interrupted['id']}").json()["status"] != "running"
                and time.monotonic() < deadline
            ):
                time.sleep(0.1)
            assert client.get(f"/api/jobs/{interrupted['id']}").json()["status"] == "running"
        stop(ROOT)
        assert (
            not psutil.pid_exists(worker.pid)
            or psutil.Process(worker.pid).create_time() != identity
        )
        start(ROOT, model)
        with httpx.Client(base_url="http://127.0.0.1:8111", timeout=20) as client:
            assert wait_ready(client) == revision
            persisted = client.get(f"/api/inspections/{inspection['id']}").json()
            assert persisted["original_decision"] == inspection["original_decision"]
            assert persisted["latest_review"]["note"] == "Restart persistence verified"
            assert persisted["model_revision"] == revision
            assert (
                client.post(
                    f"/api/inspections/{inspection['id']}/reviews",
                    json=review,
                    headers={"Idempotency-Key": review_key},
                ).status_code
                == 200
            )
            recovered = client.get(f"/api/jobs/{interrupted['id']}").json()
            assert recovered["status"] == "failed" and recovered["error"]["code"] == "INTERRUPTED"
            assert recovered["inspection_id"] is None
            replay = submit(image, key)
            assert replay.status_code == 200 and replay.json()["inspection_id"] == inspection["id"]
    finally:
        stop(ROOT)
