import warnings
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageOps, UnidentifiedImageError

from defect_lens.contracts import InputMetadata
from defect_lens.errors import DomainError
from defect_lens.manifests import file_hash

RgbFrame = NDArray[np.uint8]


class InputRejected(DomainError):
    def __init__(self, code: str, message: str = ""):
        status = 415 if code == "UNSUPPORTED_IMAGE" else 422
        super().__init__(code, message or code, status)


def inspect_input(path: Path) -> InputMetadata:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                if image.format not in {"PNG", "JPEG"} or getattr(image, "n_frames", 1) != 1:
                    raise InputRejected("UNSUPPORTED_IMAGE")
                width, height = image.size
                if (
                    not (128 <= width <= 4096 and 128 <= height <= 4096)
                    or width * height > 8_000_000
                ):
                    raise InputRejected("IMAGE_DIMENSIONS")
                return InputMetadata(
                    raw_sha256=file_hash(path),
                    width=width,
                    height=height,
                    aspect_ratio=width / height,
                    image_format=image.format,
                )
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise InputRejected("INVALID_IMAGE") from error


def decode_image(path: Path) -> RgbFrame:
    inspect_input(path)
    try:
        with Image.open(path) as image:
            image.load()
            rgb = ImageOps.exif_transpose(image).convert("RGB")
            normalized = ImageOps.pad(rgb, (256, 256), color=(48, 48, 48))
            return np.asarray(normalized, dtype=np.uint8).copy()
    except (OSError, ValueError) as error:
        raise InputRejected("INVALID_IMAGE") from error
