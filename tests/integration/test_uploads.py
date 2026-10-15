from collections.abc import Iterator
from uuid import uuid4

from fastapi.testclient import TestClient

from tests.integration.test_api import submit_image


def test_invalid_and_oversized_uploads(client: TestClient, revision: str) -> None:
    assert submit_image(client, b"corrupt", str(uuid4()), revision).status_code == 422
    assert (
        submit_image(client, b"x" * (8 * 1024 * 1024 + 1), str(uuid4()), revision).status_code
        == 413
    )

    def chunks() -> Iterator[bytes]:
        for _ in range(10):
            yield b"x" * 1024 * 1024

    response = client.post(
        "/api/jobs",
        content=chunks(),
        headers={"Content-Type": "multipart/form-data; boundary=test"},
    )
    assert response.status_code == 413
    assert (
        client.post(
            "/api/jobs", content=b"invalid", headers={"Content-Type": "multipart/form-data"}
        ).status_code
        == 400
    )


def test_upload_gate_is_bounded() -> None:
    import pytest

    from defect_lens.errors import DomainError
    from defect_lens.routes import UploadGate

    gate = UploadGate()
    with gate.enter(), gate.enter(), pytest.raises(DomainError, match="uploads"), gate.enter():
        raise AssertionError("third upload entered")
