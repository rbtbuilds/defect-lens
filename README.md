# Defect Lens

A visual inspection application that flags unusual regions on a photographed object and lets an operator accept, reject or review the result. The initial task is one tabletop object type with visible surface damage or missing components.

Status: proposed project. This repository currently contains a brief and evaluation design; it has no runnable application or measured model results.

## What it demonstrates

Visual features, anomaly detection, localisation, threshold calibration, image processing and practical inference reliability. The workflow is derived from [Roboflow's FDE requirements](https://jobs.ashbyhq.com/roboflow/444ee288-cb72-4751-b16d-67c27749e901/), especially real-world image variation and operational handoff.

## First release

Upload an image, inspect a defect heatmap and see a pass, review or fail decision. Record an operator correction with the image and model version. Provide a local batch mode and show processing failures explicitly. Start from recorded images; add a webcam only after the same pipeline is verified.

Use an aligned-image difference method as a simple baseline, then compare a pretrained visual encoder with patch-level nearest-neighbour anomaly scoring. Calibration must use validation examples. An anomaly heatmap is evidence of unusual appearance, not proof of a particular defect cause. Any text explanation must be tied to observable regions.

## Proposed design

Image input -> size and quality validation -> normalisation and region selection -> versioned feature extractor -> patch anomaly scores -> calibrated decision -> review queue and audit record. Python owns inference and the API; a small web interface owns image overlays and review. Persist image references and review state locally. Queue jobs with bounded memory and expose model readiness separately from server health.

Use owned photographs and a procedural fixture set for the redistributable demo. Split capture sessions and physical specimens before making augmentations. The optional [MVTec AD benchmark](https://www.mvtec.com/research-teaching/datasets/mvtec-ad) has non-commercial data terms and must remain separate from the permissively licensed demo. Do not bundle its images or assets under the code licence.

## Acceptance criteria

A clean checkout eventually runs the sample without cloud keys. A held-out report compares methods and shows false rejects and missed defects. Interrupted or invalid inputs reach a clear failure state. The operator can correct a decision and retrieve its model version. Throughput and memory are reported for the actual Mac; no untested industrial hardware claim is permitted.

## Scope limits

One object type, file input and human review first. Industrial cameras, line controls, Jetson deployment and continuous retraining are later work. Human decisions are stored as feedback; they do not automatically become training labels or trigger model replacement.

## Next implementation decision

Validate a small owned capture set and the aligned-image baseline before choosing the feature encoder. Freeze the object definition and acceptable false-reject cost in the project specification. See [evaluation design](EVALUATION.md).

## Licence

Original code and documentation: [MIT](LICENSE). Third-party datasets, models and media retain their own terms.

## Implementation handoff

The v1 planning package fixes the tabletop object, runtime/API contracts, UI design and candidate ResNet18 patch baseline. Its evaluation compares candidates before any real-world quality claim; no implementation or measured result is implied by this plan.

- [Copyable fork prompt](CHAT-HANDOFF.md)
- [Project execution instructions](AGENTS.md)
- [Full v1 specification](docs/SPEC.md)
- [Ten-task native execution plan](docs/superpowers/plans/2026-10-15-v1.md)
- [Current state and evidence gates](docs/STATE.md)
- [Portfolio release standard](docs/RELEASE-STANDARD.md)

All generated application data and model artifacts belong under this project's ignored `.runtime` directory. The default procedural image-difference sample will run without cloud keys or pretrained downloads. Owned-photo capture evidence remains a separate pending requirement.
