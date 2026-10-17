# VisA candle photographic development diagnostics

**Development resubstitution, not held-out accuracy.** The same 24 development
images select thresholds and supply these metrics. Physical specimen/session
identities are unknown; no final evaluation or specimen bootstrap is claimed.
These are public photographs with author-provided labels, not owned captures.
No person reviewed the model outputs or supplied new labels for this study.

## What ran

The [frozen protocol](../../docs/PHOTO-PROTOCOL.md) selected 12 normal photographs
to fit both methods, followed by 12 different normal and 12 defective photographs
for development. The [manifest](manifest.json) records upstream partitions,
every image/mask hash and unknown physical identity. The source CSV contains
10,821 entries; only 36 photographs and 12 masks were acquired (4,226,496 payload
bytes, plus metadata/tar headers). Unselected image payloads were skipped.

Four candles, wax and varying placement are a different domain from the tabletop
plate. A standalone offline adapter resizes the full image to 256 square, without
plate registration, border suppression or product quality gates. Both methods
use the same geometry. The application and frozen procedural reports are unchanged.

| Development measure | Median difference | ResNet18 patch |
| --- | ---: | ---: |
| True positives / false positives / false negatives / true negatives | 12 / 0 / 0 / 12 | 12 / 1 / 0 / 11 |
| Precision / recall | 1.000 / 1.000 | 0.923 / 1.000 |
| False reject rate | 0.0% | 8.3% |
| Missed-defect rate | 0.0% | 0.0% |
| Defects receiving pass | 0/12 | 0/12 |
| Review band | 7/24 (29.2%) | 6/24 (25.0%) |
| Mean defect-mask IoU | 0.010465 | 0.176416 |
| Mean per-image defect pixel AP | 0.012651 | 0.294584 |
| Failed samples | 0 | 0 |
| Warm median / p95 | 6.03 / 6.50 ms | 19.50 / 21.82 ms |
| Cold build + first inference | 21.64 ms | 1607.94 ms |

The patch false reject is `candle/Data/Images/Normal/0025.JPG`. Review is the
development threshold band; this adapter does not apply the plate's blur or
framing heuristics. Binary errors use the high threshold, independently of
whether an example enters review. All 48 prediction rows are retained in the
[raw report](report.json).

## What the results mean

Image classification alone would conceal a serious weakness: the difference
method's localizations barely overlap the author masks, even after selecting
its pixel threshold on these development masks. The pretrained method localizes
more of the annotated pixels here but remains weak, and rejects one good image.
Neither result supports deployment or transfer to the product's plate domain.

IoU uses a threshold optimized on the same 12 development defect masks. Pixel AP
does not use that threshold. Both are averaged over defect images only, unlike
some upstream VisA summaries that include normal images. All 12 resized masks
retain positive pixels (64-291 each). Square resizing distorts geometry. Source
labels and masks were used as supplied; their truth was not independently
confirmed. These numbers are not directly comparable with full-dataset papers.

Source-image paths and hashes are disjoint across fit/development. They cannot
establish different physical specimens or sessions; related photographs may
cross partitions. The small, lexicographically selected development set and
same-set calibration further limit interpretation. Final specimen-separated
evaluation refuses to run until credible grouping provenance is available.

## Runtime and provenance

Apple M5 Pro, 24 GiB RAM, macOS 26.5.1, Python 3.12.14, NumPy 2.5.4, OpenCV 5.0.0,
torch 2.14.1 and torchvision 0.29.1. CPU only; torch 2 threads, BLAS environment
limits 1 and OpenCV sequential execution verified as 1 before both methods.
The GCD backend requires disabling parallelism with `setNumThreads(0)`;
positive thread requests were not honored in the observed build.

Cold timing includes model/reference construction and first scoring of a fit
image, excluding fit-image decoding. Three further fit-image warmups are excluded.
Warm timing includes each development image's decode, resize and scoring;
it excludes mask loading, metric calculation and report writing. There is no
API, artifact-storage or queue time in these measurements. The entire comparison
held the machine lease; its model child exited before release.

The raw report contains protocol, manifest, checkpoint, source/dependency hashes,
calibration and machine details. SHA256:
`21ce82658cd7927b9e551cfd524273e7eca4860ae9aecc99cbfcc18f0407aa50`.
The acquisition manifest's canonical source/selection identity is
`f17594529872d92bdec929cdd4179462d94d1c40ea222dc5e61d705204697c17`;
validation rejects any membership, label, partition, source or input-hash change.
New inputs or protocol changes require a separate revision. Output overwrite is
refused. The initial attempt failed during provenance serialization and produced
no report; only this corrected run supplies these measurements.

Independent automated review recalculated image calibration, decisions, confusion,
review counts and latency summaries, and checked source/asset hashes. Pixel-metric
aggregates match saved rows; heatmaps were not retained, so per-pixel values and
pixel-threshold optimization were not independently recalculated. No models were
rerun by the reviewer and no human annotation review is claimed.

## Reproduce locally

From a fresh checkout with the README dependencies installed:

```bash
uv sync --locked --extra features
uv run python scripts/acquire_photographs.py
uv run python -c 'from pathlib import Path; from defect_lens.inference.patch import download_weights; print(download_weights(Path(".runtime/models/weights")))'
uv run --extra features python scripts/evaluate_photographs.py --weights .runtime/models/weights/resnet18-f37072fd.pth
```

Downloads use official public sources and pinned terms/metadata. Selective tar
scanning can take about 15 minutes because it reads headers across the archive;
it does not download the 1.93 GB archive. Fresh acquisition writes source evidence
under `.runtime/visa-candle-source` and data under `.runtime/data/visa-candle`.
The new diagnostic output is `.runtime/visa-candle-dev-v1/report.json`. Existing
input/evidence/output directories are refused; select new CLI paths for repeat
runs. A busy machine lease refuses evaluation. `--final` explicitly exits 2.
No cloud keys, paid service, manual capture, labelling or output review is required.

## Attribution and terms

VisA: Yang Zou, Jongheon Jeong, Latha Pemula, Dongqing Zhang and Onkar Dabeer,
[*SPot-the-Difference Self-Supervised Pre-training for Anomaly Detection and
Segmentation*](https://arxiv.org/abs/2207.14315), 2022.
[Official source](https://github.com/amazon-science/spot-diff), revision
`2a692ab575001cbde74d402d897a7286086c6199`. The preserved
[dataset licence](LICENSE-DATASET.txt) is CC BY 4.0, separate from MIT code.
Images/masks are resized and binarized for measurement; source photographs and
weights remain local. See [third-party notices](../../THIRD-PARTY.md).
