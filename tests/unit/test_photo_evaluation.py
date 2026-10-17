from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from defect_lens.lease import LeaseBusy
from defect_lens.photo_evaluation import compare, diagnose, difference_heatmap, full_image_score
from defect_lens.photographs import PhotoSample


def test_direct_comparison_requires_owned_lease_before_reading_inputs(tmp_path: Path) -> None:
    with pytest.raises(LeaseBusy):
        compare(tmp_path, tmp_path / "output", tmp_path / "weights", tmp_path / "protocol")


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
