from pathlib import Path

from defect_lens.captures import validate_captures
from defect_lens.contracts import CaptureReview, DatasetManifest
from tests.support import make_dataset


def capture_schema(root: Path) -> DatasetManifest:
    data = make_dataset(root)
    data.mode = "owned_capture"
    data.generator_revision = None
    for sample in data.samples:
        sample.source = "owned_photo"
        sample.rights_note = (
            "Synthetic schema test only; creator permission declaration is simulated"
        )
        sample.captured_at = "2026-10-15T10:00:00Z"
        sample.capture_review = CaptureReview(
            reviewer_alias="test",
            physical_specimen_confirmed=True,
            annotation={
                "none": "good",
                "surface_mark": "staged_surface_mark",
                "missing_fastener": "missing_fastener",
                "quality": "quality",
            }[sample.defect_kind],
            setup_notes="Synthetic validation exercise, no owned photos",
            distance_cm=40,
            mask_transform=[1, 0, 0, 0, 1, 0] if sample.mask_path else None,
        )
    return data


def test_capture_rights_and_provenance_required(tmp_path: Path) -> None:
    data = capture_schema(tmp_path)
    assert validate_captures(data, tmp_path).valid
    data.samples[0].rights_note = ""
    result = validate_captures(data, tmp_path)
    assert not result.valid and not result.rights_complete
    assert "RIGHTS_MISSING" in {issue.code for issue in result.issues}
    data.samples[0].image_sha256 = "0" * 64
    assert "MANIFEST_INVALID" in {issue.code for issue in validate_captures(data, tmp_path).issues}


def test_overlap_fixture_and_cause_claims_rejected(tmp_path: Path) -> None:
    data = capture_schema(tmp_path)
    item = next(s for s in data.samples if s.split == "test")
    item.specimen_id = data.samples[0].specimen_id
    item.session_id = data.samples[0].session_id
    assert not validate_captures(data, tmp_path).valid
    session_data = capture_schema(tmp_path / "session")
    next(s for s in session_data.samples if s.split == "test").session_id = session_data.samples[
        0
    ].session_id
    assert not validate_captures(session_data, tmp_path / "session").valid
    data = make_dataset(tmp_path / "fixture")
    data.mode = "owned_capture"
    assert "FIXTURE_SOURCE" in {
        issue.code for issue in validate_captures(data, tmp_path / "fixture").issues
    }
    data = capture_schema(tmp_path / "cause")
    mark = next(s for s in data.samples if s.defect_kind == "surface_mark")
    assert mark.capture_review is not None
    mark.capture_review.annotation = "crack"
    assert "ANNOTATION_INVALID" in {
        issue.code for issue in validate_captures(data, tmp_path / "cause").issues
    }
    quality = next(s for s in data.samples if s.label == "ambiguous")
    quality.label = "defect"
    assert "AMBIGUOUS_LABEL" in {
        issue.code for issue in validate_captures(data, tmp_path / "cause").issues
    }


def test_capture_label_and_kind_must_agree(tmp_path: Path) -> None:
    data = capture_schema(tmp_path)
    missing = next(s for s in data.samples if s.defect_kind == "missing_fastener")
    missing.label = "good"
    result = validate_captures(data, tmp_path)
    assert not result.valid
    assert "LABEL_KIND_CONFLICT" in {issue.code for issue in result.issues}
    missing.label = "defect"
    good = next(s for s in data.samples if s.split == "validation" and s.defect_kind == "none")
    good.label = "defect"
    assert not validate_captures(data, tmp_path).valid
