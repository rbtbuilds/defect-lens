import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np

from defect_lens.contracts import (
    Contract,
    DataMode,
    DatasetManifest,
    Decision,
    InputMetadata,
    Method,
    SampleRecord,
)
from defect_lens.imaging import RgbFrame, decode_image, inspect_input
from defect_lens.inference.base import Scorer, ScoreResult
from defect_lens.inference.calibration import Calibration, LabelledScore, calibrate, decide
from defect_lens.inference.difference import DifferenceScorer, fit_difference
from defect_lens.inference.preprocess import PreparedFrame, prepare_frame
from defect_lens.manifests import contained, file_hash, validate_groups, validate_manifest


class ModelIntegrityError(ValueError):
    pass


INFERENCE_CONFIG = {
    "size": 256,
    "roi": [32, 224],
    "ecc_iterations": 40,
    "ecc_epsilon": 1e-5,
    "angle_limit": 5,
    "translation_limit": 12,
    "correlation_min": 0.8,
    "blur_variance_min": 20,
    "clipped_fraction_max": 0.25,
    "top_fraction": 0.01,
    "brightness_limit": 0.1,
}


class ModelManifest(Contract):
    revision: str
    method: Method
    data_mode: DataMode
    source_hash: str
    lock_hashes: dict[str, str]
    training_hash: str
    validation_hash: str
    artifact_hashes: dict[str, str]
    calibration: Calibration
    seed: int
    inference_config: dict[str, object]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


class CurrentPointer(Contract):
    revision: str


def resolve_model(directory: Path) -> Path:
    if (directory / "CURRENT.json").exists():
        revision = CurrentPointer.model_validate_json(
            (directory / "CURRENT.json").read_bytes()
        ).revision
        if not re.fullmatch("[0-9a-f]{64}", revision):
            raise ModelIntegrityError("invalid revision")
        return contained(directory, f"revisions/{revision}")
    return directory


@dataclass
class ModelBundle:
    manifest: ModelManifest
    anchor: RgbFrame
    scorer: Scorer

    def inspect(
        self, frame: RgbFrame, metadata: InputMetadata
    ) -> tuple[PreparedFrame, ScoreResult, Decision]:
        prepared = prepare_frame(frame, self.anchor, metadata)
        result = self.scorer.score(prepared)
        return prepared, result, decide(result.score, self.manifest.calibration, result.reasons)


def read_model_manifest(directory: Path) -> ModelManifest:
    return ModelManifest.model_validate_json(
        (resolve_model(directory) / "manifest.json").read_bytes()
    )


def inference_source_hash() -> str:
    root = Path(__file__).parent
    paths = [
        *sorted((root / "inference").glob("*.py")),
        *[
            root / name
            for name in [
                "__init__.py",
                "models.py",
                "imaging.py",
                "manifests.py",
                "config.py",
                "worker.py",
                "contracts.py",
                "captures.py",
            ]
        ],
    ]
    return hashlib.sha256(
        canonical({str(path.relative_to(root)): file_hash(path) for path in paths})
    ).hexdigest()


def load_model(directory: Path, lease_token: str | None = None) -> ModelBundle:
    root = resolve_model(directory)
    manifest = ModelManifest.model_validate_json((root / "manifest.json").read_bytes())
    if manifest.source_hash != inference_source_hash():
        raise ModelIntegrityError(
            "Inference source differs from frozen model; prepare a new revision"
        )
    repository_root = Path(__file__).parents[2]
    for name, expected in manifest.lock_hashes.items():
        if file_hash(contained(repository_root, name)) != expected:
            raise ModelIntegrityError("Dependency lock differs from frozen model")
    identity = manifest.model_dump(exclude={"revision"})
    if hashlib.sha256(canonical(identity)).hexdigest() != manifest.revision:
        raise ModelIntegrityError("model manifest identity mismatch")
    for relative, expected in manifest.artifact_hashes.items():
        if file_hash(contained(root, relative)) != expected:
            raise ModelIntegrityError("model artifact checksum mismatch")
    anchor = np.asarray(np.load(root / "anchor.npy", allow_pickle=False), dtype=np.uint8)
    scorer: Scorer
    if manifest.method == "difference":
        scorer = DifferenceScorer(
            np.asarray(np.load(root / "reference.npy", allow_pickle=False), dtype=np.uint8)
        )
    else:
        from defect_lens.lease import DEFAULT_LEASE, LeaseBusy, token_matches

        if lease_token is None or not token_matches(DEFAULT_LEASE, lease_token):
            raise LeaseBusy("Feature loading requires the owned machine lease")
        from defect_lens.inference.patch import PatchScorer, ResNetEncoder

        scorer = PatchScorer(
            np.asarray(np.load(root / "bank.npy", allow_pickle=False), dtype=np.float32),
            ResNetEncoder(root / "weights.pth"),
        )
    return ModelBundle(manifest, anchor, scorer)


def load_difference(directory: Path) -> DifferenceScorer:
    scorer = load_model(directory).scorer
    if not isinstance(scorer, DifferenceScorer):
        raise ModelIntegrityError("not a difference model")
    return scorer


def subset_hash(samples: Sequence[SampleRecord]) -> str:
    return hashlib.sha256(canonical([s.model_dump() for s in samples])).hexdigest()


