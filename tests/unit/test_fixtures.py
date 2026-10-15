from pathlib import Path

from defect_lens.fixtures import generate_fixtures


def test_fixture_counts_and_reproducibility(tmp_path: Path) -> None:
    first = generate_fixtures(tmp_path / "one", seed=17)
    second = generate_fixtures(tmp_path / "two", seed=17)
    assert len(first.samples) == 216
    assert sum(s.split == "train" for s in first.samples) == 36
    assert first.model_dump() == second.model_dump()
    assert all(s.label == "good" for s in first.samples if s.split == "train")


def test_fixture_cli_writes_a_real_manifest(tmp_path: Path) -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from defect_lens.cli import main; main()",
            "fixtures",
            "--output",
            str(tmp_path / "cli"),
            "--seed",
            "9",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "cli/manifest.json").exists()
