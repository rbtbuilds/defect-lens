from pathlib import Path

import pytest

from defect_lens.evaluation import evaluate
from defect_lens.models import prepare_model
from tests.support import make_dataset


def test_frozen_evaluation_records_all_samples_and_provenance(tmp_path: Path) -> None:
    dataset = make_dataset(tmp_path / "data")
    model = prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    report = evaluate(
        dataset,
        [model],
        tmp_path / "report",
        dataset_root=tmp_path / "data",
        model_directories=[tmp_path / "model"],
        lease_path=tmp_path / "lease",
    )
    assert report.complete
    assert len(report.methods[0].rows) == 15
    assert report.methods[0].metrics.ambiguous_count == 3
    dataset.samples[0].image_sha256 = "a" * 64
    with pytest.raises(ValueError, match="provenance"):
        evaluate(
            dataset,
            [model],
            tmp_path / "invalid",
            dataset_root=tmp_path / "data",
            model_directories=[tmp_path / "model"],
            lease_path=tmp_path / "lease",
        )


def test_decode_failure_is_retained_in_incomplete_report(tmp_path: Path) -> None:
    from defect_lens.manifests import file_hash

    dataset = make_dataset(tmp_path / "data")
    model = prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    sample = [s for s in dataset.samples if s.split == "test"][-1]
    path = tmp_path / "data" / sample.image_path
    path.write_bytes(b"corrupt but hash-declared input")
    sample.image_sha256 = file_hash(path)
    report = evaluate(
        dataset,
        [model],
        tmp_path / "report",
        dataset_root=tmp_path / "data",
        model_directories=[tmp_path / "model"],
        lease_path=tmp_path / "lease",
    )
    assert not report.complete
    assert len(report.methods[0].rows) == 15
    assert report.methods[0].metrics.failures == 1
