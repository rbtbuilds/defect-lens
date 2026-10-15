from pathlib import Path

from defect_lens.config import Settings


def test_runtime_paths_are_project_local(tmp_path: Path) -> None:
    assert Settings(root=tmp_path).database_path == tmp_path / ".runtime" / "defect-lens.sqlite3"
