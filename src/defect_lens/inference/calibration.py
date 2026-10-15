from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from defect_lens.contracts import Contract, Decision


class Calibration(Contract):
    low: float
    high: float
    pixel_threshold: float | None
    heatmap_display_max: float
    validation_manifest_sha: str
    missed_cost: int = 5
    false_reject_cost: int = 1
    seed: int = 20261015


@dataclass(frozen=True)
class LabelledScore:
    sample_id: str
    specimen_id: str
    truth: Literal["good", "defect"]
    score: float
    heatmap: NDArray[np.float32] | None = None
    mask: NDArray[np.uint8] | None = None


def calibrate(samples: Sequence[LabelledScore], validation_manifest_sha: str) -> Calibration:
    if {s.truth for s in samples} != {"good", "defect"} or not all(
        np.isfinite(s.score) for s in samples
    ):
        raise ValueError("finite good and defect validation scores required")
    values = sorted({s.score for s in samples})
    candidates = [
        values[0] - 1e-6,
        *[(a + b) / 2 for a, b in pairwise(values)],
        values[-1] + 1e-6,
    ]

    def loss(threshold: float) -> int:
        return sum(
            5 if s.truth == "defect" else 1
            for s in samples
            if (s.score >= threshold) != (s.truth == "defect")
        )

    high = max(min(candidates, key=lambda t: (loss(t), -t)), 1e-6)
    low = min(float(np.percentile([s.score for s in samples if s.truth == "good"], 90)), 0.9 * high)
    heatmaps = [s.heatmap[32:224, 32:224].reshape(-1) for s in samples if s.heatmap is not None]
    display = max(float(np.percentile(np.concatenate(heatmaps), 99.5)), 1e-6) if heatmaps else 1
    labelled = [s for s in samples if s.mask is not None and s.heatmap is not None]
    pixel: float | None = None
    if labelled:
        thresholds = np.linspace(
            0, max(float(s.heatmap.max()) for s in labelled if s.heatmap is not None), 33
        )

        def overlap(t: float) -> float:
            ratios: list[float] = []
            for sample in labelled:
                if sample.heatmap is None or sample.mask is None:
                    continue
                predicted = sample.heatmap >= t
                actual = sample.mask > 0
                union = int(np.count_nonzero(predicted | actual))
                ratios.append(float(np.count_nonzero(predicted & actual)) / union if union else 1)
            return float(np.mean(ratios))

        pixel = float(max(thresholds, key=lambda t: (overlap(float(t)), float(t))))
    return Calibration(
        low=low,
        high=high,
        pixel_threshold=pixel,
        heatmap_display_max=display,
        validation_manifest_sha=validation_manifest_sha,
    )


def decide(score: float, calibration: Calibration, reasons: tuple[str, ...]) -> Decision:
    if reasons:
        return "review"
    if score <= calibration.low:
        return "pass"
    if score >= calibration.high:
        return "fail"
    return "review"
