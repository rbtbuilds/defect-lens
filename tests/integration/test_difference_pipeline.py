from pathlib import Path

from defect_lens.contracts import InputMetadata
from defect_lens.models import load_model, prepare_model
from tests.support import make_dataset, make_frame


def test_prepared_pipeline_handles_good_defect_and_ambiguous(tmp_path: Path) -> None:
    make_dataset(tmp_path / "data")
    prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    bundle = load_model(tmp_path / "model")
    metadata = InputMetadata(raw_sha256="a" * 64, width=256, height=256, aspect_ratio=1)
    assert bundle.inspect(make_frame(), metadata)[2] == "pass"
    assert bundle.inspect(make_frame("missing"), metadata)[2] == "fail"
    assert bundle.inspect(make_frame("blur"), metadata)[2] == "review"
