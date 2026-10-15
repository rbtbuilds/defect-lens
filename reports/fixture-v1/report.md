# Held-out procedural inspection report

Complete: True. Data mode: procedural. No industrial claim.

| Method | Precision | Recall | False reject | Missed defect | Review burden | Warm p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| difference | 1.0 | 1.0 | 0.0 | 0.0 | 0.23333333333333334 | 16.51 |
| resnet18_patch | 1.0 | 1.0 | 0.0 | 0.0 | 0.6 | 32.29 |

Binary fail threshold and operational pass/review/fail metrics are separate. Ambiguous frames are excluded from binary denominators and retained in review burden. Intervals resample procedural specimen groups, not independently photographed physical assemblies. Pixel AP is the mean per-image value over known defect masks.

Timing includes PNG decode, ECC alignment, actual scorer and PNG artifact storage, with three unmeasured warmups. API timings use actual ASGI requests and a supervised worker, including queue/storage and excluding TCP. Cold timing includes model loading and first inference; peak RSS samples the entire benchmark process tree every 10 ms.

The failure gallery includes uncertain blur examples even if all labelled defects are detected. These original procedural images support a software demonstration; no owned photographs have been validated.

See report.json for sample/model/lock/config hashes, thresholds, slice counts, specimen bootstrap, per-stage timing and all prediction rows.
