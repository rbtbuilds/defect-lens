from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from defect_lens.api import create_app
from defect_lens.config import Settings


def test_health_does_not_claim_model_readiness(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(root=tmp_path))) as client:
        assert client.get("/healthz").json() == {"status": "ok", "database": "ok"}
        ready = client.get("/readyz")
        assert ready.status_code == 503
        assert ready.json()["status"] == "unprepared"


def test_database_probe_failure_is_503(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import sqlite3

    with TestClient(create_app(Settings(root=tmp_path)), raise_server_exceptions=False) as client:

        def unavailable(*_args: object, **_kwargs: object) -> sqlite3.Connection:
            raise sqlite3.OperationalError("probe unavailable")

        with monkeypatch.context() as patch:
            patch.setattr(sqlite3, "connect", unavailable)
            response = client.get("/healthz")
            assert response.status_code == 503
            assert response.json()["error"]["request_id"]
