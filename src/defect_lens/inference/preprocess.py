import math
from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from defect_lens.contracts import InputMetadata
from defect_lens.imaging import RgbFrame

cv2.setNumThreads(1)


@dataclass(frozen=True)
class PreparedFrame:
    rgb: RgbFrame
    alignment_score: float | None
    quality_reasons: tuple[str, ...]
    transform: NDArray[np.float32] | None = None


def prepare_frame(frame: RgbFrame, reference: RgbFrame, metadata: InputMetadata) -> PreparedFrame:
    reasons: list[str] = []
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    if not 0.9 <= metadata.aspect_ratio <= 1.1:
        reasons.append("framing")
    if float(cv2.Laplacian(gray, cv2.CV_64F).var()) < 20:
        reasons.append("blur")
    roi = gray[32:224, 32:224]
    if float(np.mean((roi <= 5) | (roi >= 250))) > 0.25:
        reasons.append("clipping")
    mask = np.zeros((256, 256), dtype=np.uint8)
    mask[24:232, 24:232] = 255
    mask[40:216, 40:216] = 0
    warp = np.eye(2, 3, dtype=np.float32)
    correlation: float | None = None
    try:
        coefficient, matrix = cv2.findTransformECC(
            cv2.cvtColor(reference, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255,
            gray.astype(np.float32) / 255,
            warp,
            cv2.MOTION_EUCLIDEAN,
            (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 40, 1e-5),
            mask,
        )
        correlation = float(coefficient)
        warp = np.asarray(matrix, dtype=np.float32)
        angle = math.degrees(math.atan2(float(warp[1, 0]), float(warp[0, 0])))
        if abs(angle) > 5 or np.abs(warp[:, 2]).max() > 12 or correlation < 0.8:
            reasons.append("alignment")
        else:
            frame = np.asarray(
                cv2.warpAffine(
                    frame,
                    warp,
                    (256, 256),
                    flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=(48, 48, 48),
                ),
                dtype=np.uint8,
            )
    except cv2.error:
        reasons.append("alignment")
    return PreparedFrame(frame, correlation, tuple(reasons), warp)
