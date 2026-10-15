import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx
import psutil

from defect_lens.contracts import Contract
from defect_lens.models import read_model_manifest

ROOT = Path(__file__).resolve().parents[1]
PORTS = (8111, 5111)


class ProcessRecord(Contract):
    name: str
    pid: int
    process_start: float
    token: str
    command: list[str]


class ProcessRecords(Contract):
    processes: list[ProcessRecord]


def load_records(root: Path) -> ProcessRecords:
    path = root / ".runtime/dev-processes.json"
    return (
        ProcessRecords.model_validate_json(path.read_bytes())
        if path.exists()
        else ProcessRecords(processes=[])
    )


def running(record: ProcessRecord) -> bool:
    try:
        process = psutil.Process(record.pid)
        if abs(process.create_time() - record.process_start) > 0.01:
            raise RuntimeError(
                f"{record.name} process identity changed; refusing to signal PID {record.pid}"
            )
        return process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


def check_ports() -> None:
    for port in PORTS:
        with socket.socket() as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(
                    f"Port {port} is occupied. Inspect its owner with lsof; no process was stopped."
                )


def save_records(root: Path, records: ProcessRecords) -> None:
    path = root / ".runtime/dev-processes.json"
    temporary = path.with_suffix(f".{uuid4().hex}.tmp")
    temporary.write_text(records.model_dump_json(indent=2) + "\n")
    temporary.replace(path)


def stop(root: Path = ROOT) -> None:
    records = load_records(root)
    active = [record for record in records.processes if running(record)]
    # Validate every identity before sending the first signal.
    for record in active:
        process = psutil.Process(record.pid)
        children = [(child, child.create_time()) for child in process.children(recursive=True)]
        process.terminate()
        try:
            process.wait(20)
        except psutil.TimeoutExpired:
            for child, identity in reversed(children):
                try:
                    if abs(child.create_time() - identity) < 0.01:
                        child.kill()
                        child.wait(5)
                except psutil.NoSuchProcess:
                    pass
            if running(record):
                process.kill()
                process.wait(5)
        psutil.wait_procs([child for child, _ in children], timeout=5)
        for child, identity in children:
            if (
                child.is_running()
                and child.status() != psutil.STATUS_ZOMBIE
                and abs(child.create_time() - identity) < 0.01
            ):
                raise RuntimeError(
                    "Owned child remains alive; ownership record retained for inspection"
                )
    (root / ".runtime/dev-processes.json").unlink(missing_ok=True)


def start(root: Path, model: Path) -> None:
    root = root.resolve()
    runtime = root / ".runtime"
    runtime.mkdir(exist_ok=True)
    existing = load_records(root)
    if any(running(record) for record in existing.processes):
        raise RuntimeError("Recorded processes already running; inspect status first")
    check_ports()
    model = (root / model).resolve()
    if not model.is_relative_to(runtime):
        raise ValueError("Model must live in this checkout .runtime")
    read_model_manifest(model)
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node is unavailable")
    commands = [
        (
            "api",
            [
                str(root / ".venv/bin/defect-lens"),
                "serve",
                "--model",
                str(model),
                "--host",
                "127.0.0.1",
                "--port",
                "8111",
            ],
        ),
        (
            "web",
            [
                node,
                str(root / "web/node_modules/vite/bin/vite.js"),
                "--host",
                "127.0.0.1",
                "--port",
                "5111",
                "--strictPort",
            ],
        ),
    ]
    records = ProcessRecords(processes=[])
    try:
        for name, command in commands:
            token = uuid4().hex
            env = {
                **os.environ,
                "DEFECT_LENS_PROCESS_TOKEN": token,
                "OPENBLAS_NUM_THREADS": "1",
                "OMP_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
            }
            with (runtime / f"{name}.log").open("ab") as log:
                process = subprocess.Popen(
                    command,
                    cwd=root / "web" if name == "web" else root,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            records.processes.append(
                ProcessRecord(
                    name=name,
                    pid=process.pid,
                    process_start=psutil.Process(process.pid).create_time(),
                    token=token,
                    command=command,
                )
            )
            save_records(root, records)
        with httpx.Client(timeout=1) as client:
            for name, url in [
                ("api", "http://127.0.0.1:8111/healthz"),
                ("web", "http://127.0.0.1:5111/"),
            ]:
                deadline = time.monotonic() + 30
                while True:
                    if not all(running(record) for record in records.processes):
                        raise RuntimeError(f"{name} exited during startup; inspect .runtime logs")
                    try:
                        if client.get(url).status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError(f"{name} startup deadline; inspect .runtime logs")
                    time.sleep(0.1)
    except BaseException:
        stop(root)
        raise


def status(root: Path = ROOT) -> dict[str, object]:
    records = load_records(root)
    return {
        "processes": [
            {"name": r.name, "pid": r.pid, "running": running(r)} for r in records.processes
        ],
        "ports": list(PORTS),
        "recorded_count": len(records.processes),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Own only this checkout API/web processes")
    parser.add_argument("command", choices=["start", "stop", "status"])
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    git_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if Path.cwd().resolve() != ROOT or Path(git_root).resolve() != ROOT:
        raise RuntimeError("Run from the verified Defect Lens Git root")
    try:
        if args.command == "start":
            if args.model is None:
                parser.error("start requires --model")
            start(ROOT, args.model)
        elif args.command == "stop":
            stop()
        print(json.dumps(status(), indent=2))
    except (OSError, ValueError, RuntimeError, psutil.Error) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
