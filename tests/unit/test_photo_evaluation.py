import json
from collections.abc import Sequence
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from defect_lens.imaging import RgbFrame
from defect_lens.lease import LeaseBusy
from defect_lens.manifests import file_hash
from defect_lens.photo_evaluation import (
    compare,
    diagnose,
    difference_heatmap,
    full_image_score,
    hash_sources,
)
from defect_lens.photographs import PhotoManifest, PhotoSample


def test_direct_comparison_requires_owned_lease_before_reading_inputs(tmp_path: Path) -> None:
    with pytest.raises(LeaseBusy):
        compare(tmp_path, tmp_path / "output", tmp_path / "weights", tmp_path / "protocol")


def test_source_identity_accepts_relative_script_and_absolute_module_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "script.py").write_bytes(b"abc")
    (tmp_path / "module.py").write_bytes(b"abc")
    monkeypatch.chdir(tmp_path)
    result = hash_sources([Path("script.py"), tmp_path / "module.py"], tmp_path)
    assert result == {
        "script.py": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        "module.py": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    }


def test_comparison_applies_thread_cap_before_even_loading_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def owned(_path: Path, _token: str) -> bool:
        return True

    monkeypatch.setattr("defect_lens.photo_evaluation.token_matches", owned)
    previous = cv2.getNumThreads()
    try:
        cv2.setNumThreads(4)
        with pytest.raises(FileNotFoundError):
            compare(
                tmp_path,
                tmp_path / "out",
                tmp_path / "weights",
                tmp_path / "protocol",
                lease_token="test",
            )
        assert cv2.getNumThreads() == 1
    finally:
        cv2.setNumThreads(previous)


def test_corrupt_first_development_input_is_retained_in_incomplete_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = tmp_path / "protocol.md"
    protocol.write_text("Synthetic software regression, not photographic evidence")
    weights = tmp_path / "weights"
    weights.write_bytes(b"model boundary replaced in this light regression")
    samples: list[PhotoSample] = []
    for i in range(7):
        name = f"{i}.png"
        Image.new("RGB", (256, 256), (100 + i * 10,) * 3).save(tmp_path / name)
        samples.append(
            PhotoSample(
                image_path=name,
                image_sha256=file_hash(tmp_path / name),
                upstream_split="train",
                partition="fit" if i < 4 else "development",
                label="good" if i < 6 else "defect",
                mask_path="mask.png" if i == 6 else None,
            )
        )
    (tmp_path / "4.png").write_bytes(b"corrupt but hash-valid declared input")
    samples[4].image_sha256 = file_hash(tmp_path / "4.png")
    Image.new("L", (256, 256), 255).save(tmp_path / "mask.png")
    manifest = PhotoManifest(protocol_sha256=file_hash(protocol), samples=samples)
    (tmp_path / "manifest.json").write_text(manifest.model_dump_json())

    def owned(_path: Path, _token: str) -> bool:
        return True

    def validation_boundary(_manifest: PhotoManifest, _root: Path) -> None:
        pass

    def hash_boundary(path: Path) -> str:
        return "f37072fd" + "0" * 56 if path == weights else file_hash(path)

    def model_boundary(_method: str, _fit: Sequence[RgbFrame], _weights: Path):
        cv2.setNumThreads(4)

        def score(frame: RgbFrame):
            assert cv2.getNumThreads() == 1
            return np.asarray(frame[:, :, 0] / 255, dtype=np.float32)

        return score

    monkeypatch.setattr("defect_lens.photo_evaluation.token_matches", owned)
    monkeypatch.setattr("defect_lens.photo_evaluation.validate_photos", validation_boundary)
    monkeypatch.setattr("defect_lens.photo_evaluation.file_hash", hash_boundary)
    monkeypatch.setattr("defect_lens.photo_evaluation.build_scorer", model_boundary)
    compare(tmp_path, tmp_path / "out", weights, protocol, lease_token="test")
    report = json.loads((tmp_path / "out/report.json").read_text())
    assert report["complete"] is False
    for method in report["methods"].values():
        assert method["metrics"]["failures"] == 1
        assert len(method["rows"]) == 3
        assert method["rows"][0]["source_image"] == "4.png"
        assert method["rows"][0]["error"] == "UnidentifiedImageError"


def test_full_frame_adapter_keeps_border_defects() -> None:
    reference = np.full((256, 256, 3), 100, dtype=np.uint8)
    frame = reference.copy()
    frame[:16, :16] = 255
    heatmap = difference_heatmap(frame, reference)
    assert float(heatmap[:16, :16].mean()) > 0.5
    assert full_image_score(heatmap) > 0.1


def test_diagnostics_retain_failed_inputs_and_do_not_call_them_correct(tmp_path: Path) -> None:
    Image.new("RGB", (128, 256), (100, 100, 100)).save(tmp_path / "good.png")
    Image.new("RGB", (128, 256), (200, 200, 200)).save(tmp_path / "defect.png")
    Image.new("L", (128, 256), 255).save(tmp_path / "mask.png")
    samples = [
        PhotoSample(
            image_path=name,
            image_sha256="a" * 64,
            upstream_split="test",
            partition="development",
            label="defect" if name == "defect.png" else "good",
            mask_path="mask.png" if name == "defect.png" else None,
        )
        for name in ["good.png", "defect.png", "missing.png"]
    ]
    report = diagnose(
        lambda frame: np.asarray(frame[:, :, 0] / 255, dtype=np.float32), samples, tmp_path
    )
    assert len(report.rows) == 3
    assert report.metrics.failures == 1
    assert report.rows[2].error is not None
    assert report.metrics.labelled_count == 2
    assert report.metrics.confusion == {"tp": 1, "fp": 0, "fn": 0, "tn": 1}
    assert report.metrics.localization_iou == 1


def test_fit_rows_cannot_enter_reported_development_metrics(tmp_path: Path) -> None:
    record = PhotoSample(
        image_path="unused.png",
        image_sha256="a" * 64,
        upstream_split="train",
        partition="fit",
        label="good",
    )
    with pytest.raises(ValueError, match="development"):
        diagnose(lambda _frame: np.zeros((256, 256), dtype=np.float32), [record], tmp_path)
