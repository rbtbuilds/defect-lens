from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from defect_lens.imaging import InputRejected, decode_image


def test_huge_dimensions_and_corruption_are_rejected(tmp_path: Path) -> None:
    huge = tmp_path / "huge.png"
    Image.new("RGB", (4096, 4096)).save(huge)
    with pytest.raises(InputRejected, match="IMAGE_DIMENSIONS"):
        decode_image(huge)
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"corrupt")
    with pytest.raises(InputRejected, match="INVALID_IMAGE"):
        decode_image(bad)


def test_decoder_normalizes_rgb_and_exif(tmp_path: Path) -> None:
    path = tmp_path / "good.png"
    Image.new("L", (256, 256), 70).save(path)
    decoded = decode_image(path)
    assert decoded.shape == (256, 256, 3)
    assert decoded.dtype == np.uint8
    assert int(decoded[0, 0, 0]) == 70


def test_dimension_limit_is_checked_before_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "huge.png"
    Image.new("RGB", (4096, 4096)).save(path)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("pixels decoded before dimension admission")

    monkeypatch.setattr(Image.Image, "load", forbidden)
    with pytest.raises(InputRejected, match="IMAGE_DIMENSIONS"):
        decode_image(path)


def test_animation_is_rejected_and_exif_is_transposed(tmp_path: Path) -> None:
    animated = tmp_path / "animated.gif"
    Image.new("RGB", (128, 128)).save(
        animated, save_all=True, append_images=[Image.new("RGB", (128, 128), "white")]
    )
    with pytest.raises(InputRejected, match="UNSUPPORTED_IMAGE"):
        decode_image(animated)
    exif = Image.Exif()
    exif[274] = 3
    image = Image.new("RGB", (256, 256), "black")
    image.paste("white", (0, 0, 128, 128))
    path = tmp_path / "rotated.jpg"
    image.save(path, exif=exif)
    assert int(decode_image(path)[220, 220, 0]) > 240
