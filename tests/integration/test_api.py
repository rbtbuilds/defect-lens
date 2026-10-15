from typing import cast
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response

from defect_lens.repository import Repository
from tests.integration.test_supervisor import wait_until


def submit_image(client: TestClient, image: bytes, key: str, revision: str) -> Response:
    return client.post(
        "/api/jobs",
        files={"image": ("ignored.jpg", image, "image/jpeg")},
        data={"model_revision": revision, "data_mode": "procedural"},
        headers={"Idempotency-Key": key},
    )


def test_duplicate_upload_and_actual_inspection(
    client: TestClient, good_png: bytes, revision: str
) -> None:
    key = str(uuid4())
    first = submit_image(client, good_png, key, revision)
    assert first.status_code == 202, first.text
    second = submit_image(client, good_png, key, revision)
    assert second.status_code == 200
    job_id = first.json()["id"]
    assert second.json()["id"] == job_id
    wait_until(lambda: client.get(f"/api/jobs/{job_id}").json()["status"] == "succeeded")
    job = client.get(f"/api/jobs/{job_id}").json()
    inspection = client.get(f"/api/inspections/{job['inspection_id']}").json()
    assert inspection["model_revision"] == revision
    assert inspection["score"] is not None
    assert client.get(inspection["heatmap_url"]).headers["content-type"] == "image/png"
    assert submit_image(client, good_png + b"different", key, revision).status_code == 409
    repository = cast(Repository, cast(FastAPI, client.app).state.repository)
    repository.set_ready(None)
    assert submit_image(client, good_png, key, revision).status_code == 200
    assert submit_image(client, good_png, str(uuid4()), revision).status_code == 503


def test_wrong_revision_and_origin(client: TestClient, good_png: bytes, revision: str) -> None:
    assert submit_image(client, good_png, str(uuid4()), "b" * 64).status_code == 409
    response = client.post("/api/jobs", headers={"Origin": "https://example.com"})
    assert response.status_code == 403
    assert response.json()["error"]["request_id"]


def test_33rd_job_rejected_and_full_queue_replay(
    client: TestClient, good_png: bytes, revision: str
) -> None:
    from defect_lens.supervisor import Supervisor

    app = cast(FastAPI, client.app)
    supervisor = cast(Supervisor, app.state.supervisor)
    repository = cast(Repository, app.state.repository)
    supervisor.shutdown(0)
    repository.set_ready(revision)
    key = str(uuid4())
    assert submit_image(client, good_png, key, revision).status_code == 202
    for _ in range(31):
        assert submit_image(client, good_png, str(uuid4()), revision).status_code == 202
    assert submit_image(client, good_png, str(uuid4()), revision).status_code == 429
    assert submit_image(client, good_png, key, revision).status_code == 200
    assert len(list((repository.settings.runtime / "inputs").iterdir())) == 32
