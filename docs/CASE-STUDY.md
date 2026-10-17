# Engineering case study

## The workflow

An operator compares a tabletop assembly with a known-good example, checks for a missing fastener or an unexpected mark, then records the decision. Defect Lens exposes that comparison: the aligned image, anomaly overlay, score and human correction stay tied to the model revision that produced them.

The application is a portfolio simulation. There is no customer pilot or measured time saving.

## Why two methods

The first method aligns the plate edges using enhanced correlation coefficient (ECC) registration, corrects bounded brightness differences and compares the image with a median good reference. It is inexpensive and its spatial output is easy to inspect.

The second uses actual ResNet18 IMAGENET1K_V1 layer2 features. It compares unit-normalized patch vectors with a seeded bank of up to 4,096 vectors from good training images. Both methods use the same 256-square geometry and CPU execution path.

The [frozen comparison](../reports/fixture-v1/report.md) evaluated 90 held-out images per method. Both detected all 36 labelled defects with no false rejects on 36 good images. Difference required 21/90 reviews (23.3%); the feature method required 54/90 (60.0%), including every good image. Mean defect-mask intersection over union was 1.000 versus 0.213, and warm pipeline latency at the 95th percentile was 16.51 ms versus 32.29 ms.

That result supports keeping difference as the default for this simple geometry. The pretrained comparator adds a useful reference point, but its wider review band creates more work for the operator in this test.

## Reproducibility and its limits

The generator produces 216 original procedural images: 36 good training views, 90 validation views and 90 held-out views. Specimen/session groups are assigned before rendering. Only validation chooses decision thresholds, localization thresholds and the heatmap scale.

Each model revision includes source, dependency, configuration, artifact and training/validation hashes. The report preserves all test outcomes, including failures, and marks a run with sample errors incomplete. Binary metrics use successfully evaluated labelled images; the failure count remains explicit.

Generated groups are not independently photographed assemblies. Their bootstrap intervals describe this generated set; they do not establish variation across real objects. No owned-photo study has run. The [capture guide](CAPTURE-GUIDE.md) defines a separate study with distinct physical assemblies, exclusive sessions, explicit rights and reviewed truth masks.

## Adding photographic evidence without changing the claim

The next evidence step uses a small, predefined VisA candle subset with the
authors' image labels and masks. Its CC BY 4.0 data terms permit attributed
reuse and are preserved separately from the MIT application code. Source
photographs and weights remain local.

Candles are a different inspection problem: multiple objects, varying placement
and no plate jig. A standalone adapter therefore scores the entire resized
photograph. Reusing the plate registration or border crop would discard relevant
pixels and make its quality gates inappropriate. Both the median-reference
baseline and actual ResNet18 features use that same full-frame geometry.

The important restriction is statistical. Published source paths identify
images, not independently confirmed physical specimens or acquisition sessions.
The [photo protocol](PHOTO-PROTOCOL.md) freezes selection and methods before
fitting, and refuses final evaluation without those groups. Development
diagnostics calibrate and measure on the same development images, so their
numbers are resubstitution results. They can reveal failure behavior; they do
not estimate performance on unseen physical objects. No person reviewed the
outputs or supplied new annotations for this pass.

The [measured diagnostic](../reports/visa-candle-dev-v1/report.md) illustrates why
that restraint matters. Difference had no binary errors after development
threshold selection, yet mean defect-mask overlap was only 0.010. Pretrained
patches reached 0.176 overlap and falsely rejected one of 12 good images. Neither
is a strong localization result. Looking only at image-level accuracy would hide
the weakness. Both preserve every prediction and error count; the report includes
runtime scope, source/weight hashes and the known independence limitation.

## Uncertain inputs

A blurred image can have a large appearance difference even when no fastener is missing. The quality gate sends it to review and suppresses the score/heatmap, rather than inviting an operator to interpret blur as localized damage. Those images appear in the report's gallery.

Corrections are append-only and retain the original result. An operator note does not automatically become training truth.

## Recovery and consistency

SQLite transactions protect bounded admission, job completion and versioned corrections. Retries retain their request identity. A supervised inference child has a time limit, a memory ceiling and one restart budget. A running job interrupted by shutdown becomes explicitly `INTERRUPTED`; incompatible queued jobs retain their original input/revision and fail as `MODEL_CHANGED` after a different verified model becomes ready.

The restart test saves a correction, interrupts a blocked worker, restarts the actual API and retrieves the correction without duplicate review entries. Browser tests exercise good, defective and blurred inputs, overlay controls, keyboard correction and reload at mobile/desktop widths in both themes.

One browser regression exposed a late response replacing the inspection the user had just selected. A reordered-promise test now verifies that a refresh updates only the currently displayed inspection. Process tests also cover child exit before lease release and refusal to stop a process whose recorded identity no longer matches.
