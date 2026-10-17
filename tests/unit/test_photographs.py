import io
import tarfile
from pathlib import Path
from typing import Self

import pytest

from defect_lens.photographs import (
    PhotoManifest,
    PhotoSample,
    fetch_members,
    read_range,
    validate_photos,
)


def test_range_reader_fetches_only_selected_payload() -> None:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, data in [("skip.jpg", b"skip" * 10000), ("keep.jpg", b"photo")]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    blob = stream.getvalue()
    reads: list[tuple[int, int]] = []

    def read(start: int, size: int) -> bytes:
        reads.append((start, size))
        return blob[start : start + size]

    assert fetch_members(read, len(blob), {"keep.jpg"}) == {"keep.jpg": b"photo"}
    assert sum(size for _, size in reads) < 5000


@pytest.mark.parametrize("path", ["../escape.jpg", "/escape.jpg", "x/../../escape.jpg"])
def test_range_reader_refuses_unsafe_requested_paths(path: str) -> None:
    with pytest.raises(ValueError, match="path"):
        fetch_members(lambda _start, size: b"\0" * size, 10240, {path})


def test_missing_member_is_not_silently_omitted() -> None:
    with pytest.raises(ValueError, match="Missing"):
        fetch_members(lambda _start, size: b"\0" * size, 10240, {"absent.jpg"})


@pytest.mark.parametrize("status, content_range", [(200, ""), (206, "bytes 1-512/1929840640")])
def test_range_refusal_does_not_read_unbounded_response(
    monkeypatch: pytest.MonkeyPatch, status: int, content_range: str
) -> None:
    class Response:
        def __init__(self) -> None:
            self.status = status
            self.headers = {"Content-Range": content_range}

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *_args: object) -> None:
            pass

        def read(self, _size: int) -> bytes:
            raise AssertionError("Unbounded response body must not be read")

    def response(*_args: object, **_kwargs: object) -> Response:
        return Response()

    monkeypatch.setattr("defect_lens.photographs.urlopen", response)
    with pytest.raises(ValueError, match="range"):
        read_range(0, 512)


def sample(path: str, partition: str = "fit") -> PhotoSample:
    return PhotoSample.model_validate(
        {
            "image_path": path,
            "image_sha256": "a" * 64,
            "upstream_split": "train",
            "label": "good",
            "partition": partition,
        }
    )


def test_public_photos_cannot_claim_owned_or_confirmed_specimens() -> None:
    record = sample("image.jpg").model_dump()
    record["physical_specimen_id"] = "invented"
    with pytest.raises(ValueError):
        PhotoSample.model_validate(record)
    record.pop("physical_specimen_id")
    record["source"] = "owned_photo"
    with pytest.raises(ValueError):
        PhotoSample.model_validate(record)


def test_validation_rejects_hash_tampering_and_overlap(tmp_path: Path) -> None:
    (tmp_path / "image.jpg").write_bytes(b"changed")
    manifest = PhotoManifest(protocol_sha256="b" * 64, samples=[sample("image.jpg")])
    with pytest.raises(ValueError, match="hash"):
        validate_photos(manifest, tmp_path)
    manifest.samples.append(sample("image.jpg", "development"))
    with pytest.raises(ValueError, match="overlap|duplicate"):
        validate_photos(manifest, tmp_path)


def test_final_evaluation_refuses_unverified_physical_groups(tmp_path: Path) -> None:
    manifest = PhotoManifest(protocol_sha256="b" * 64, samples=[])
    with pytest.raises(ValueError, match="specimen"):
        validate_photos(manifest, tmp_path, final=True)
