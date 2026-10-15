from datetime import datetime
from pathlib import Path

from defect_lens.contracts import Contract, DatasetManifest
from defect_lens.manifests import ManifestError, validate_manifest


class CaptureIssue(Contract):
    code: str
    sample_id: str | None = None
    message: str


class CaptureValidation(Contract):
    valid: bool
    counts: dict[str, int]
    issues: list[CaptureIssue]
    rights_complete: bool
    pilot_counts_met: bool


def validate_captures(manifest: DatasetManifest, root: Path) -> CaptureValidation:
    issues: list[CaptureIssue] = []
    if manifest.mode != "owned_capture" or manifest.generator_revision is not None:
        issues.append(
            CaptureIssue(
                code="FIXTURE_SOURCE",
                message="Owned capture manifests cannot retain a procedural generator identity",
            )
        )
    try:
        validate_manifest(manifest, root)
    except (OSError, ManifestError):
        issues.append(
            CaptureIssue(
                code="MANIFEST_INVALID",
                message="Check hashes, relative paths, unique IDs and exclusive specimen/session groups",
            )
        )
    anchor = next(
        iter(sorted(s.id for s in manifest.samples if s.split == "train" and s.label == "good")),
        None,
    )
    rights = True
    for sample in manifest.samples:

        def add(code: str, message: str, sample_id: str = sample.id) -> None:
            issues.append(CaptureIssue(code=code, sample_id=sample_id, message=message))

        if sample.source != "owned_photo" or "procedural" in sample.rights_note.lower():
            add("FIXTURE_SOURCE", "Procedural images cannot be relabelled as owned photographs")
        if not sample.rights_note.strip():
            rights = False
            add("RIGHTS_MISSING", "Record explicit ownership/permission; do not infer rights")
        try:
            if sample.captured_at is None:
                raise ValueError("Missing capture time")
            stamp = datetime.fromisoformat(sample.captured_at)
            if stamp.tzinfo is None:
                raise ValueError("Timezone required")
        except ValueError:
            add("CAPTURE_TIME_INVALID", "Record an actual timezone-aware capture timestamp")
        review = sample.capture_review
        if review is None or not review.physical_specimen_confirmed:
            add("REVIEW_MISSING", "Human reviewer must confirm specimen identity and setup")
        else:
            expected = {
                "none": "good",
                "missing_fastener": "missing_fastener",
                "surface_mark": "staged_surface_mark",
                "quality": "quality",
            }[sample.defect_kind]
            if review.annotation != expected:
                add(
                    "ANNOTATION_INVALID",
                    "Use observed good/missing_fastener/staged_surface_mark/quality; do not infer damage causes",
                )
            if sample.mask_path and (
                review.mask_transform is None
                or (
                    review.mask_coordinate_frame == "aligned"
                    and review.mask_anchor_sample_id != anchor
                )
            ):
                add(
                    "MASK_FRAME_INVALID",
                    "Record mask transform and the selected training anchor for aligned masks",
                )
        if (sample.defect_kind == "quality" and sample.label != "ambiguous") or (
            sample.label == "ambiguous" and sample.defect_kind != "quality"
        ):
            add("AMBIGUOUS_LABEL", "Quality uncertainty is not a known defect label")
        if sample.split == "train" and sample.label != "good":
            add("TRAINING_LABEL", "Training manifest must contain good images only")
    counts = {
        f"{split}_specimens": len({s.specimen_id for s in manifest.samples if s.split == split})
        for split in ["train", "validation", "test"]
    }
    counts.update(
        {
            f"{split}_sessions": len({s.session_id for s in manifest.samples if s.split == split})
            for split in ["train", "validation", "test"]
        }
    )
    counts["samples"] = len(manifest.samples)
    return CaptureValidation(
        valid=not issues,
        counts=counts,
        issues=issues,
        rights_complete=rights,
        pilot_counts_met=all(
            counts[f"{split}_specimens"] >= 3 and counts[f"{split}_sessions"] >= 3
            for split in ["train", "validation", "test"]
        ),
    )
