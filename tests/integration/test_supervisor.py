from collections.abc import Callable
from multiprocessing.queues import Queue
from pathlib import Path

from defect_lens.supervisor import Supervisor
from defect_lens.worker import WorkerCommand, WorkerEvent, WorkerSettings
from tests.integration.test_repository import prepared_repo


def test_server_lock_refuses_second_owner(tmp_path: Path) -> None:
    import pytest

    from defect_lens.errors import DomainError

    repo = prepared_repo(tmp_path)
    first = Supervisor(repo.settings, repo)
    second = Supervisor(repo.settings, repo)
    first.start()
    try:
        with pytest.raises(DomainError, match="already running"):
            second.start()
    finally:
        first.shutdown(0)
    assert first.process is None or not first.process.is_alive()


def wait_until(predicate: Callable[[], bool], timeout: float = 10) -> None:
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("Timed out waiting for actual process state")


def blocking_worker(
    settings: WorkerSettings, inbound: Queue[WorkerCommand], outbound: Queue[WorkerEvent]
) -> None:
    import time

    from defect_lens.worker import WorkerEvent

    outbound.put(WorkerEvent("ready"))
    inbound.get()
    time.sleep(60)


def test_actual_worker_completes_and_shutdown_joins(tmp_path: Path) -> None:
    from dataclasses import replace

    from tests.integration.test_repository import enqueue

    repo = prepared_repo(tmp_path)
    settings = replace(repo.settings, model_dir=tmp_path / "model")
    supervisor = Supervisor(settings, repo)
    supervisor.start()
    try:
        wait_until(lambda: supervisor.ready.status == "ready")
        job, _ = enqueue(repo)
        wait_until(lambda: repo.get_job(job.id).status == "succeeded")
        inspection_id = repo.get_job(job.id).inspection_id
        assert inspection_id is not None
        assert repo.get_inspection(inspection_id).score is not None
        assert repo.count_inspections(job.id) == 1
    finally:
        supervisor.shutdown()
    assert supervisor.process is None


def test_timeout_restart_budget_and_memory_limit(tmp_path: Path) -> None:
    from dataclasses import replace

    from tests.integration.test_repository import enqueue

    repo = prepared_repo(tmp_path)
    settings = replace(repo.settings, model_dir=tmp_path / "model", job_timeout=0.15)
    supervisor = Supervisor(settings, repo, blocking_worker)
    supervisor.start()
    try:
        wait_until(lambda: supervisor.ready.status == "ready")
        first, _ = enqueue(repo)
        wait_until(lambda: repo.get_job(first.id).status == "failed")
        error = repo.get_job(first.id).error
        assert error is not None and error.code == "TIMEOUT"
        wait_until(lambda: supervisor.ready.status == "ready")
        second, _ = enqueue(repo)
        wait_until(lambda: repo.get_job(second.id).status == "failed")
        wait_until(lambda: supervisor.ready.status == "degraded")
        assert supervisor.restarts == 1
    finally:
        supervisor.shutdown(0)
    assert supervisor.process is None
    memory = Supervisor(replace(settings, worker_memory_mb=1), repo, blocking_worker)
    memory.start()
    try:
        wait_until(lambda: memory.ready.status == "degraded")
        assert memory.restarts == 1
    finally:
        memory.shutdown(0)
