"""Full-image public-photo diagnostics; never a product or held-out accuracy claim."""

import hashlib
import json
import platform
import time
from collections.abc import Callable, Sequence
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image

from defect_lens.contracts import Contract, Decision
from defect_lens.evaluation import (
    Metrics,
    PredictionRow,
    pixel_average_precision,
    summarize_predictions,
)
from defect_lens.imaging import RgbFrame
from defect_lens.inference.calibration import Calibration, LabelledScore, calibrate, decide
from defect_lens.inference.patch import ResNetEncoder, chunked_nearest, reservoir_bank
from defect_lens.manifests import contained, file_hash
from defect_lens.photographs import PhotoManifest, PhotoSample, validate_photos

Heatmap = NDArray[np.float32]
Scorer = Callable[[RgbFrame], Heatmap]


class PhotoPrediction(Contract):
    source_image: str
    truth: str
    decision: Decision = "review"
    score: float | None = None
    binary_fail: bool = False
    latency_ms: float | None = None
    iou: float | None = None
    pixel_ap: float | None = None
    error: str | None = None


class PhotoDiagnostics(Contract):
    rows: list[PhotoPrediction]
    calibration: Calibration | None
    metrics: Metrics
    warm_median_ms: float | None
    warm_p95_ms: float | None


def load_photo(path: Path, *, mask: bool = False) -> NDArray[np.uint8]:
    with Image.open(path) as image:
        if image.width * image.height > 8_000_000 or max(image.size) > 4096:
            raise ValueError("Photograph exceeds decoding bounds")
        resized = image.convert("L" if mask else "RGB").resize(
            (256, 256), Image.Resampling.NEAREST if mask else Image.Resampling.BILINEAR
        )
        return np.asarray(resized, dtype=np.uint8)


def full_image_score(heatmap: Heatmap) -> float:
    if heatmap.shape != (256, 256) or not np.isfinite(heatmap).all():
        raise ValueError("Finite full-frame heatmap required")
    values = heatmap.reshape(-1)
    count = int(np.ceil(len(values) * 0.01))
    return float(np.mean(np.partition(values, -count)[-count:]))


def difference_heatmap(frame: RgbFrame, reference: RgbFrame) -> Heatmap:
    delta = frame.astype(np.float32) - reference.astype(np.float32)
    offset = np.clip(np.median(delta, axis=(0, 1)), -20, 20)
    difference = np.mean(np.abs(delta - offset), axis=2) / 255
    return np.asarray(cv2.GaussianBlur(difference, (3, 3), 0), dtype=np.float32)


def build_scorer(method: str, fit: Sequence[RgbFrame], weights: Path) -> Scorer:
    if len(fit) < 4:
        raise ValueError("At least four good fit photographs required")
    if method == "difference":
        reference = np.median(np.stack(fit), axis=0).astype(np.uint8)
        return lambda frame: difference_heatmap(frame, reference)
    if method != "resnet18_patch":
        raise ValueError("Unknown photographic method")
    encoder = ResNetEncoder(weights)
    bank = reservoir_bank((encoder.encode(frame) for frame in fit), seed=20261017)

    def score(frame: RgbFrame) -> Heatmap:
        distances = chunked_nearest(encoder.encode(frame), bank).reshape(32, 32)
        return np.asarray(cv2.resize(distances, (256, 256)), dtype=np.float32)

    return score


