# Defect Lens evaluation design

Status: measured frozen comparison completed on original procedural inputs; actual pretrained execution verified. No owned-photo study has run. See the [report](reports/fixture-v1/report.md), [raw predictions and provenance](reports/fixture-v1/report.json) and [verification state](docs/STATE.md).

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
