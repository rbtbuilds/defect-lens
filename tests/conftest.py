from collections.abc import Generator
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from defect_lens.api import create_app
from defect_lens.config import Settings
from defect_lens.fixtures import render_frame
from defect_lens.models import prepare_model
from tests.integration.test_supervisor import wait_until
from tests.support import make_dataset


def pytest_configure(config: pytest.Config) -> None:
    (config.rootpath / ".runtime").mkdir(exist_ok=True)


@pytest.fixture
def good_png() -> bytes:
    stream = BytesIO()
    render_frame("good")[0].save(stream, format="PNG")
    return stream.getvalue()


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient]:
    make_dataset(tmp_path / "data")
    prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    with TestClient(create_app(Settings(tmp_path, tmp_path / "model"))) as client:
        wait_until(lambda: client.get("/readyz").status_code == 200)
        yield client


@pytest.fixture
def revision(client: TestClient) -> str:
    return str(client.get("/readyz").json()["model_revision"])