def prepare_model(
    dataset: Path, method: Method, output: Path, *, _lease_token: str | None = None
) -> ModelManifest:
    if method == "resnet18_patch" and _lease_token is None:
        from defect_lens.lease import MachineLease, run_model_process

        with MachineLease().acquire("pretrained feature preparation") as handle:
            run_model_process(
                [
                    sys.executable,
                    "-m",
                    "defect_lens.feature_runner",
                    str(dataset.resolve()),
                    str(output.resolve()),
                    handle.token,
                ],
            )
        return read_model_manifest(output)
    if method == "resnet18_patch":
        from defect_lens.lease import DEFAULT_LEASE, LeaseBusy, token_matches

        if _lease_token is None or not token_matches(DEFAULT_LEASE, _lease_token):
            raise LeaseBusy("Feature preparation requires owned lease")
    all_data = DatasetManifest.model_validate_json(dataset.read_bytes())
    validate_groups(all_data)
    if all_data.mode == "owned_capture":
        from defect_lens.captures import validate_captures

        validation = validate_captures(all_data, dataset.parent)
        if not validation.valid:
            raise ValueError("Owned capture manifest failed rights/annotation validation")
    selected = all_data.model_copy(
        update={"samples": [s for s in all_data.samples if s.split != "test"]}
    )
    validate_manifest(selected, dataset.parent)
    train = sorted([s for s in selected.samples if s.split == "train"], key=lambda s: s.id)
    if not train or any(s.label != "good" for s in train):
        raise ValueError("training must contain good samples only")
    anchor = decode_image(contained(dataset.parent, train[0].image_path))
    aligned: list[RgbFrame] = []
    for sample in train:
        path = contained(dataset.parent, sample.image_path)
        frame = prepare_frame(decode_image(path), anchor, inspect_input(path))
        if not frame.quality_reasons:
            aligned.append(frame.rgb)
    scorer: Scorer
    weights: Path | None = None
    if method == "difference":
        scorer = fit_difference(aligned)
    else:
        from defect_lens.inference.patch import ResNetEncoder, download_weights, fit_patch

        weights = download_weights(output.parent / "weights")
        scorer = fit_patch(aligned, ResNetEncoder(weights), all_data.seed or 0)
    labelled: list[LabelledScore] = []
    validation = [s for s in selected.samples if s.split == "validation"]
    for sample in validation:
        if sample.label == "ambiguous":
            continue
        path = contained(dataset.parent, sample.image_path)
        frame = prepare_frame(decode_image(path), anchor, inspect_input(path))
        if frame.quality_reasons:
            continue
        result = scorer.score(frame)
        mask = None
        if sample.mask_path is not None:
            from PIL import Image

            with Image.open(contained(dataset.parent, sample.mask_path)) as image:
                mask = np.asarray(image, dtype=np.uint8)
            if frame.transform is not None and not (
                sample.capture_review and sample.capture_review.mask_coordinate_frame == "aligned"
            ):
                mask = np.asarray(
                    cv2.warpAffine(
                        mask,
                        frame.transform,
                        (256, 256),
                        flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
                    ),
                    dtype=np.uint8,
                )
        labelled.append(
            LabelledScore(
                sample.id, sample.specimen_id, sample.label, result.score, result.heatmap, mask
            )
        )
    calibration = calibrate(labelled, subset_hash(validation))
    output.mkdir(parents=True, exist_ok=True)
    stage = output / f".stage-{uuid4().hex}"
    stage.mkdir()
    np.save(stage / "anchor.npy", anchor, allow_pickle=False)
    if isinstance(scorer, DifferenceScorer):
        np.save(stage / "reference.npy", scorer.reference, allow_pickle=False)
    else:
        if weights is None:
            raise ValueError("Unexpected scorer")
        np.save(stage / "bank.npy", scorer.bank, allow_pickle=False)
        shutil.copyfile(weights, stage / "weights.pth")
    source_root = Path(__file__).parent
    source_hash = inference_source_hash()
    repository_root = source_root.parents[1]
    locks = {
        name: file_hash(repository_root / name)
        for name in ["uv.lock", "web/package-lock.json"]
        if (repository_root / name).exists()
    }
    fields = {
        "method": method,
        "data_mode": all_data.mode,
        "source_hash": source_hash,
        "lock_hashes": locks,
        "training_hash": subset_hash(train),
        "validation_hash": subset_hash(validation),
        "artifact_hashes": {p.name: file_hash(p) for p in stage.iterdir()},
        "calibration": calibration.model_dump(),
        "seed": all_data.seed or 0,
        "inference_config": INFERENCE_CONFIG,
    }
    revision = hashlib.sha256(canonical(fields)).hexdigest()
    manifest = ModelManifest.model_validate(dict(revision=revision, **fields))
    provenance = {
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip(),
        "git_dirty": bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repository_root,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
        ),
    }
    (stage / "provenance.json").write_bytes(canonical(provenance))
    (stage / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n")
    target = output / "revisions" / revision
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        if method == "difference":
            load_model(target)
        else:
            for relative, expected in manifest.artifact_hashes.items():
                if file_hash(contained(target, relative)) != expected:
                    raise ModelIntegrityError("Existing model artifact changed")
        for path in stage.iterdir():
            path.unlink()
        stage.rmdir()
    else:
        stage.rename(target)
    temporary = output / f".CURRENT-{uuid4().hex}.json"
    temporary.write_bytes(canonical({"revision": revision}))
    temporary.replace(output / "CURRENT.json")
    return manifest
