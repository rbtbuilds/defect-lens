import hashlib
import json
import platform
import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
import psutil
from PIL import Image
from pydantic import Field

from defect_lens.contracts import Contract, DataMode, DatasetManifest, Decision
from defect_lens.errors import DomainError
from defect_lens.imaging import decode_image, inspect_input
from defect_lens.inference.calibration import decide
from defect_lens.inference.preprocess import prepare_frame
from defect_lens.lease import DEFAULT_LEASE, MachineLease
from defect_lens.manifests import contained, file_hash, validate_manifest
from defect_lens.models import (
    ModelManifest,
    canonical,
    load_model,
    read_model_manifest,
    subset_hash,
)


class PredictionRow(Contract):
    sample_id: str
    specimen_id: str
    truth: Literal["good", "defect", "ambiguous"]
    decision: Decision
    score: float | None
    binary_fail: bool
    sample_sha256: str = ""
    lighting: str = "normal"
    blur: str = "none"
    reasons: list[str] = Field(default_factory=list)
    timings_ms: dict[str, float] = Field(default_factory=dict)
    iou: float | None = None
    pixel_ap: float | None = None
    error: str | None = None


class Metrics(Contract):
    precision: float | None
    recall: float | None
    false_reject_rate: float | None
    missed_defect_rate: float | None
    defect_pass_rate: float | None
    review_burden: float | None
    labelled_count: int
    ambiguous_count: int
    ambiguous_review_rate: float | None
    confusion: dict[str, int]
    localization_iou: float | None
    pixel_average_precision: float | None
    failures: int


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def summarize_predictions(rows: Sequence[PredictionRow]) -> Metrics:
    labelled = [r for r in rows if r.truth != "ambiguous" and r.error is None]
    good = [r for r in labelled if r.truth == "good"]
    defects = [r for r in labelled if r.truth == "defect"]
    tp = sum(r.binary_fail for r in defects)
    fp = sum(r.binary_fail for r in good)
    ambiguous = [r for r in rows if r.truth == "ambiguous"]
    overlaps = [r.iou for r in rows if r.iou is not None]
    aps = [r.pixel_ap for r in rows if r.pixel_ap is not None]
    return Metrics(
        precision=ratio(tp, tp + fp),
        recall=ratio(tp, len(defects)),
        false_reject_rate=ratio(fp, len(good)),
        missed_defect_rate=ratio(len(defects) - tp, len(defects)),
        defect_pass_rate=ratio(sum(r.decision == "pass" for r in defects), len(defects)),
        review_burden=ratio(sum(r.decision == "review" for r in rows), len(rows)),
        labelled_count=len(labelled),
        ambiguous_count=len(ambiguous),
        ambiguous_review_rate=ratio(sum(r.decision == "review" for r in ambiguous), len(ambiguous)),
        confusion={"tp": tp, "fp": fp, "fn": len(defects) - tp, "tn": len(good) - fp},
        localization_iou=float(np.mean(overlaps)) if overlaps else None,
        pixel_average_precision=float(np.mean(aps)) if aps else None,
        failures=sum(r.error is not None for r in rows),
    )


class IntervalSet(Contract):
    intervals: dict[str, tuple[float, float]] | None
    reason: str | None
    repeats: int = 1000
    seed: int = 20261015


def bootstrap_by_specimen(
    rows: Sequence[PredictionRow], seed: int = 20261015, repeats: int = 1000
) -> IntervalSet:
    groups = sorted({r.specimen_id for r in rows})
    if len(groups) < 5:
        return IntervalSet(
            intervals=None,
            reason="Fewer than five physical specimen groups",
            repeats=repeats,
            seed=seed,
        )
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {
        key: []
        for key in [
            "precision",
            "recall",
            "false_reject_rate",
            "missed_defect_rate",
            "defect_pass_rate",
            "review_burden",
        ]
    }
    grouped = {group: [r for r in rows if r.specimen_id == group] for group in groups}
    for _ in range(repeats):
        sampled = [
            row
            for group in rng.choice(groups, len(groups), replace=True)
            for row in grouped[str(group)]
        ]
        metrics = summarize_predictions(sampled).model_dump()
        for key, collected in values.items():
            value = metrics[key]
            if isinstance(value, float):
                collected.append(value)
    return IntervalSet(
        intervals={
            key: (float(np.percentile(value, 2.5)), float(np.percentile(value, 97.5)))
            for key, value in values.items()
            if value
        },
        reason=None,
        repeats=repeats,
        seed=seed,
    )


