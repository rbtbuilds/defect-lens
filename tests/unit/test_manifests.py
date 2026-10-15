from pathlib import Path

import pytest

from defect_lens.fixtures import generate_fixtures
from defect_lens.manifests import ManifestError, load_manifest, validate_manifest


def test_manifest_rejects_overlap_and_changed_file(tmp_path: Path) -> None:
    manifest = generate_fixtures(tmp_path, seed=17, specimens_per_split=1)
    shared = manifest.samples[0].specimen_id
    index = next(i for i, s in enumerate(manifest.samples) if s.split == "test")
    altered = manifest.model_copy(deep=True)
    altered.samples[index].specimen_id = shared
    with pytest.raises(ManifestError, match="specimen overlap"):
        validate_manifest(altered, tmp_path)
    (tmp_path / manifest.samples[0].image_path).write_bytes(b"changed")
    with pytest.raises(ManifestError, match="checksum"):
        load_manifest(tmp_path / "manifest.json")


def test_manifest_refuses_path_escape(tmp_path: Path) -> None:
    manifest = generate_fixtures(tmp_path, seed=1, specimens_per_split=1)
    manifest.samples[0].image_path = "../outside.png"
    with pytest.raises(ManifestError, match="path"):
        validate_manifest(manifest, tmp_path)
