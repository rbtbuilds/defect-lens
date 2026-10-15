import json
import subprocess
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    import sys

    sys.path.insert(0, str(ROOT))
    from scripts.dev import check_ports

    check_ports()
    state = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    if state.strip():
        raise RuntimeError("Commit the scoped source/docs before checking exact HEAD")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    clone = ROOT / ".runtime" / f"clean-clone-{uuid4().hex[:10]}"
    subprocess.run(["git", "clone", "--no-hardlinks", str(ROOT), str(clone)], cwd=ROOT, check=True)
    commands = [
        ["uv", "sync", "--locked", "--extra", "features"],
        ["npm", "--prefix", "web", "ci"],
        ["npm", "--prefix", "web", "exec", "--", "playwright", "install", "chromium"],
        ["uv", "run", "python", "scripts/verify.py", "--fixture-only"],
    ]
    results: list[dict[str, object]] = []
    try:
        for command in commands:
            result = subprocess.run(command, cwd=clone, check=False)
            results.append({"command": command, "exit_code": result.returncode})
            if result.returncode:
                raise RuntimeError("Clean clone verification failed")
        check_ports()
    finally:
        subprocess.run(["uv", "run", "python", "scripts/dev.py", "stop"], cwd=clone, check=False)
        (ROOT / ".runtime/clean-clone-evidence.json").write_text(
            json.dumps(
                {"source_commit": head, "clone": str(clone.relative_to(ROOT)), "commands": results},
                indent=2,
            )
            + "\n"
        )


if __name__ == "__main__":
    main()
