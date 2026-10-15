from pathlib import Path
from uuid import uuid4

import pytest

from defect_lens.config import Settings
from defect_lens.contracts import (
    AcceptedInput,
    InputMetadata,
    Job,
    ReviewCreate,
    StoredResult,
    UploadForm,
)
from defect_lens.errors import DomainError
from defect_lens.models import prepare_model, read_model_manifest
from defect_lens.repository import Repository
from tests.support import make_dataset


def prepared_repo(root: Path, max_pending: int = 32) -> Repository:
    make_dataset(root / "data")
    manifest = prepare_model(root / "data/manifest.json", "difference", root / "model")
    repo = Repository(Settings(root, max_pending=max_pending))
    repo.register_model(manifest)
    repo.set_ready(manifest.revision)
    return repo


def enqueue(repo: Repository, key: str | None = None, digest: str = "a" * 64) -> tuple[Job, bool]:
    path = repo.settings.runtime / f"{uuid4()}.png"
    from defect_lens.fixtures import render_frame

    render_frame("good")[0].save(path)
    model = read_model_manifest(repo.settings.root / "model").revision
    return repo.enqueue(
        AcceptedInput(
            normalized_path=path,
            metadata=InputMetadata(raw_sha256="a" * 64, width=256, height=256, aspect_ratio=1),
        ),
        UploadForm(model_revision=model, data_mode="procedural"),
        key or str(uuid4()),
        digest,
    )


def test_replay_capacity_conflict_and_atomic_completion(tmp_path: Path) -> None:
    repo = prepared_repo(tmp_path, max_pending=1)
    key = str(uuid4())
    first, replay = enqueue(repo, key)
    assert not replay
    repo.set_ready(None)
    assert enqueue(repo, key)[0].id == first.id
    with pytest.raises(DomainError, match="different request"):
        enqueue(repo, key, "b" * 64)
    repo.set_ready(first.model_revision)
    with pytest.raises(DomainError, match="Queue"):
        enqueue(repo)
    claimed = repo.claim_next()
    assert claimed is not None
    result = StoredResult(
        decision="pass", score=0.01, reasons=[], artifacts={}, artifact_bytes=0, regions=[]
    )
    inspection = repo.complete(first.id, result)
    with pytest.raises(DomainError):
        repo.complete(first.id, result)
    assert repo.count_inspections(first.id) == 1
    review_key = str(uuid4())
    request = ReviewCreate(
        decision="fail", note="Visible mark", operator_alias="test", expected_version=0
    )
    review = repo.add_review(inspection.id, request, review_key)
    assert repo.add_review(inspection.id, request, review_key).id == review.id
    with pytest.raises(DomainError, match="Refresh"):
        repo.add_review(inspection.id, request, str(uuid4()))
    reopened = Repository(repo.settings)
    assert reopened.get_inspection(inspection.id).latest_review == review
    assert reopened.get_inspection(inspection.id).original_decision == "pass"


def test_concurrent_admission_respects_capacity(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    repo = prepared_repo(tmp_path, max_pending=1)

    def admit(_: int) -> str:
        try:
            enqueue(repo)
            return "accepted"
        except DomainError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(admit, range(2)))
    assert sorted(results) == ["QUEUE_FULL", "accepted"]