def diagnose(scorer: Scorer, samples: Sequence[PhotoSample], root: Path) -> PhotoDiagnostics:
    if any(sample.partition != "development" for sample in samples):
        raise ValueError("Diagnostics accept development rows only")
    rows: list[PhotoPrediction] = []
    labelled: list[LabelledScore] = []
    for sample in samples:
        row = PhotoPrediction(source_image=sample.image_path, truth=sample.label)
        try:
            started = time.perf_counter_ns()
            heatmap = scorer(load_photo(contained(root, sample.image_path)))
            row.score = full_image_score(heatmap)
            row.latency_ms = (time.perf_counter_ns() - started) / 1e6
            mask = (
                load_photo(contained(root, sample.mask_path), mask=True)
                if sample.mask_path
                else None
            )
            labelled.append(
                LabelledScore(sample.image_path, "unknown", sample.label, row.score, heatmap, mask)
            )
        except (OSError, ValueError, RuntimeError, cv2.error) as error:
            row.error = type(error).__name__
        rows.append(row)
    calibration = None
    if {s.truth for s in labelled} == {"good", "defect"}:
        subset_sha = hashlib.sha256(
            json.dumps([sample.model_dump() for sample in samples], sort_keys=True).encode()
        ).hexdigest()
        calibration = calibrate(labelled, subset_sha)
        calibration.seed = 20261017
        by_image = {s.sample_id: s for s in labelled}
        for row in rows:
            if row.error or row.score is None:
                continue
            row.decision = decide(row.score, calibration, ())
            row.binary_fail = row.score >= calibration.high
            score = by_image[row.source_image]
            if score.mask is not None and score.heatmap is not None:
                actual = score.mask > 0
                predicted = score.heatmap >= float(calibration.pixel_threshold or 0)
                union = int(np.count_nonzero(actual | predicted))
                row.iou = float(np.count_nonzero(actual & predicted)) / union if union else 1
                row.pixel_ap = pixel_average_precision(score.heatmap, actual)
    else:
        for row in rows:
            row.error = row.error or "InsufficientDevelopmentLabels"
    metrics = summarize_predictions(
        [
            PredictionRow(
                sample_id=row.source_image,
                specimen_id="unknown",
                truth="good" if row.truth == "good" else "defect",
                decision=row.decision,
                score=row.score,
                binary_fail=row.binary_fail,
                iou=row.iou,
                pixel_ap=row.pixel_ap,
                error=row.error,
            )
            for row in rows
        ]
    )
    latencies = [row.latency_ms for row in rows if row.latency_ms is not None and row.error is None]
    return PhotoDiagnostics(
        rows=rows,
        calibration=calibration,
        metrics=metrics,
        warm_median_ms=float(np.median(latencies)) if latencies else None,
        warm_p95_ms=float(np.percentile(latencies, 95)) if latencies else None,
    )


def compare(root: Path, output: Path, weights: Path, protocol: Path) -> None:
    manifest_path = root / "manifest.json"
    manifest = PhotoManifest.model_validate_json(manifest_path.read_bytes())
    validate_photos(manifest, root)
    if file_hash(protocol) != manifest.protocol_sha256:
        raise ValueError("Frozen photo protocol hash mismatch")
    if not file_hash(weights).startswith("f37072fd"):
        raise ValueError("Expected official ResNet18 checkpoint checksum")
    if output.exists():
        raise ValueError("Refusing to overwrite diagnostic report")
    fit = [
        load_photo(contained(root, s.image_path)) for s in manifest.samples if s.partition == "fit"
    ]
    development = [s for s in manifest.samples if s.partition == "development"]
    methods: dict[str, object] = {}
    complete = True
    for method in ["difference", "resnet18_patch"]:
        started = time.perf_counter_ns()
        scorer = build_scorer(method, fit, weights)
        first = load_photo(contained(root, development[0].image_path))
        full_image_score(scorer(first))
        cold_ms = (time.perf_counter_ns() - started) / 1e6
        for _ in range(3):
            full_image_score(scorer(first))
        diagnostic = diagnose(scorer, development, root)
        complete = complete and diagnostic.metrics.failures == 0
        methods[method] = {**diagnostic.model_dump(), "cold_build_first_inference_ms": cold_ms}
        del scorer
    source_paths = [
        Path(__file__),
        Path(__file__).with_name("photographs.py"),
        Path(__file__).with_name("evaluation.py"),
        *[Path(__file__).parent / "inference" / name for name in ["patch.py", "calibration.py"]],
        Path("scripts/evaluate_photographs.py"),
    ]
    report = {
        "schema_version": 1,
        "complete": complete,
        "evidence": "public photographs; actual CPU inference; development resubstitution",
        "final_evaluation": "BLOCKED: physical specimen and session IDs unknown",
        "domain_shift": "VisA multiple candles; full-image adapter, not the fixed-camera plate API",
        "physical_independence_verified": False,
        "human_review": False,
        "protocol_sha256": manifest.protocol_sha256,
        "manifest_sha256": file_hash(manifest_path),
        "weights_sha256": file_hash(weights),
        "source_hashes": {str(p.relative_to(Path.cwd())): file_hash(p) for p in source_paths},
        "lock_hashes": {
            name: file_hash(Path(name)) for name in ["uv.lock", "web/package-lock.json"]
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "opencv": cv2.__version__,
        },
        "timing_scope": "CPU, torch2/OpenCV1; warm decode/resize/scoring only; cold excludes fit image decode; no API/disk report/mask metric time",
        "intervals": None,
        "interval_reason": "No verified independent physical specimen groups",
        "methods": methods,
    }
    output.mkdir(parents=True)
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
