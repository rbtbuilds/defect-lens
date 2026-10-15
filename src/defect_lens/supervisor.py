import fcntl
import logging
import multiprocessing as mp
import queue
import threading
import time
from collections.abc import Callable
from multiprocessing.process import BaseProcess
from multiprocessing.queues import Queue
from pathlib import Path
from typing import IO

import psutil

from defect_lens.config import Settings
from defect_lens.contracts import Job, JobError, ReadyState
from defect_lens.errors import DomainError
from defect_lens.lease import LeaseBusy, LeaseHandle, MachineLease, token_matches
from defect_lens.models import ModelManifest, read_model_manifest, resolve_model
from defect_lens.repository import Repository
from defect_lens.worker import WorkerCommand, WorkerEvent, WorkerSettings, worker_main

WorkerTarget = Callable[[WorkerSettings, Queue[WorkerCommand], Queue[WorkerEvent]], None]


class Supervisor:
    def __init__(
        self, settings: Settings, repository: Repository, target: WorkerTarget = worker_main
    ):
        self.settings = settings
        self.repository = repository
        self.target = target
        self.ready = ReadyState()
        self.process: BaseProcess | None = None
        self.process_start: float | None = None
        self.manifest: ModelManifest | None = None
        self.model_path: Path | None = None
        self.lease: LeaseHandle | None = None
        self.server_lock: IO[str] | None = None
        self.inbound: Queue[WorkerCommand] | None = None
        self.outbound: Queue[WorkerEvent] | None = None
        self.thread: threading.Thread | None = None
        self.stopping = threading.Event()
        self.active: Job | None = None
        self.dispatched = 0.0
        self.restarts = 0
        self.accepting = True

    def start(self) -> ReadyState:
        self.settings.runtime.mkdir(parents=True, exist_ok=True)
        lock = (self.settings.runtime / "server.lock").open("a+")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            lock.close()
            raise DomainError(
                "SERVER_BUSY", "This project server is already running", 503
            ) from error
        self.server_lock = lock
        self.repository.recover_interrupted()
        if self.settings.model_dir is None:
            return self.ready
        try:
            self.model_path = resolve_model(self.settings.model_dir)
            self.manifest = read_model_manifest(self.model_path)
            self.repository.register_model(self.manifest)
            self.ready = ReadyState(
                status="loading",
                model_revision=self.manifest.revision,
                method=self.manifest.method,
                data_mode=self.manifest.data_mode,
                reason="Loading selected model",
            )
            if self.manifest.method == "resnet18_patch":
                if self.settings.feature_lease_token and token_matches(
                    self.settings.lease_path, self.settings.feature_lease_token
                ):
                    self.lease = None
                else:
                    self.lease = MachineLease(self.settings.lease_path).acquire(
                        "feature inference worker lifetime"
                    )
            self._spawn()
            self.thread = threading.Thread(
                target=self._loop, name="defect-lens-supervisor", daemon=True
            )
            self.thread.start()
        except LeaseBusy:
            self.ready.status = "busy"
            self.ready.reason = (
                "model_busy: another owner holds the machine lease; restart when available"
            )
        except (OSError, ValueError):
            self.ready.status = "unprepared"
            self.ready.reason = "Selected model is missing or invalid; prepare it before restart"
        return self.ready

    def _spawn(self) -> None:
        if self.model_path is None:
            return
        context = mp.get_context("spawn")
        self.inbound = context.Queue(maxsize=1)
        self.outbound = context.Queue(maxsize=2)
        self.process = context.Process(
            target=self.target,
            args=(
                WorkerSettings(
                    self.settings,
                    self.model_path,
                    self.lease.token if self.lease else self.settings.feature_lease_token,
                ),
                self.inbound,
                self.outbound,
            ),
            daemon=True,
        )
        self.process.start()
        if self.process.pid is not None:
            self.process_start = psutil.Process(self.process.pid).create_time()
        self.ready.status = "loading"
        self.ready.worker_alive = True

    def submit_pending(self) -> None:
        if (
            self.accepting
            and self.active is None
            and self.ready.status == "ready"
            and self.inbound is not None
        ):
            self.active = self.repository.claim_next()
            if self.active:
                self.dispatched = time.monotonic()
                self.inbound.put_nowait(WorkerCommand("inspect", self.active.id))

    def _loop(self) -> None:
        try:
            self._run_loop()
        except Exception:
            logging.getLogger(__name__).exception("Supervisor failed")
            self.repository.set_ready(None)
            self._terminate()
            if self.active:
                self.repository.fail(
                    self.active.id,
                    JobError(code="INTERNAL", message="Inspection supervisor failed"),
                )
                self.active = None
            self.ready.status = "degraded"
            self.ready.worker_alive = False
            self.ready.reason = "Supervisor failed; restart application"

    def _run_loop(self) -> None:
        while not self.stopping.wait(0.1):
            try:
                if self.outbound is not None:
                    while True:
                        event = self.outbound.get_nowait()
                        if event.kind == "ready":
                            self.ready.status = "ready"
                            self.ready.reason = None
                            if self.manifest and self.accepting:
                                self.repository.set_ready(self.manifest.revision)
                        elif (
                            event.kind == "complete"
                            and event.result is not None
                            and self.active
                            and event.job_id == self.active.id
                        ):
                            try:
                                self.repository.complete(event.job_id, event.result)
                            except DomainError as error:
                                self.repository.fail(
                                    event.job_id, JobError(code=error.code, message=error.message)
                                )
                            self.active = None
                        elif event.kind == "failure":
                            self._restart(
                                event.error or JobError(code="INTERNAL", message="Worker failed")
                            )
                            break
            except queue.Empty:
                pass
            process = self.process
            if process is None:
                continue
            if not process.is_alive():
                self._restart(
                    JobError(
                        code="INTERRUPTED", message="Worker exited unexpectedly; resubmit to retry"
                    )
                )
                continue
            try:
                rss = psutil.Process(process.pid).memory_info().rss if process.pid else 0
            except psutil.Error:
                rss = 0
            if rss > self.settings.worker_memory_mb * 1024 * 1024:
                self._restart(JobError(code="MEMORY_LIMIT", message="Worker exceeded memory limit"))
                continue
            if self.active and time.monotonic() - self.dispatched > self.settings.job_timeout:
                self._restart(
                    JobError(code="TIMEOUT", message="Inspection exceeded processing deadline")
                )
                continue
            self.submit_pending()

    def _terminate(self) -> None:
        process = self.process
        if process is not None:
            if process.is_alive():
                if (
                    process.pid is None
                    or abs(psutil.Process(process.pid).create_time() - (self.process_start or 0))
                    > 0.01
                ):
                    raise RuntimeError("Worker process identity changed; refusing signal")
                process.terminate()
                process.join(5)
                if process.is_alive():
                    process.kill()
                    process.join(5)
            else:
                process.join()
            if process.is_alive():
                raise RuntimeError("Owned worker did not exit")
        self.process = None
        for channel in (self.inbound, self.outbound):
            if channel is not None:
                channel.cancel_join_thread()
                channel.close()
        self.inbound = self.outbound = None

    def _restart(self, error: JobError) -> None:
        self.repository.set_ready(None)
        self._terminate()
        if self.active:
            self.repository.fail(self.active.id, error)
            self.active = None
        self.ready.worker_alive = False
        if self.restarts < 1 and self.accepting:
            self.restarts += 1
            self._spawn()
        else:
            self.ready.status = "degraded"
            self.ready.reason = "Worker restart budget exhausted; restart application"

    def shutdown(self, grace_seconds: float = 5) -> None:
        self.accepting = False
        self.repository.set_ready(None)
        deadline = time.monotonic() + grace_seconds
        while self.active and time.monotonic() < deadline:
            time.sleep(0.05)
        self.stopping.set()
        if self.thread is not None:
            self.thread.join(12)
            if self.thread.is_alive():
                raise RuntimeError("Supervisor did not stop; retaining ownership locks")
        self._terminate()
        self.repository.recover_interrupted()
        self.ready.worker_alive = False
        self.ready.status = "unprepared"
        if self.lease is not None:
            self.lease.close_after_worker_exit()
            self.lease = None
        if self.server_lock is not None:
            fcntl.flock(self.server_lock, fcntl.LOCK_UN)
            self.server_lock.close()
            self.server_lock = None
