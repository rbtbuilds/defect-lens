from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast
from urllib.request import urlopen

import cv2
import numpy as np
from numpy.typing import NDArray

from defect_lens.imaging import RgbFrame
from defect_lens.inference.base import ScoreResult
from defect_lens.inference.difference import image_score
from defect_lens.inference.preprocess import PreparedFrame
from defect_lens.manifests import file_hash

if TYPE_CHECKING:
    import torch

PatchMatrix = NDArray[np.float32]
WEIGHT_URL = "https://download.pytorch.org/models/resnet18-f37072fd.pth"


class PatchEncoder(Protocol):
    def encode(self, frame: RgbFrame) -> PatchMatrix: ...


def normalize_rgb(frame: RgbFrame) -> "torch.Tensor":
    import torch

    pixels = (
        torch.frombuffer(bytearray(frame.tobytes()), dtype=torch.uint8)
        .reshape(256, 256, 3)
        .permute(2, 0, 1)
        .to(dtype=torch.float32)
        / 255
    )
    return (
        (pixels - torch.tensor([0.485, 0.456, 0.406])[:, None, None])
        / torch.tensor([0.229, 0.224, 0.225])[:, None, None]
    ).unsqueeze(0)


class ResNetEncoder:
    def __init__(self, weights: Path):
        import torch
        from torchvision.models import resnet18
        from torchvision.models.feature_extraction import create_feature_extractor

        torch.set_num_threads(2)
        cv2.setNumThreads(1)
        network = resnet18(weights=None)
        state = cast(
            dict[str, torch.Tensor], torch.load(weights, map_location="cpu", weights_only=True)
        )
        network.load_state_dict(state)
        self.extractor = create_feature_extractor(
            network, return_nodes={"layer2": "patches"}
        ).eval()

    def encode(self, frame: RgbFrame) -> PatchMatrix:
        import torch

        with torch.inference_mode():
            outputs = cast(dict[str, torch.Tensor], self.extractor(normalize_rgb(frame)))
            features = outputs["patches"]
            if tuple(features.shape) != (1, 128, 32, 32):
                raise ValueError("Unexpected feature map shape")
            vectors = features[0].permute(1, 2, 0).reshape(-1, 128)
            vectors = torch.nn.functional.normalize(vectors, dim=1)
            return np.asarray(vectors.numpy(), dtype=np.float32)


def download_weights(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "resnet18-f37072fd.pth"
    if not target.exists():
        temporary = directory / "download.part"
        with urlopen(WEIGHT_URL, timeout=60) as response, temporary.open("wb") as stream:
            while chunk := response.read(65536):
                stream.write(chunk)
                if stream.tell() > 64 * 1024 * 1024:
                    raise ValueError("Checkpoint exceeds expected size")
        if not file_hash(temporary).startswith("f37072fd"):
            raise ValueError("Upstream checkpoint checksum mismatch")
        temporary.replace(target)
    if not file_hash(target).startswith("f37072fd"):
        raise ValueError("Checkpoint checksum mismatch")
    return target


def chunked_nearest(query: PatchMatrix, bank: PatchMatrix) -> NDArray[np.float32]:
    if (
        query.ndim != 2
        or bank.ndim != 2
        or query.shape[1] != 128
        or bank.shape[1] != 128
        or len(bank) == 0
        or len(bank) > 4096
    ):
        raise ValueError("Invalid patch matrices")
    minimum = np.full(len(query), np.inf, dtype=np.float32)
    for q in range(0, len(query), 128):
        block = query[q : q + 128]
        for b in range(0, len(bank), 512):
            reference = bank[b : b + 512]
            distances = np.maximum(
                np.sum(block * block, axis=1)[:, None]
                + np.sum(reference * reference, axis=1)[None, :]
                - 2 * block @ reference.T,
                0,
            )
            minimum[q : q + len(block)] = np.minimum(
                minimum[q : q + len(block)], np.sqrt(distances).min(axis=1)
            )
    return minimum


def reservoir_bank(stream: Iterable[PatchMatrix], seed: int) -> PatchMatrix:
    rng = np.random.default_rng(seed)
    bank = np.empty((4096, 128), dtype=np.float32)
    count = 0
    for vectors in stream:
        for vector in vectors:
            if count < 4096:
                bank[count] = vector
            else:
                slot = int(rng.integers(0, count + 1))
                if slot < 4096:
                    bank[slot] = vector
            count += 1
    if count == 0:
        raise ValueError("Empty training bank")
    return bank[: min(count, 4096)].copy()


@dataclass
class PatchScorer:
    bank: PatchMatrix
    encoder: PatchEncoder

    def score(self, frame: PreparedFrame) -> ScoreResult:
        distances = chunked_nearest(self.encoder.encode(frame.rgb), self.bank).reshape(32, 32)
        heatmap = np.asarray(
            cv2.resize(distances, (256, 256), interpolation=cv2.INTER_LINEAR), dtype=np.float32
        )
        heatmap[:32] = heatmap[224:] = 0
        heatmap[:, :32] = heatmap[:, 224:] = 0
        return ScoreResult(image_score(heatmap), heatmap, frame.quality_reasons)


def fit_patch(train: Sequence[RgbFrame], encoder: PatchEncoder, seed: int) -> PatchScorer:
    if len(train) < 4:
        raise ValueError("At least four accepted good frames required")

    def patches() -> Iterable[PatchMatrix]:
        for frame in train:
            yield encoder.encode(frame).reshape(32, 32, 128)[4:28, 4:28].reshape(-1, 128)

    return PatchScorer(reservoir_bank(patches(), seed), encoder)
