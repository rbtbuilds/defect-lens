# VisA candle development protocol, v1

Frozen before image acquisition on 2026-10-17. This is a domain-shift diagnostic,
not a specimen-separated final evaluation or an owned-photo pilot.

## Source and eligibility

Official source: [Amazon Science spot-diff](https://github.com/amazon-science/spot-diff),
revision `2a692ab575001cbde74d402d897a7286086c6199`; `split_csv/1cls.csv`
and `LICENSE-DATASET`. Dataset: VisA, Zou et al., *SPot-the-Difference
Self-Supervised Pre-training for Anomaly Detection and Segmentation* (2022).
Archive: https://amazon-visual-anomaly.s3.us-west-2.amazonaws.com/VisA_20220922.tar
Terms: CC BY 4.0, independently preserved under reports/visa-candle-dev-v1.
Code remains MIT. No third-party photographs or weights are committed.

The candle category has photographs and author-provided pixel masks. Its
multiple objects and varying placement violate the fixed plate/jig assumption.
Use a standalone offline full-image adapter, with no plate registration, central
crop or quality gates. Square resizing is a declared geometric distortion.

## Selection and separation

Sort official CSV candle paths lexicographically. First 12 upstream train/normal
images fit both methods. Next 12 upstream train/normal images and first 12
upstream test/anomaly images form development. Preserve upstream split names;
our development anomalies consume a small portion of the upstream test split.
No source image or identical file hash may cross our partitions. No augmentation.
Reserve all other upstream images; do not acquire a final set in this pass.

**Physical specimen and session IDs are unknown.** Image paths are source IDs,
never physical specimen assertions. No specimen bootstrap or independence claim.
A future confirmatory protocol must obtain author-supported object/session
grouping, assign all views of each physical object and session to one partition,
then hash-freeze train/development/final membership before fitting or tuning.
Without that provenance, the final-evaluation command must refuse to run.
No Matthew photographs, labels or output review are required for this study.

## Frozen methods and measurement

Both use 256 x 256 RGB full-image resizing (bilinear), masks nearest-neighbor
and positive values as defect. Normal masks are all zero. Baseline: median good
reference, bounded median brightness correction +/-20, channel-mean absolute
difference /255, Gaussian 3 x 3 smoothing. Pretrained: existing CPU ResNet18
ImageNet checkpoint, layer2 normalized 128-vector features on 32 x 32 grid;
4096-vector seeded reservoir over good fit images, no optimization/fine-tuning.
Upsample nearest-patch distance to 256 square with bilinear interpolation.
Image score: mean of largest ceil(1% * 65536) heatmap values for both methods.

Development-only thresholds use existing loss 5*miss + false reject, ties to
larger high threshold, low=min(normal p90,0.9*high). Pixel threshold maximizes
mean development defect IoU over 33 evenly spaced candidates. Fix seed 20261017.
No tuning after these diagnostics. Report **development resubstitution**, since
the same labelled development set supplies thresholds and metrics. Never present
these numbers as held-out accuracy. Keep original procedural reports unchanged.

Report all 24 development rows for both methods, failures retained, confusion,
precision/recall, missed defects, false rejects, review burden, defect false pass,
mean defect IoU and mean per-image pixel AP. Undefined values are JSON null.
Runtime: cold construction + first image, 3 excluded warmups, per-image warm
decode/resize/scoring and total latency; exclude mask loading/metrics/disk report
writing. CPU only, torch2/OpenCV1 threads. Hold the shared ML lease for the
complete comparison; child exits before release. Record environment, source,
dependency, checkpoint, protocol and input/mask hashes. Any sample failure marks
the report incomplete. Refuse output overwrite; new measurements need a new path.

No physical-specimen confirmation, human output review, industrial validation,
product-domain accuracy, or supervised model training is claimed. Distinct image
hashes cannot establish distinct underlying physical objects.
