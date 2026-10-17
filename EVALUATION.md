# Defect Lens evaluation design

Status: frozen procedural comparison completed; actual pretrained execution
verified. A separate [public-photo development study](reports/visa-candle-dev-v1/report.md)
has run with author-provided labels and masks. Its metrics are resubstitution,
not held-out accuracy; specimen-separated photographic final evaluation is blocked.
No owned-photo study has run. See the [procedural report](reports/fixture-v1/report.md),
[raw procedural provenance](reports/fixture-v1/report.json) and [verification state](docs/STATE.md).

## Baseline and split

Compare aligned-image differences with pretrained patch-feature anomaly scoring. Group by physical specimen and capture session; split groups before augmentation. Fit features on good training images, select thresholds on validation examples and evaluate the held-out set once per frozen candidate. Report performance on real captures separately from procedural fixtures.

## Measurements

Report image-level precision and recall, missed-defect rate, false-reject rate and the confusion matrix at the chosen threshold. Where pixel masks exist, report localisation overlap and pixel-level precision-recall. Show lighting and blur slices, sample counts, bootstrap intervals by specimen where sample size permits, warm and cold latency, throughput and peak memory. Reject rate is not a substitute for defect recall.

## End to end scenario

Start the application from a clean checkout. Submit a good image, a known defect and an ambiguous image. Check overlays and status, correct one decision, restart and retrieve the correction with its model revision. Submit a corrupt image and an oversized file; each must fail clearly without exhausting the worker. Interrupt processing and verify recovery without duplicate review entries.

## Release evidence

Save a split manifest, image provenance, model revision, configuration, environment and measured results. Publish a failure gallery using owned images. A synthetic-only result supports a fixture demonstration, not industrial accuracy. No numerical quality target has been measured or promised.

## Observed fixture results

Each method processed 90 held-out images: 36 good, 36 known defects, 18 ambiguous. Both had precision/recall 1.0, zero false rejects and zero missed labelled defects at the frozen high threshold. Operational review burden was 23.3% for difference and 60.0% for ResNet18 patch; all 18 ambiguous images were reviewed by each method. Mean defect-mask IoU was 1.000 versus 0.213. Warm pipeline p95 was 16.51 ms versus 32.29 ms on the observed Apple M5 Pro/24 GiB CPU setup. This includes decode/alignment/scoring/artifact storage; separate ASGI API measurements include queueing and exclude TCP. Peak combined benchmark process-tree RSS was 259.1 MiB versus 586.8 MiB.

The procedural geometry is deliberately simple and generated groups are not independently photographed specimens. These results are a reproducibility demonstration, not industrial accuracy. The report preserves all 180 prediction rows, stage timings, source/lock/model/data/config hashes and specimen-group bootstrap. Its 36 gallery images are reviewed original blur examples; there were no labelled binary misses/false rejects to illustrate.

Thread-policy correction (17 October 2026): the original procedural run requested
one OpenCV thread but did not verify that its backend honored the request. The
current macOS GCD build reports 15 after `setNumThreads(1)` and 1 after disabling
parallelism with `setNumThreads(0)`. Treat the old timings as measurements of that
original process, not confirmed single-thread OpenCV results. Frozen reports and
predictions remain unchanged. The new photographic run verifies sequential
OpenCV before both methods and records the observed count. This follows the
[backend-specific OpenCV constraint](https://docs.opencv.org/4.10.0/db/de0/group__core__utils.html).

## Public photographs

The [separate report](reports/visa-candle-dev-v1/report.md) uses 12 fit normals and
24 development photographs from VisA candle under CC BY 4.0. Source IDs are not
physical specimen IDs. The frozen protocol permits development resubstitution
only and refuses final evaluation. Both methods use a full-image adapter, not
the plate's registration/quality pipeline. Difference/patch review counts are
7/24 and 6/24; mean defect IoU is 0.010465 and 0.176416. Patch falsely rejects
one good image. Neither has binary misses on this threshold-selection set.

Source photographs, masks and weights stay local; licence, metadata, hashes,
predictions and measurements are curated separately. This is author-labelled
public-photo evidence, not an owned capture set, human output review or
industrial validation. Per-pixel measurements were not independently recomputed
by the reviewer because heatmaps are not retained; aggregate rows and source
provenance were independently checked. Reproduction requires the public assets.
