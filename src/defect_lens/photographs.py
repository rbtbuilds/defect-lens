"""Public-photo provenance, independent of the owned-capture product contract."""

import csv
import hashlib
import io
import tarfile
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.request import Request, urlopen

from defect_lens.contracts import Contract
from defect_lens.manifests import contained, file_hash

UPSTREAM = "2a692ab575001cbde74d402d897a7286086c6199"
ARCHIVE = "https://amazon-visual-anomaly.s3.us-west-2.amazonaws.com/VisA_20220922.tar"
ARCHIVE_SIZE = 1929840640
ARCHIVE_ETAG = '"05c830591a1172938cb714895c9e0cfb-113"'


class PhotoSample(Contract):
    source: Literal["public_photograph"] = "public_photograph"
    image_path: str
    image_sha256: str
    mask_path: str | None = None
    mask_sha256: str | None = None
    upstream_split: Literal["train", "test"]
    label: Literal["good", "defect"]
    partition: Literal["fit", "development"]
    physical_specimen_id: None = None
    session_id: None = None


class PhotoManifest(Contract):
    dataset: Literal["VisA candle"] = "VisA candle"
    terms: Literal["CC-BY-4.0"] = "CC-BY-4.0"
    upstream_revision: str = UPSTREAM
    archive_url: str = ARCHIVE
    archive_etag: str = ARCHIVE_ETAG
    protocol_sha256: str
    csv_sha256: str = ""
    license_sha256: str = ""
    samples: list[PhotoSample]


def safe_path(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or not path.parts:
        raise ValueError("Unsafe archive path")


def fetch_members(
    read: Callable[[int, int], bytes], archive_size: int, wanted: set[str]
) -> dict[str, bytes]:
    for name in wanted:
        safe_path(name)
    found: dict[str, bytes] = {}
    position = 0
    headers = 0
    while position + 512 <= archive_size and found.keys() != wanted:
        header = read(position, 512)
        if len(header) != 512:
            raise ValueError("Truncated tar header")
        if header == b"\0" * 512:
            break
        info = tarfile.TarInfo.frombuf(header, "utf-8", "strict")
        headers += 1
        if headers > 25000 or info.size < 0 or position + 512 + info.size > archive_size:
            raise ValueError("Invalid or excessive archive members")
        if info.name in wanted:
            if not info.isfile() or info.size > 8 * 1024 * 1024:
                raise ValueError("Unsafe or oversized photo member")
            content = read(position + 512, info.size)
            if len(content) != info.size:
                raise ValueError("Truncated photo member")
            found[info.name] = content
        position += 512 + ((info.size + 511) // 512) * 512
    if found.keys() != wanted:
        raise ValueError(f"Missing archive members: {sorted(wanted - found.keys())}")
    return found


def read_range(start: int, size: int) -> bytes:
    end = start + size - 1
    request = Request(ARCHIVE, headers={"Range": f"bytes={start}-{end}", "If-Match": ARCHIVE_ETAG})
    with urlopen(request, timeout=45) as response:
        if response.status != 206 or response.headers.get("Content-Range") != (
            f"bytes {start}-{end}/{ARCHIVE_SIZE}"
        ):
            raise ValueError("Server did not honor bounded archive range")
        data = response.read(size + 1)
    if len(data) != size:
        raise ValueError("Range payload length mismatch")
    return data


def validate_photos(manifest: PhotoManifest, root: Path, *, final: bool = False) -> None:
    if final:
        raise ValueError("Final evaluation blocked: physical specimen/session identities unknown")
    paths = [s.image_path for s in manifest.samples]
    hashes = [s.image_sha256 for s in manifest.samples]
    if len(set(paths)) != len(paths) or len(set(hashes)) != len(hashes):
        raise ValueError("Photo overlap or duplicate image hashes")
    for sample in manifest.samples:
        if sample.partition == "fit" and sample.label != "good":
            raise ValueError("Only normal photographs may fit the reference")
        for name, digest in [
            (sample.image_path, sample.image_sha256),
            (sample.mask_path, sample.mask_sha256),
        ]:
            if name is not None:
                safe_path(name)
                if digest is None or file_hash(contained(root, name)) != digest:
                    raise ValueError("Photograph/mask hash mismatch")
        if sample.label == "defect" and sample.mask_path is None:
            raise ValueError("Defect photograph requires source mask")


def acquire(output: Path, evidence: Path, protocol: Path) -> PhotoManifest:
    if output.exists() or evidence.exists():
        raise ValueError("Refusing to overwrite photo acquisition or evidence")
    base = f"https://raw.githubusercontent.com/amazon-science/spot-diff/{UPSTREAM}/"

    def upstream(path: str) -> bytes:
        with urlopen(base + path, timeout=45) as response:
            data = response.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024:
            raise ValueError("Oversized upstream metadata")
        return data

    metadata = upstream("split_csv/1cls.csv")
    license_text = upstream("LICENSE-DATASET")
    rows = sorted(
        [r for r in csv.DictReader(io.StringIO(metadata.decode())) if r["object"] == "candle"],
        key=lambda r: r["image"],
    )
    normals = [r for r in rows if r["split"] == "train" and r["label"] == "normal"]
    anomalies = [r for r in rows if r["split"] == "test" and r["label"] == "anomaly"]
    if len(normals) < 24 or len(anomalies) < 12:
        raise ValueError("Upstream metadata cannot satisfy frozen selection")
    selected = [(r, "fit" if i < 12 else "development") for i, r in enumerate(normals[:24])]
    selected += [(r, "development") for r in anomalies[:12]]
    wanted = {r["image"] for r, _ in selected} | {r["mask"] for r, _ in selected if r["mask"]}
    payloads = fetch_members(read_range, ARCHIVE_SIZE, wanted)
    output.mkdir(parents=True)
    for name, content in payloads.items():
        destination = contained(output, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    samples = [
        PhotoSample.model_validate(
            {
                "image_path": r["image"],
                "image_sha256": hashlib.sha256(payloads[r["image"]]).hexdigest(),
                "mask_path": r["mask"] or None,
                "mask_sha256": hashlib.sha256(payloads[r["mask"]]).hexdigest()
                if r["mask"]
                else None,
                "upstream_split": r["split"],
                "label": "good" if r["label"] == "normal" else "defect",
                "partition": partition,
            }
        )
        for r, partition in selected
    ]
    manifest = PhotoManifest(
        protocol_sha256=file_hash(protocol),
        csv_sha256=hashlib.sha256(metadata).hexdigest(),
        license_sha256=hashlib.sha256(license_text).hexdigest(),
        samples=samples,
    )
    validate_photos(manifest, output)
    evidence.mkdir(parents=True)
    (evidence / "source-split.csv").write_bytes(metadata)
    (evidence / "LICENSE-DATASET.txt").write_bytes(license_text)
    for directory in [output, evidence]:
        (directory / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n")
    return manifest
