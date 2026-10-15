from pathlib import Path

import pytest

from defect_lens.batch import BatchSummary


def test_batch_failure_exit_is_explicit() -> None:
    assert BatchSummary(submitted=2, succeeded=1, failed=1).exit_code == 4
    assert BatchSummary(submitted=2, succeeded=2, failed=0).exit_code == 0


def test_startup_failures_record_every_sample(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pathlib import Path

    import httpx

    from defect_lens import batch
    from tests.support import make_dataset

    data = make_dataset(tmp_path / "data")
    path = tmp_path / "data/manifest.json"
    for mode in ["refused", "http_error", "malformed"]:

        def handler(request: httpx.Request, current: str = mode) -> httpx.Response:
            if current == "refused":
                raise httpx.ConnectError("refused", request=request)
            return httpx.Response(
                503 if current == "http_error" else 200, json={"unexpected": True}
            )

        def client(_url: str) -> httpx.Client:
            return httpx.Client(
                base_url="http://127.0.0.1:8111", transport=httpx.MockTransport(handler)
            )

        monkeypatch.setattr(batch, "create_client", client, raising=False)
        output = tmp_path / f"{mode}.jsonl"
        result = batch.run_batch(path, "http://127.0.0.1:8111", output)
        assert result.exit_code == 4 and result.failed == len(data.samples)
        assert len(Path(output).read_text().splitlines()) == len(data.samples)
