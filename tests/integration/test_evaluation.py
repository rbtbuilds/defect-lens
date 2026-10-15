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


def test_busy_evaluation_leaves_no_output(tmp_path: Path) -> None:
    from defect_lens.lease import LeaseBusy, MachineLease

    dataset = make_dataset(tmp_path / "data")
    model = prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    lease = tmp_path / "lease"
    with MachineLease(lease).acquire("test owner"):
        with pytest.raises(LeaseBusy):
            evaluate(
                dataset,
                [model],
                tmp_path / "report",
                dataset_root=tmp_path / "data",
                model_directories=[tmp_path / "model"],
                lease_path=lease,
            )
        assert not (tmp_path / "report").exists()


@pytest.mark.parametrize("identifier", ["/tmp/defect-lens-review-probe", "../../escape"])
def test_sample_ids_never_become_filesystem_paths(tmp_path: Path, identifier: str) -> None:
    if identifier.startswith("/"):
        identifier = str(tmp_path / "absolute-probe")
    data = make_dataset(tmp_path / "data")
    sample = next(s for s in data.samples if s.split == "test" and s.label == "ambiguous")
    sample.id = identifier
    model = prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    report = evaluate(
        data,
        [model],
        tmp_path / "report",
        dataset_root=tmp_path / "data",
        model_directories=[tmp_path / "model"],
        lease_path=tmp_path / "lease",
    )
    assert report.complete
    gallery = list((tmp_path / "report/difference/failure-gallery").glob("*.png"))
    assert len(gallery) == 3
    assert all(len(path.stem) == 64 for path in gallery)
    assert not (tmp_path / "escape.png").exists()


def test_first_corrupt_sample_still_produces_incomplete_report(tmp_path: Path) -> None:
    from defect_lens.manifests import file_hash

    data = make_dataset(tmp_path / "data")
    model = prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    sample = next(s for s in data.samples if s.split == "test")
    path = tmp_path / "data" / sample.image_path
    path.write_bytes(b"corrupt initial test image")
    sample.image_sha256 = file_hash(path)
    report = evaluate(
        data,
        [model],
        tmp_path / "report",
        dataset_root=tmp_path / "data",
        model_directories=[tmp_path / "model"],
        lease_path=tmp_path / "lease",
    )
    assert not report.complete
    assert len(report.methods[0].rows) == 15
    assert report.methods[0].rows[0].error is not None


def test_no_usable_test_image_reports_null_timings(tmp_path: Path) -> None:
    from defect_lens.manifests import file_hash

    data = make_dataset(tmp_path / "data")
    model = prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    for sample in data.samples:
        if sample.split == "test":
            path = tmp_path / "data" / sample.image_path
            path.write_bytes(b"corrupt declared image")
            sample.image_sha256 = file_hash(path)
    report = evaluate(
        data,
        [model],
        tmp_path / "report",
        dataset_root=tmp_path / "data",
        model_directories=[tmp_path / "model"],
        lease_path=tmp_path / "lease",
    )
    assert not report.complete and len(report.methods[0].rows) == 15
    assert report.methods[0].cold_load_first_inference_ms is None
    assert report.methods[0].warm_latency_p95_ms is None
    assert report.methods[0].timing_unavailable_reason is not None


def test_comparison_can_borrow_an_owned_lease_without_releasing_it(tmp_path: Path) -> None:
    from defect_lens.lease import MachineLease

    data = make_dataset(tmp_path / "data")
    model = prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    lease = tmp_path / "lease"
    with MachineLease(lease).acquire("whole refresh and comparison") as handle:
        report = evaluate(
            data,
            [model],
            tmp_path / "report",
            dataset_root=tmp_path / "data",
            model_directories=[tmp_path / "model"],
            lease_path=lease,
            _lease_handle=handle,
        )
        assert report.complete and lease.exists()
    assert not lease.exists()


@pytest.mark.parametrize("all_corrupt", [False, True])
def test_api_timing_failure_preserves_pipeline_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, all_corrupt: bool
) -> None:
    from defect_lens import evaluation
    from defect_lens.manifests import file_hash

    data = make_dataset(tmp_path / "data")
    model = prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    samples = [sample for sample in data.samples if sample.split == "test"]
    for sample in samples if all_corrupt else samples[-1:]:
        path = tmp_path / "data" / sample.image_path
        path.write_bytes(b"corrupt image with declared hash")
        sample.image_sha256 = file_hash(path)
    lease = tmp_path / "lease"
    monkeypatch.setattr(evaluation, "DEFAULT_LEASE", lease)
    report = evaluate(
        data,
        [model],
        tmp_path / "report",
        dataset_root=tmp_path / "data",
        model_directories=[tmp_path / "model"],
        lease_path=lease,
    )
    assert not report.complete
    assert len(report.methods[0].rows) == 15
    assert report.methods[0].metrics.failures == (15 if all_corrupt else 1)
    assert report.methods[0].api_timing_unavailable_reason is not None
    assert report.methods[0].api_timings_ms == []
    assert report.unavailable_reasons
    saved = evaluation.EvaluationReport.model_validate_json(
        (tmp_path / "report/report.json").read_bytes()
    )
    assert not saved.complete and len(saved.methods[0].rows) == 15
    assert not lease.exists()


def test_api_only_failure_marks_comparison_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    from collections.abc import Sequence

    from defect_lens import evaluation

    data = make_dataset(tmp_path / "data")
    model = prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")
    original_runner = evaluation.run_model_process

    def fail_api(command: Sequence[str]) -> None:
        if "--api" in command:
            raise subprocess.CalledProcessError(1, list(command))
        original_runner(command)

    lease = tmp_path / "lease"
    monkeypatch.setattr(evaluation, "DEFAULT_LEASE", lease)
    monkeypatch.setattr(evaluation, "run_model_process", fail_api)
    report = evaluate(
        data,
        [model],
        tmp_path / "report",
        dataset_root=tmp_path / "data",
        model_directories=[tmp_path / "model"],
        lease_path=lease,
    )
    assert report.methods[0].metrics.failures == 0
    assert not report.complete
    assert report.methods[0].api_timing_unavailable_reason is not None
    assert (tmp_path / "report/report.json").is_file()
