from pathlib import Path

from defect_lens.config import Settings


def test_runtime_paths_are_project_local(tmp_path: Path) -> None:
    assert Settings(root=tmp_path).database_path == tmp_path / ".runtime" / "defect-lens.sqlite3"


def test_process_thread_limits_precede_numeric_imports() -> None:
    import json
    import os
    import subprocess
    import sys

    names = ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            "import defect_lens,os,json; print(json.dumps({k:os.environ.get(k) for k in "
            + repr(names)
            + "}))",
        ],
        env={**os.environ, **{name: "8" for name in names}},
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(child.stdout) == {name: "1" for name in names}
