from pathlib import Path

from fastapi.testclient import TestClient

from defect_lens.api import create_app
from defect_lens.config import Settings


def test_health_does_not_claim_model_readiness(tmp_path: Path) -> None:
    with TestClient(create_app(Settings(root=tmp_path))) as client:
        assert client.get("/healthz").json() == {"status": "ok", "database": "ok"}
        ready = client.get("/readyz")
        assert ready.status_code == 503
        assert ready.json()["status"] == "unprepared"
