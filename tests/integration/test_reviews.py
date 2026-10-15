from uuid import uuid4

from fastapi.testclient import TestClient

from tests.integration.test_api import submit_image
from tests.integration.test_supervisor import wait_until


def test_review_replay_and_conflict(client: TestClient, good_png: bytes, revision: str) -> None:
    job = submit_image(client, good_png, str(uuid4()), revision).json()
    wait_until(lambda: client.get(f"/api/jobs/{job['id']}").json()["status"] == "succeeded")
    inspection_id = client.get(f"/api/jobs/{job['id']}").json()["inspection_id"]
    url = f"/api/inspections/{inspection_id}/reviews"
    body = {
        "decision": "fail",
        "note": "Fastener is present",
        "operator_alias": "tester",
        "expected_version": 0,
    }
    headers = {"Idempotency-Key": str(uuid4())}
    first = client.post(url, json=body, headers=headers)
    assert first.status_code == 201, first.text
    assert client.post(url, json=body, headers=headers).status_code == 200
    conflict = client.post(url, json=body, headers={"Idempotency-Key": str(uuid4())})
    assert conflict.status_code == 409
    assert "Refresh" in conflict.json()["error"]["message"]
    assert len(client.get(url).json()["items"]) == 1
