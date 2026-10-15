import hashlib
from pathlib import Path

from defect_lens.contracts import DatasetManifest


class ManifestError(ValueError):
    pass


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contained(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ManifestError("invalid dataset path")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ManifestError("escaping dataset path")
    return resolved


def validate_groups(manifest: DatasetManifest) -> None:
    ids: set[str] = set()
    groups: dict[str, str] = {}
    sessions: dict[str, str] = {}
    for sample in manifest.samples:
        if sample.id in ids:
            raise ManifestError("duplicate sample ID")
        ids.add(sample.id)
        for label, key, seen in [
            ("specimen", sample.specimen_id, groups),
            ("session", sample.session_id, sessions),
        ]:
            if key in seen and seen[key] != sample.split:
                raise ManifestError(f"{label} overlap")
            seen[key] = sample.split


def validate_manifest(manifest: DatasetManifest, root: Path) -> None:
    validate_groups(manifest)
    for sample in manifest.samples:
        for relative, expected in [
            (sample.image_path, sample.image_sha256),
            (sample.mask_path, sample.mask_sha256),
        ]:
            if relative is None:
                if expected is not None:
                    raise ManifestError("mask checksum without path")
                continue
            path = contained(root, relative)
            if not path.is_file() or file_hash(path) != expected:
                raise ManifestError(f"checksum mismatch: {sample.id}")


def load_manifest(path: Path) -> DatasetManifest:
    manifest = DatasetManifest.model_validate_json(path.read_bytes())
    validate_manifest(manifest, path.parent)
    return manifest
