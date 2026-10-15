import json
from pathlib import Path

import pytest

from defect_lens.lease import LeaseBusy, MachineLease


def test_exclusive_ownership_and_token_release(tmp_path: Path) -> None:
    lease = MachineLease(tmp_path / "lease")
    with lease.acquire("test owner") as handle:
        owner = json.loads((lease.path / "owner.json").read_text())
        assert owner["project"] == "defect-lens"
        assert owner["process_start"] > 0
        assert owner["token"] == handle.token
        with pytest.raises(LeaseBusy):
            lease.acquire("contender")
        original = handle.token
        handle.token = "wrong"
        with pytest.raises(LeaseBusy):
            handle.close_after_worker_exit()
        handle.token = original
    assert not lease.path.exists()


def test_busy_preparation_never_starts_loader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import defect_lens.lease as module
    from defect_lens.models import prepare_model

    real_factory = module.MachineLease
    lease = real_factory(tmp_path / "lease")

    def factory() -> MachineLease:
        return real_factory(tmp_path / "lease")

    with lease.acquire("owner"):
        monkeypatch.setattr(module, "MachineLease", factory)
        with pytest.raises(LeaseBusy):
            prepare_model(tmp_path / "absent.json", "resnet18_patch", tmp_path / "model")
        assert not (tmp_path / "model").exists()


def test_interrupted_model_runner_stops_owned_descendants_before_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    import sys
    import time

    import psutil

    import defect_lens.lease as module

    record = tmp_path / "child.json"
    code = "import subprocess,sys,time,json,os; child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); open(sys.argv[1],'w').write(json.dumps([os.getpid(),child.pid])); time.sleep(60)"
    original = subprocess.Popen[bytes].wait
    raised = False

    def interrupted(process: subprocess.Popen[bytes], timeout: float | None = None) -> int:
        nonlocal raised
        if not raised:
            deadline = time.monotonic() + 5
            while not record.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            assert record.exists()
            raised = True
            raise KeyboardInterrupt
        return original(process, timeout=timeout)

    monkeypatch.setattr(subprocess.Popen, "wait", interrupted)
    with MachineLease(tmp_path / "lease").acquire("owned process lifetime"):
        with pytest.raises(KeyboardInterrupt):
            module.run_model_process([sys.executable, "-c", code, str(record)])
        for pid in json.loads(record.read_text()):
            assert (
                not psutil.pid_exists(pid) or psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
            )
