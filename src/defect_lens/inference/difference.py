import math
from collections.abc import Sequence
from dataclasses import dataclass

import cv2
import numpy as np

from defect_lens.imaging import RgbFrame
from defect_lens.inference.base import Heatmap, ScoreResult
from defect_lens.inference.preprocess import PreparedFrame


def image_score(heatmap: Heatmap) -> float:
    values = heatmap[32:224, 32:224].reshape(-1)
    count = max(1, math.ceil(len(values) * 0.01))
    return float(np.partition(values, -count)[-count:].mean())


@dataclass
class DifferenceScorer:
    reference: RgbFrame

    def score(self, frame: PreparedFrame) -> ScoreResult:
        source = frame.rgb.astype(np.float32) / 255
        reference = self.reference.astype(np.float32) / 255
        offset = np.clip(np.median((source - reference)[32:224, 32:224], axis=(0, 1)), -0.1, 0.1)
        difference = np.abs(np.clip(source - offset, 0, 1) - reference).mean(axis=2)
        heatmap = np.asarray(cv2.GaussianBlur(difference, (3, 3), 0), dtype=np.float32)
        heatmap[:32] = 0
        heatmap[224:] = 0
        heatmap[:, :32] = 0
        heatmap[:, 224:] = 0
        return ScoreResult(image_score(heatmap), heatmap, frame.quality_reasons)


def fit_difference(train: Sequence[RgbFrame]) -> DifferenceScorer:
    if len(train) < 4:
        raise ValueError("at least four accepted good training frames required")
    reference = np.median(np.stack(train), axis=0).astype(np.uint8)
    return DifferenceScorer(reference)
