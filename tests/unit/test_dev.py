import json
import os
import socket
from pathlib import Path

import pytest

from scripts.dev import check_ports, stop


def test_occupied_port_refusal_preserves_owner() -> None:
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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


def test_occupied_port_refusal_after_server_close() -> None:
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 8111))
        server.listen(1)
        with socket.create_connection(("127.0.0.1", 8111)) as client:
            connection, _ = server.accept()
            with connection:
                connection.shutdown(socket.SHUT_WR)
                assert client.recv(1) == b""
    test_occupied_port_refusal_preserves_owner()