class MethodReport(Contract):
    model: ModelManifest
    data_mode: DataMode
    execution_mode: Literal["real_difference", "real_pretrained"]
    rows: list[PredictionRow]
    metrics: Metrics
    intervals: IntervalSet
    slices: dict[str, Metrics]
    cold_load_first_inference_ms: float
    warm_latency_median_ms: float
    warm_latency_p95_ms: float
    throughput_per_second: float
    peak_combined_rss_bytes: int = 0
    api_timings_ms: list[float] = Field(default_factory=lambda: list[float]())
    api_timing_note: str = "Actual ASGI HTTP transport including queue, decode, alignment, inference and artifact storage; excludes TCP"
    timing_method: str = "perf_counter_ns; one cold load+first inference; three excluded warmups; all held-out samples timed including decode/alignment/scoring/PNG storage"
    localization_note: str = "Mean per-image pixel AP and IoU over known defect masks, in aligned coordinates; absent masks yield null"


class EvaluationReport(Contract):
    schema_version: int = 1
    claim_level: Literal["fixture", "owned_capture"]
    data_mode: DataMode
    complete: bool
    manifest_sha256: str
    environment: dict[str, str | int]
    methods: list[MethodReport]
    unavailable_reasons: list[str] = Field(default_factory=list)


def environment() -> dict[str, str | int]:
    chip = (
        subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        if sys.platform == "darwin"
        else platform.processor()
    )
    return {
        "os": platform.platform(),
        "chip": chip,
        "ram_bytes": psutil.virtual_memory().total,
        "python": platform.python_version(),
        "device": "cpu",
        "numpy": np.__version__,
        "opencv": cv2.__version__,
    }


def verify_provenance(dataset: DatasetManifest, model: ModelManifest, root: Path) -> None:
    train = sorted([s for s in dataset.samples if s.split == "train"], key=lambda s: s.id)
    validation = [s for s in dataset.samples if s.split == "validation"]
    if (
        subset_hash(train) != model.training_hash
        or subset_hash(validation) != model.validation_hash
        or dataset.mode != model.data_mode
    ):
        raise ValueError("Dataset provenance differs from frozen model")
    validate_manifest(dataset, root)


def evaluate_one(
    dataset: DatasetManifest, model_directory: Path, root: Path, output: Path, token: str
) -> MethodReport:
    model = read_model_manifest(model_directory)
    verify_provenance(dataset, model, root)
    samples = [s for s in dataset.samples if s.split == "test"]
    if not samples:
        raise ValueError("No held-out samples")
    started = time.perf_counter_ns()
    bundle = load_model(model_directory, token)
    first = contained(root, samples[0].image_path)
    bundle.inspect(decode_image(first), inspect_input(first))
    cold = (time.perf_counter_ns() - started) / 1e6
    for _ in range(3):
        bundle.inspect(decode_image(first), inspect_input(first))
    rows: list[PredictionRow] = []
    output.mkdir(parents=True, exist_ok=True)
    gallery = output / "failure-gallery"
    gallery.mkdir(exist_ok=True)
    for sample in samples:
        begin = time.perf_counter_ns()
        row = PredictionRow(
            sample_id=sample.id,
            specimen_id=sample.specimen_id,
            truth=sample.label,
            decision="review",
            score=None,
            binary_fail=False,
            sample_sha256=sample.image_sha256,
            lighting=sample.lighting,
            blur=sample.blur,
        )
        try:
            path = contained(root, sample.image_path)
            if file_hash(path) != sample.image_sha256:
                raise ValueError("Image checksum changed")
            frame = decode_image(path)
            metadata = inspect_input(path)
            decoded = time.perf_counter_ns()
            prepared = prepare_frame(frame, bundle.anchor, metadata)
            aligned = time.perf_counter_ns()
            result = bundle.scorer.score(prepared)
            inferred = time.perf_counter_ns()
            row.decision = decide(result.score, model.calibration, result.reasons)
            row.score = None if result.reasons else result.score
            row.binary_fail = not result.reasons and result.score >= model.calibration.high
            row.reasons = list(result.reasons)
            from defect_lens.worker import persist_prepared

            persist_prepared(bundle, prepared, result, row.decision, output, f"heldout-{sample.id}")
            stored = time.perf_counter_ns()
            row.timings_ms = {
                "decode": (decoded - begin) / 1e6,
                "alignment": (aligned - decoded) / 1e6,
                "inference": (inferred - aligned) / 1e6,
                "storage": (stored - inferred) / 1e6,
                "total": (stored - begin) / 1e6,
            }
            if sample.mask_path and not result.reasons:
                with Image.open(contained(root, sample.mask_path)) as image:
                    mask = np.asarray(image, dtype=np.uint8)
                if prepared.transform is not None:
                    mask = np.asarray(
                        cv2.warpAffine(
                            mask,
                            prepared.transform,
                            (256, 256),
                            flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
                        ),
                        dtype=np.uint8,
                    )
                actual = mask[32:224, 32:224] > 0
                values = result.heatmap[32:224, 32:224]
                if model.calibration.pixel_threshold is not None:
                    predicted = values >= model.calibration.pixel_threshold
                    union = int(np.count_nonzero(predicted | actual))
                    row.iou = float(np.count_nonzero(predicted & actual)) / union if union else 1
                ranked = actual.reshape(-1)[np.argsort(-values.reshape(-1), kind="stable")]
                if np.count_nonzero(ranked):
                    precision = np.cumsum(ranked) / (np.arange(len(ranked)) + 1)
                    row.pixel_ap = float(precision[ranked].mean())
            if (
                (sample.label == "good" and row.binary_fail)
                or (sample.label == "defect" and not row.binary_fail)
                or sample.label == "ambiguous"
            ):
                Image.fromarray(prepared.rgb).save(gallery / f"{sample.id}.png")
        except (OSError, ValueError, RuntimeError, cv2.error, DomainError):
            row.error = "Evaluation sample failed; report is incomplete"
        rows.append(row)
    latencies = [r.timings_ms["total"] for r in rows if "total" in r.timings_ms]
    return MethodReport(
        model=model,
        data_mode=dataset.mode,
        execution_mode="real_difference" if model.method == "difference" else "real_pretrained",
        rows=rows,
        metrics=summarize_predictions(rows),
        intervals=bootstrap_by_specimen(rows),
        slices={
            f"{field}:{value}": summarize_predictions(
                [r for r in rows if getattr(r, field) == value]
            )
            for field in ["lighting", "blur"]
            for value in sorted({str(getattr(r, field)) for r in rows})
        },
        cold_load_first_inference_ms=cold,
        warm_latency_median_ms=float(np.median(latencies)) if latencies else 0,
        warm_latency_p95_ms=float(np.percentile(latencies, 95)) if latencies else 0,
        throughput_per_second=1000 * len(latencies) / sum(latencies) if sum(latencies) else 0,
    )


