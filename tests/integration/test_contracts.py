import json
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.export_contracts import export


def test_wire_contract_exports_match(client: TestClient, tmp_path: Path) -> None:
    expected = json.loads(Path("docs/api/openapi.json").read_text())
    assert client.get("/openapi.json").json() == expected
    (tmp_path / "web/src").mkdir(parents=True)
    (tmp_path / "docs/api").mkdir(parents=True)
    export(tmp_path)
    assert (tmp_path / "web/src/types.ts").read_text() == Path("web/src/types.ts").read_text()
    assert "/Users/" not in json.dumps(expected)
