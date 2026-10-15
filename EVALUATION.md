# Defect Lens evaluation design

Status: frozen evaluation tooling and metric/provenance tests implemented. Actual pretrained execution passed. The full measured fixture comparison is pending the shared ML lease; no owned-photo study has run. See [current evidence](docs/STATE.md).

## Baseline and split

Compare aligned-image differences with pretrained patch-feature anomaly scoring. Group by physical specimen and capture session; split groups before augmentation. Fit features on good training images, select thresholds on validation examples and evaluate the held-out set once per frozen candidate. Report performance on real captures separately from procedural fixtures.

## Measurements

Report image-level precision and recall, missed-defect rate, false-reject rate and the confusion matrix at the chosen threshold. Where pixel masks exist, report localisation overlap and pixel-level precision-recall. Show lighting and blur slices, sample counts, bootstrap intervals by specimen where sample size permits, warm and cold latency, throughput and peak memory. Reject rate is not a substitute for defect recall.

## End to end scenario

Start the application from a clean checkout. Submit a good image, a known defect and an ambiguous image. Check overlays and status, correct one decision, restart and retrieve the correction with its model revision. Submit a corrupt image and an oversized file; each must fail clearly without exhausting the worker. Interrupt processing and verify recovery without duplicate review entries.

## Release evidence

Save a split manifest, image provenance, model revision, configuration, environment and measured results. Publish a failure gallery using owned images. A synthetic-only result supports a fixture demonstration, not industrial accuracy. No numerical quality target has been measured or promised.