def evaluate(
    dataset: DatasetManifest,
    models: Sequence[ModelManifest],
    output: Path,
    *,
    dataset_root: Path,
    model_directories: Sequence[Path],
    lease_path: Path = DEFAULT_LEASE,
) -> EvaluationReport:
    if len(models) != len(model_directories) or not models:
        raise ValueError("Explicit model directories required")
    for model in models:
        verify_provenance(dataset, model, dataset_root)
    output.mkdir(parents=True, exist_ok=False)
    frozen = output / "split-manifest.json"
    frozen.write_text(dataset.model_dump_json(indent=2) + "\n")
    methods: list[MethodReport] = []
    with MachineLease(lease_path).acquire("complete frozen comparison benchmark") as handle:
        for model, directory in zip(models, model_directories, strict=True):
            destination = output / model.method
            command = [
                sys.executable,
                "-m",
                "defect_lens.evaluation_runner",
                str(frozen.resolve()),
                str(dataset_root.resolve()),
                str(directory.resolve()),
                str(destination.resolve()),
                handle.token,
            ]
            peak = psutil.Process().memory_info().rss
            stopped = threading.Event()

            def monitor(event: threading.Event = stopped) -> None:
                nonlocal peak
                while not event.wait(0.01):
                    parent = psutil.Process()
                    total = parent.memory_info().rss
                    for child in parent.children(recursive=True):
                        try:
                            total += child.memory_info().rss
                        except psutil.Error:
                            pass
                    peak = max(peak, total)

            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
            try:
                subprocess.run(command, check=True)
                report = MethodReport.model_validate_json(
                    (destination / "method-report.json").read_bytes()
                )
                # API timing runs in a separate process after the pipeline model exits.
                if lease_path == DEFAULT_LEASE:
                    subprocess.run([*command, "--api"], check=True)
                    report.api_timings_ms = json.loads(
                        (destination / "api-timing.json").read_bytes()
                    )
                else:
                    report.api_timing_note = "Not run in this light integration test; production benchmark uses actual ASGI flow"
                report.peak_combined_rss_bytes = peak
                methods.append(report)
            finally:
                stopped.set()
                thread.join()
    report = EvaluationReport(
        claim_level="fixture" if dataset.mode == "procedural" else "owned_capture",
        data_mode=dataset.mode,
        complete=all(r.error is None for method in methods for r in method.rows),
        manifest_sha256=hashlib.sha256(canonical(dataset.model_dump())).hexdigest(),
        environment=environment(),
        methods=methods,
    )
    (output / "report.json").write_text(report.model_dump_json(indent=2) + "\n")
    (output / "environment.json").write_text(json.dumps(report.environment, indent=2) + "\n")
    return report
