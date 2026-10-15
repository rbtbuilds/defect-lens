import json
import os
import socket
from pathlib import Path

import pytest

from scripts.dev import check_ports, stop


def test_occupied_port_refusal_preserves_owner() -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 8111))
        listener.listen(1)
        with pytest.raises(RuntimeError, match="8111"):
            check_ports()
        assert listener.getsockname()[1] == 8111


def test_stop_refuses_mismatched_process_identity(tmp_path: Path) -> None:
    runtime = tmp_path / ".runtime"
    runtime.mkdir()
    (runtime / "dev-processes.json").write_text(
        json.dumps(
            {
                "processes": [
                    {
                        "name": "api",
                        "pid": os.getpid(),
                        "process_start": 0,
                        "token": "wrong",
                        "command": ["test"],
                    }
                ]
            }
        )
    )
    with pytest.raises(RuntimeError, match="identity"):
        stop(tmp_path)
    assert (runtime / "dev-processes.json").exists()
