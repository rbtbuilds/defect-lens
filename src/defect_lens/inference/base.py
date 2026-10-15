from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from defect_lens.inference.preprocess import PreparedFrame

Heatmap = NDArray[np.float32]


@dataclass(frozen=True)
class ScoreResult:
    score: float
    heatmap: Heatmap
    reasons: tuple[str, ...] = ()


class Scorer(Protocol):
    def score(self, frame: PreparedFrame) -> ScoreResult: ...
