# Defect Lens state

Updated: 2026-10-15. Implementation and final regression pass complete on `feat/defect-lens-v1`.
Working directory and Git root: `/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens`.

## Task ledger

| Task | State | Evidence |
| --- | --- | --- |
| 1. Bootstrap | Complete | Isolated uv/npm environments, exact locks, Python 3.12.14. Tested Node 26.7.0 exception; CI Node 24. |
| 2. Fixtures/decoder | Complete | 216 original images; repeatable 36 train / 90 validation / 90 test split; bounded PNG/JPEG decoding. |
| 3. Difference/calibration | Complete | Validation-only calibration, frozen source/data/artifact identity; actual good/defect/blur workflow. |
| 4. Pretrained/lease | Complete | Actual ResNet18 layer2 execution, verified public checkpoint, owned process exit before lease release. |
| 5. Durable workflow | Complete | Transactional admission/completion, quotas, worker time/RSS/restart limits, append-only corrections. |
| 6. API/batch | Complete | Real HTTP batch and API tests; bounded upload, replay, conflict, failure and generated-contract checks. |
| 7. Interface | Complete | Strict TypeScript, 8 UI tests and 5 actual-API browser tests; desktop/mobile, both palettes and keyboard flow. |
| 8. Evaluation | Complete | Two actual frozen methods, 90 held-out images each; curated report, raw rows, provenance and reviewed gallery. |
| 9. Capture gate | Complete as no-run gate | Validated capture schema/guide. No owned photographs supplied; no photo accuracy claim. |
| 10. Release verification | Final exact-source clone pending | Full local verification passed after review fixes; final clone will be recorded below. |

## Verification and reproduction

`uv run python scripts/verify.py --fixture-only` passed all 14 commands: Ruff, formatting, strict Pyright including tests/scripts, 62 Python unit/integration tests (one real-model test deselected), strict TypeScript including tests/configuration, 8 Vitest tests, production build, fixture/model preparation, 5 actual-API Playwright tests and 1 actual restart/interrupted-worker test. The latter saves a correction, restarts, retrieves it, and verifies unfinished work becomes INTERRUPTED without duplicate reviews. Oversized/corrupt inputs, process ownership and occupied-port refusal are covered. Logs: `.runtime/final-verification.log` and `.runtime/verification.json`.

`uv run pytest tests/integration/test_feature_prepare.py -m real_model -q` separately passed one actual pretrained test after final inference changes. It verifies shape, finite varied scores, full checkpoint hash and worker exit. Log: `.runtime/final-real-model.log`.

Final measured command:

```bash
uv run defect-lens benchmark --prepare --dataset .runtime/data/fixtures/manifest.json --difference-model .runtime/models/demo-difference --patch-model .runtime/models/demo-patch --output .runtime/outputs/fixture-evaluation
uv run defect-lens export-report --input .runtime/outputs/fixture-evaluation --output reports/fixture-v1
```

One token/identity-checked machine lease covered preparation, both model processes and the whole comparison. Child process groups exited before release. No threshold was tuned on held-out images. Hardware: Apple M5 Pro, 24 GiB, macOS 26.5.1 arm64, CPU; Python 3.12.14. Log: `.runtime/benchmark.log`.

## Measured evidence

Each method evaluated 36 good, 36 known-defect and 18 ambiguous test images. Both binary precision/recall were 1.0, with no false rejects or missed labelled defects; all ambiguous images required review. Difference required 21/90 reviews (23.3%), versus 54/90 (60.0%) for ResNet18 patch. Mean defect-mask IoU: 1.000 versus 0.213; pixel AP: 1.000 versus 0.293. Warm pipeline p95: 16.51 ms versus 32.29 ms. Cold load plus first inference: 12.67 ms versus 1199.84 ms. Peak combined benchmark process-tree RSS: 259.1 MiB versus 586.8 MiB. Separate API measurements use actual ASGI and supervised inference, include queueing, and exclude TCP.

- Difference revision: `c25f014f92c51762c4920972e91c21db1715444e2a969a78870f272a1ef40dee`.
- Patch revision: `8208eec4bf15e320df0f6e9ef2cd0a4ba13476bf032c3f0e743fa508dc149311`.
- Curated report: `reports/fixture-v1/report.json`; SHA256 `c51bb924255675f0be253e36506f69f0e23dc19550aa1402e3e07dea68b5ffaf`.
- Report Markdown, split manifest and environment accompany all 180 raw rows. All 36 gallery images were inspected; they illustrate ambiguous blur, since there were no labelled binary errors.

Procedural software evidence and actual pretrained execution are complete. Generated specimen groups are not independent photographed objects; these results support the local demonstration only. Owned-photo study: NOT RUN, no assets supplied. Screen reader: NOT TESTED. Arbitrary mirrored/rotated pose robustness: NOT CERTIFIED. No industrial deployment, customer impact or time saving is claimed.

## Review, scope and integration

One fresh reviewer found eight Important issues, no Critical or Minor findings. All eight were accepted and verified RED-to-GREEN in one fix pass; the complete suite passed afterward. No second review occurred. See `REVIEW.md` and the durable execution record for findings, decisions and costs. A path-escape reproduction initially wrote a test PNG under /tmp; its exact checksum was verified and only that probe removed. The regression now remains under this project's temporary directory.

The first clean clone exposed missing runtime-directory initialization (37 test setup errors); the explicit initialization fix passed a separate clone at 316770e. That check predates final review fixes, so a new exact-source clone is required.

All implementation and commits are local. No public repository, push, deployment, model upload, paid compute or external send occurred. No central registry/vault/parent/sibling record was modified. Integration owner: please record the verified outcome and remaining capture gate in the existing portfolio/operations record using its exact ID and current version; no record identity is assumed here. Keep this branch as-is for later publication approval.
