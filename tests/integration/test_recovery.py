from pathlib import Path

import pytest

from tests.integration.test_repository import enqueue, prepared_repo


def test_restart_fails_running_and_preserves_queued(tmp_path: Path) -> None:
    repo = prepared_repo(tmp_path)
    running, _ = enqueue(repo)
    queued, _ = enqueue(repo)
    assert repo.claim_next() is not None
    assert repo.recover_interrupted() == 1
    failed = repo.get_job(running.id)
    assert failed.error is not None and failed.error.code == "INTERRUPTED"
    assert repo.get_job(queued.id).status == "queued"
    assert repo.count_inspections(running.id) == 0


def test_artifact_before_commit_crash_never_duplicates_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sqlite3
    from collections.abc import Generator
    from contextlib import contextmanager

    import pytest

    import defect_lens.repository as module
    from defect_lens.contracts import InputMetadata
    from defect_lens.models import load_model
    from defect_lens.worker import persist_result

    repo = prepared_repo(tmp_path)
    job, _ = enqueue(repo)
    repo.claim_next()
    path, metadata = repo.input_for(job.id)
    result = persist_result(
        load_model(tmp_path / "model"),
        path,
        InputMetadata.model_validate_json(metadata),
        repo.settings.runtime,
        job.id,
    )
    original = module.transaction

    @contextmanager
    def interrupted(path: Path) -> Generator[sqlite3.Connection]:
        with original(path) as connection:
            yield connection
            raise RuntimeError("simulated crash before commit")

    with monkeypatch.context() as patch:
        patch.setattr(module, "transaction", interrupted)
        with pytest.raises(RuntimeError, match="simulated crash"):
            repo.complete(job.id, result)
    reopened = module.Repository(repo.settings)
    assert reopened.recover_interrupted() == 1
    assert reopened.count_inspections(job.id) == 0
    assert reopened.get_job(job.id).status == "failed"
