# Photographic development study and recorded walkthrough

Specification: the autonomous portfolio pass requested on 17 October 2026;
retain the v1 product contract in docs/SPEC.md. Execute natively with
superpowers:executing-plans. No manual contributions or approval checkpoints.

## Evidence decision

Use the official VisA archive, metadata and CC BY 4.0 dataset terms pinned to
amazon-science/spot-diff revision 2a692ab575001cbde74d402d897a7286086c6199.
The candle domain is photographic and has author-provided defect masks. Its
variable object arrangements do not satisfy the plate alignment contract.
A standalone adapter resizes the full image to 256 square, without plate ECC,
border suppression or plate quality heuristics. It never feeds the application
or represents public images as owned captures.

Physical object and acquisition-session identifiers are absent from the
published split CSV. The confirmatory specimen-separated evaluation is blocked.
Run development diagnostics only, with source-image disjointness, a small fixed
selection, no tuning rounds and explicit unknown physical independence. This
costs a final photographic accuracy claim; it avoids inventing provenance.
Freeze docs/PHOTO-PROTOCOL.md before downloading image payloads or fitting.

## Task 1: Frozen protocol and bounded acquisition

Create the protocol, separate typed photo records, selective HTTP-range tar
reader and acquisition script. Preserve source CSV/licence bytes and hashes.
Download only 12 source-training normal images for fit, the next 12 source-
training normals for development, and 12 source-test anomalies for development.
Choose lexicographic paths before viewing pixels. No final split is opened.
Test traversal, byte caps/range semantics, missing members, tampering, overlap
and false specimen assertions. Expected: focused tests pass; source manifest
records all 36 images and 12 masks with hashes and upstream splits.

## Task 2: Separate photographic diagnostic adapter

Compare a median-reference RGB difference baseline and actual frozen ResNet18
layer2 nearest patch bank (4096 vectors, seed 20261017), full-image coordinates.
Both use top 1% heatmap score. Calibrate/report on development only, prominently
resubstitution metrics. Pixel IoU threshold from development masks; pixel AP
threshold independent. Record errors, binary confusion, operational review,
false passes, segmentation, cold/warm CPU timing and provenance. Fail closed
on final evaluation, identity or hash errors; retain individual runtime errors.
Acquire the shared lease for the complete comparison and run models in a child
that exits before release. Expected: strict checks and focused regressions pass;
immutable new report with predictions and no modification to fixture-v1.

## Task 3: Automated browser recording

Add a reproducible Playwright walkthrough of actual API inference: generated
defect, heatmap control, blurred/review input, correction and persisted history.
Record a captioned MP4 with an explicit procedural-input/actual-inference label;
the automated correction is not human review. Use existing product UI unchanged.
Expected: recording assertions pass, ffprobe validates output, sampled frames
are inspected and a small curated video plus provenance is committed.

## Task 4: Recruiter documentation and verification

Update README, EVALUATION, case study, walkthrough, handoff and STATE with concise
findings, honest scope and exact reproduction commands. Run all 15 verification
commands, strict checks including new scripts/tests, and actual API/browser flow.
Fresh-context judgment reviewer checks the complete change after implementation.
Fix important findings with regressions, review final diff and commit scoped work.
Publication to the existing GitHub repository is already explicitly authorized;
use SSH only after verification. No deployment, paid resources, model uploads,
manual tasks, external messages, sibling or registry edits.

## Review focus

Check source ownership claims, missing physical IDs, fit/development leakage
language, unsafe archive paths/ranges, mask coordinates, failed-sample retention,
lease lifetime, report immutability, and actual rather than mocked demo inference.
