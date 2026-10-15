# Publication review

A separate AI reviewer with a fresh context inspected implementation commit `5496979` before the public push. The review covered backend consistency and resource limits, inference and evaluation, browser state, documentation and the published evidence. It found two Important defects and one Minor contract discrepancy, with no Critical finding.

The reviewer reproduced both defects independently. The implementer then added failing regressions, made the fixes and ran the release checks. The reviewer did not re-review the remediation; the evidence below comes from the regression and full-workflow runs.

## Findings and resolution

| Finding | Resolution | Coverage |
| --- | --- | --- |
| A failed API timing subprocess prevented aggregate report export, even when pipeline rows had been saved | Retain pipeline outcomes, record the unavailable API measurement and mark the aggregate comparison incomplete | Actual ASGI runs with one/all corrupt test images; API-only subprocess failure; saved report and lease-release assertions |
| Reloading a link to a job outside the newest 30 selected a different inspection | Restore the URL job independently of pagination, retain it in the queue and show a missing-job error without selecting another record | Reproduced failing component tests; actual browser run creates 31 newer jobs and verifies linked reload and missing-link behavior |
| Documentation promised rejection of every truncated PNG, although Pillow can decode pixels with missing trailing metadata | Narrow the contract to format/dimension checks and pixel decoding; document recoverable trailing PNG structure | Tests pin identical normalized pixels after removing IEND or the final checksum plus IEND; no decoder behavior changed |

## Verification

The final local command `uv run python scripts/verify.py --fixture-only` passed all 15 steps: Ruff, formatting, strict Pyright including tests/scripts, 68 Python unit/integration cases, frontend lint, strict TypeScript, 11 Vitest cases, the production build, fixture/model preparation, six actual-API browser cases and an actual interrupted-worker/restart case. One real-model test was explicitly deselected.

The minimum-dependency README setup was exercised with torch/torchvision absent; its five existing browser scenarios passed. A fresh screenshot shows an actual missing-fastener overlay and saved correction. Relative Markdown links were checked. A targeted scan of 265 historical blobs found no matching credential patterns or forbidden generated/model paths; it was not a comprehensive secret-scanner certification.

The reviewer recalculated metrics from all 180 published prediction rows and checked both frozen inference-source hashes against the implementation. No inference or dependency identity changed in this publication pass. The existing report remains frozen.

Full output stays local in `.runtime/publication-verification.log`, `.runtime/publication-eval-red.log`, `.runtime/publication-ui-red.log` and `.runtime/publication-browser-green.log`. The independent clone passed on implementation commit 5164122; [hosted Ubuntu/Node 24 CI](https://github.com/rbtbuilds/defect-lens/actions/runs/38813660529) passed on commit 00d674d5476539458d875957d5299b0beab06095. Full provenance is recorded in [STATE.md](STATE.md).

## Review boundaries

- Photographic accuracy and industrial suitability remain unvalidated because no owned capture study or deployment evidence exists.
- Screen-reader testing remains unperformed.
- Remote hosting, authentication and protection against a hostile local filesystem remain outside the local single-operator trust boundary.
- The reviewer did not rerun full strict checks, pretrained inference, the clean clone or hosted CI. The parent ran the release checks. Pretrained execution was previously verified against the unchanged inference implementation; a fresh model run was not attempted while another project held the shared lease.
- The independent verdict covered the pre-remediation commit. Subsequent changes are supported by the recorded regression and workflow results, without claiming another independent sign-off.

No findings were deferred: the two behavioral defects were fixed, and the decoder discrepancy was addressed through an explicit, tested contract clarification.

## Follow-up from hosted CI

A subsequent hosted run caught an intermittent missing-link error disappearing after a later successful model/list request. This was outside the original independent verdict. A controlled response-order test reproduced it, then passed after request errors were separated by owner. The complete local workflow passed again with 11 UI cases. [STATE.md](STATE.md) links the failing run, the regression evidence and current hosted checks. The fix does not increase test timeouts or retry failed assertions.
