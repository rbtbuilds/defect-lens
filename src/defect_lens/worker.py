import logging
import os
from dataclasses import dataclass
from multiprocessing.queues import Queue
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from defect_lens.config import Settings
from defect_lens.contracts import Decision, InputMetadata, JobError, Region, StoredResult
from defect_lens.imaging import decode_image
from defect_lens.inference.base import ScoreResult
from defect_lens.inference.preprocess import PreparedFrame
from defect_lens.models import ModelBundle, load_model
from defect_lens.repository import Repository


@dataclass(frozen=True)
class WorkerSettings:
    settings: Settings
    model_path: Path
    lease_token: str | None = None


@dataclass(frozen=True)
class WorkerCommand:
    kind: str
    job_id: str = ""


@dataclass(frozen=True)
class WorkerEvent:
    kind: str
    job_id: str = ""
    result: StoredResult | None = None
    error: JobError | None = None


logger = logging.getLogger(__name__)


def regions_from(heatmap: np.typing.NDArray[np.float32], threshold: float | None) -> list[Region]:
    if threshold is None:
        return []
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (heatmap >= threshold).astype(np.uint8)
    )
    regions: list[Region] = []
    for index in range(1, count):
        x, y, width, height, area = (int(v) for v in stats[index])
        if area >= 4:
            regions.append(
                Region(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    peak_score=float(heatmap[labels == index].max()),
                )
            )
    return sorted(regions, key=lambda r: r.width * r.height, reverse=True)[:10]


def persist_result(
    bundle: ModelBundle, path: Path, metadata: InputMetadata, root: Path, job_id: str
) -> StoredResult:
    prepared, scored, decision = bundle.inspect(decode_image(path), metadata)
    return persist_prepared(bundle, prepared, scored, decision, root, job_id)


def persist_prepared(
    bundle: ModelBundle,
    prepared: PreparedFrame,
    scored: ScoreResult,
    decision: Decision,
    root: Path,
    job_id: str,
) -> StoredResult:
    if Path(job_id).name != job_id or job_id in {".", ".."}:
        raise ValueError("Artifact identifier must be one safe path component")
    directory = root / "outputs" / job_id
    directory.mkdir(parents=True, exist_ok=False)
    stage = directory / "aligned.part"
    Image.fromarray(prepared.rgb).save(stage, format="PNG")
    stage.replace(directory / "aligned.png")
    artifacts = {"aligned": str((directory / "aligned.png").relative_to(root))}
    regions: list[Region] = []
    if not scored.reasons:
        intensity = np.clip(scored.heatmap / bundle.manifest.calibration.heatmap_display_max, 0, 1)
        rgba = np.empty((256, 256, 4), dtype=np.uint8)
        rgba[:, :, 0] = 230
        rgba[:, :, 1] = (170 * (1 - intensity)).astype(np.uint8)
        rgba[:, :, 2] = (30 + 150 * intensity).astype(np.uint8)
        rgba[:, :, 3] = (intensity * 220).astype(np.uint8)
        Image.fromarray(rgba).save(directory / "heatmap.part", format="PNG")
        (directory / "heatmap.part").replace(directory / "heatmap.png")
        artifacts["heatmap"] = str((directory / "heatmap.png").relative_to(root))
        regions = regions_from(scored.heatmap, bundle.manifest.calibration.pixel_threshold)
    return StoredResult(
        decision=decision,
        score=None if scored.reasons else scored.score,
        reasons=list(scored.reasons),
        artifacts=artifacts,
        artifact_bytes=sum(p.stat().st_size for p in directory.iterdir()),
        regions=regions,
    )


def worker_main(
    settings: WorkerSettings, inbound: Queue[WorkerCommand], outbound: Queue[WorkerEvent]
) -> None:
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    cv2.setNumThreads(1)
    try:
        bundle = load_model(settings.model_path, settings.lease_token)
        repository = Repository(settings.settings)
        outbound.put(WorkerEvent("ready"))
        while True:
            command = inbound.get()
            if command.kind == "stop":
                break
            try:
                path, metadata = repository.input_for(command.job_id)
                result = persist_result(
                    bundle,
                    path,
                    InputMetadata.model_validate_json(metadata),
                    settings.settings.runtime,
                    command.job_id,
                )
                outbound.put(WorkerEvent("complete", command.job_id, result=result))
            except Exception:
                logger.exception("Inspection failed: %s", command.job_id)
                outbound.put(
                    WorkerEvent(
                        "failure",
                        command.job_id,
                        error=JobError(
                            code="INTERNAL", message="Inspection failed; consult local logs"
                        ),
                    )
                )
    except Exception:
        logger.exception("Worker initialization failed")
        outbound.put(
            WorkerEvent(
                "failure",
                error=JobError(
                    code="MODEL_UNAVAILABLE",
                    message="Selected model failed integrity or loading checks",
                ),
            )
        )
