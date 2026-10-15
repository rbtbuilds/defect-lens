import json
import os
import signal
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Self
from uuid import uuid4

import psutil

DEFAULT_LEASE = Path("/tmp/bentolabs-portfolio-ml.lock")


class ModelProcessCleanupError(RuntimeError):
    pass


class LeaseBusy(RuntimeError):
    pass


@dataclass
class LeaseHandle:
    path: Path
    token: str

    def close_after_worker_exit(self) -> None:
        if not self.path.exists():
            return
        if not token_matches(self.path, self.token):
            raise LeaseBusy("Lease ownership changed; refusing release")
        (self.path / "owner.json").unlink()
        self.path.rmdir()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        if len(_args) > 1 and isinstance(_args[1], ModelProcessCleanupError):
            return
        self.close_after_worker_exit()


def token_matches(path: Path, token: str) -> bool:
    try:
        from defect_lens.contracts import Contract

        class Owner(Contract):
            project: str
            pid: int
            utc_start: str
            purpose: str
            token: str
            process_start: float

        owner = Owner.model_validate_json((path / "owner.json").read_bytes())
        return (
            owner.project == "defect-lens"
            and owner.token == token
            and abs(psutil.Process(owner.pid).create_time() - owner.process_start) < 0.01
        )
    except (OSError, ValueError, psutil.Error):
        return False


class MachineLease:
    def __init__(self, path: Path = DEFAULT_LEASE):
        self.path = path

    def acquire(self, purpose: str) -> LeaseHandle:
        try:
            self.path.mkdir()
        except FileExistsError as error:
            raise LeaseBusy("model_busy: shared machine lease is occupied") from error
        token = uuid4().hex
        owner = {
            "project": "defect-lens",
            "pid": os.getpid(),
            "utc_start": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "purpose": purpose,
            "token": token,
            "process_start": psutil.Process().create_time(),
        }
        try:
            (self.path / "owner.json").write_text(json.dumps(owner))
        except BaseException:
            self.path.rmdir()
            raise
        return LeaseHandle(self.path, token)


def run_model_process(command: Sequence[str]) -> None:
    process = subprocess.Popen(list(command), start_new_session=True, cwd=Path.cwd())
    identity = psutil.Process(process.pid).create_time()
    try:
        code = process.wait()
        if code:
            raise subprocess.CalledProcessError(code, list(command))
    finally:
        try:
            leader = psutil.Process(process.pid)
            if abs(leader.create_time() - identity) > 0.01:
                raise ModelProcessCleanupError(
                    "Model process identity changed; retain lease for inspection"
                )
        except psutil.NoSuchProcess:
            pass
        if process.poll() is not None:
            time.sleep(0.1)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        deadline = time.monotonic() + 5
        while True:
            live: list[int] = []
            for member in psutil.process_iter():
                try:
                    if (
                        os.getpgid(member.pid) == process.pid
                        and member.status() != psutil.STATUS_ZOMBIE
                    ):
                        live.append(member.pid)
                except (OSError, psutil.Error):
                    pass
            if not live:
                break
            if time.monotonic() > deadline:
                raise ModelProcessCleanupError(
                    "Owned model descendants did not exit; lease retained"
                )
            time.sleep(0.02)
