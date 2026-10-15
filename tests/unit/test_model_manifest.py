from pathlib import Path

import pytest

from defect_lens.models import ModelIntegrityError, load_model, prepare_model, resolve_model
from tests.support import make_dataset


def test_preparation_is_repeatable_and_detects_tampering(tmp_path: Path) -> None:
    make_dataset(tmp_path / "data")
    target = tmp_path / "model"
    one = prepare_model(tmp_path / "data/manifest.json", "difference", target)
    two = prepare_model(tmp_path / "data/manifest.json", "difference", target)
    assert one.revision == two.revision
    artifact = resolve_model(target) / "reference.npy"
    artifact.write_bytes(b"tampered")
    with pytest.raises(ModelIntegrityError):
        load_model(target)


def test_preparation_does_not_read_test_images(tmp_path: Path) -> None:
    manifest = make_dataset(tmp_path / "data")
    for sample in manifest.samples:
        if sample.split == "test":
            (tmp_path / "data" / sample.image_path).unlink()
            if sample.mask_path:
                (tmp_path / "data" / sample.mask_path).unlink()
    prepare_model(tmp_path / "data/manifest.json", "difference", tmp_path / "model")


def test_training_defect_is_rejected(tmp_path: Path) -> None:
    manifest = make_dataset(tmp_path / "data")
    manifest.samples[0].label = "defect"
    path = tmp_path / "data/manifest.json"
    path.write_text(manifest.model_dump_json())
    with pytest.raises(ValueError, match="good samples"):
        prepare_model(path, "difference", tmp_path / "model")


def test_changed_configuration_preserves_previous_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from defect_lens import models

    make_dataset(tmp_path / "data")
    target = tmp_path / "model"
    old = prepare_model(tmp_path / "data/manifest.json", "difference", target)
    previous = (resolve_model(target) / "manifest.json").read_bytes()
    monkeypatch.setattr(
        models, "INFERENCE_CONFIG", {**models.INFERENCE_CONFIG, "audit_revision": 2}
    )
    new = prepare_model(tmp_path / "data/manifest.json", "difference", target)
    assert new.revision != old.revision
    assert (target / "revisions" / old.revision / "manifest.json").read_bytes() == previous
