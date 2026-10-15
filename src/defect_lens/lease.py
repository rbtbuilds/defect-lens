import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Self
from uuid import uuid4

import psutil

DEFAULT_LEASE = Path("/tmp/bentolabs-portfolio-ml.lock")


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
