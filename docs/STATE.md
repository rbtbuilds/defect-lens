# Verification state

Defect Lens v1 implements all ten tasks in the [original execution record](EXECUTION-RECORD.md). A subsequent independent publication review found two Important defects; both are fixed with regressions. Its Minor decoder-contract discrepancy is documented and tested. See [PUBLICATION-REVIEW.md](PUBLICATION-REVIEW.md).

## Current checks

`uv run python scripts/verify.py --fixture-only` passed all 15 commands after the publication fixes:

| Check | Result |
| --- | --- |
| Ruff and formatting | Pass |
| Strict Pyright, including tests/scripts | 0 errors |
| Python unit/integration tests | 68 passed; 1 real-model case deselected |
| Frontend lint and strict TypeScript, including tests | Pass |
| Vitest | 10 passed |
| Production build | Pass |
| Actual-API Playwright workflow | 6 passed |
| Actual interrupted-worker/restart flow | 1 passed |

The browser run covers good/defective/blurred input, overlays, corrections, reload, both themes at mobile/desktop widths, keyboard controls and reduced motion. A pagination regression creates 31 newer jobs and verifies that reloading an older linked inspection preserves its identity. Missing links show an error. Restart verification preserves corrections and marks unfinished work `INTERRUPTED` without duplicate reviews.

The README setup also passed with torch/torchvision absent, using the default difference method. Python: 3.12.14. Local Node: 26.7.0, a tested exception because Node 24 was unavailable. CI targets Ubuntu/Node 24. Browser: Chromium 156.0.8078.4, Playwright revision 1248.

Local evidence: `.runtime/publication-verification.log`, `.runtime/verification.json`, `.runtime/publication-quickstart-browser.log` and the regression logs named in the publication review.

## Model evidence

The frozen procedural comparison evaluates 90 held-out images per method: 36 good, 36 known defects and 18 ambiguous. Both methods have binary precision/recall 1.0, with no false rejects or missed labelled defects. Difference requires 21/90 reviews (23.3%), versus 54/90 (60.0%) for ResNet18 patch. Mean defect-mask intersection over union is 1.000 versus 0.213; warm pipeline p95 is 16.51 ms versus 32.29 ms.

The [report](../reports/fixture-v1/report.md) preserves all 180 rows, split/configuration/model hashes, timings, memory measurements and original procedural gallery images. The publication reviewer independently recalculated its metrics and checked the source identities. Report JSON SHA256: `c51bb924255675f0be253e36506f69f0e23dc19550aa1402e3e07dea68b5ffaf`.

- Difference revision: `c25f014f92c51762c4920972e91c21db1715444e2a969a78870f272a1ef40dee`.
- Patch revision: `8208eec4bf15e320df0f6e9ef2cd0a4ba13476bf032c3f0e743fa508dc149311`.
- Actual pretrained execution: previously passed one dedicated integration test against the unchanged inference implementation. A fresh run was not attempted during publication preparation while another project owned the machine lease.
- Owned-photo study: not run; no capture set supplied. Follow [CAPTURE-GUIDE.md](CAPTURE-GUIDE.md) for a separate study.
- Screen-reader testing: not performed. Arbitrary mirrored/rotated poses: not certified.

No industrial accuracy, customer impact or time saving is claimed. The decoder normalizes decodable pixels and does not certify complete PNG container structure.

## Publication gates

The authenticated GitHub owner is `rbtbuilds`; `defect-lens` was available when checked. The independent clean-clone gate and remote publication/CI are the remaining steps of the authorized publication pass. Their exact commit/run evidence will be added after execution.

No deployment, paid compute, weight upload or unrelated external message is authorized by repository publication. Parent/sibling/vault/operations records remain outside this checkout's ownership. Integration owner: record the verified outcome and remaining capture gate in the existing central record using its exact ID/current version.
