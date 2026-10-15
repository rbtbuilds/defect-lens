import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify() -> None:
    from scripts.dev import check_ports, stop

    check_ports()
    (ROOT / ".runtime").mkdir(exist_ok=True)
    commands = [
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "ruff", "format", "--check", "."],
        ["uv", "run", "--extra", "features", "pyright"],
        [
            "uv",
            "run",
            "--extra",
            "features",
            "pytest",
            "tests/unit",
            "tests/integration",
            "-m",
            "not real_model",
            "-q",
        ],
        ["npm", "--prefix", "web", "run", "lint"],
        ["npm", "--prefix", "web", "run", "typecheck"],
        ["npm", "--prefix", "web", "run", "test", "--", "--run"],
        ["npm", "--prefix", "web", "run", "build"],
        [
            "uv",
            "run",
            "defect-lens",
            "fixtures",
            "--output",
            ".runtime/data/fixtures",
            "--seed",
            "20261015",
        ],
        [
            "uv",
            "run",
            "defect-lens",
            "prepare",
            "--method",
            "difference",
            "--dataset",
            ".runtime/data/fixtures/manifest.json",
            "--output",
            ".runtime/models/demo-difference",
        ],
        [
            "uv",
            "run",
            "python",
            "scripts/dev.py",
            "start",
            "--model",
            ".runtime/models/demo-difference",
        ],
        ["npm", "--prefix", "web", "run", "test:e2e"],
        ["uv", "run", "--extra", "features", "pytest", "tests/e2e/test_restart_flow.py", "-q"],
        ["uv", "run", "python", "scripts/dev.py", "stop"],
        ["uv", "run", "python", "scripts/dev.py", "status"],
    ]
    evidence: list[dict[str, object]] = []
    started = time.time()
    try:
        for command in commands:
            print("Running: " + " ".join(command), flush=True)
            result = subprocess.run(command, cwd=ROOT, check=False)
            evidence.append({"command": command, "exit_code": result.returncode})
            if result.returncode:
                raise RuntimeError("Verification command failed")
        check_ports()
    finally:
        stop(ROOT)
        (ROOT / ".runtime/verification.json").write_text(
            json.dumps(
                {"started_unix": started, "finished_unix": time.time(), "commands": evidence},
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-only", action="store_true", required=True)
    parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        raise SystemExit("Run from this checkout root")
    # Direct script execution has scripts/ on sys.path; add only its own root.
    sys.path.insert(0, str(ROOT))
    verify()
