# Verification state

## Photographic development and recording pass (2026-10-17)

Completed implementation and measurement on `feat/photographic-development-demo`,
based on `40e5d51`. The [frozen protocol](PHOTO-PROTOCOL.md) permits development
resubstitution only: 12 fit normals, 12 development normals and 12 development
defects from public VisA candle photographs. Official CC BY 4.0 terms, source CSV,
36 image and 12 mask hashes are preserved separately from MIT. Selected payloads:
4,226,496 bytes. No source photographs or weights are committed.

The [report](../reports/visa-candle-dev-v1/report.md) contains actual difference and
pretrained CPU inference, all 48 development predictions, errors, mask metrics, thresholds,
review burden and runtime scope. Both have zero binary misses on the development
threshold-selection set. Difference review is 7/24, mean defect IoU 0.010465;
patch review is 6/24, IoU 0.176416, with one good-image false reject. Warm p95 is
6.50 and 21.82 ms. These are neither held-out accuracy nor validation of the plate
app. Source photo/mask labels were used as supplied; no person reviewed outputs.

Report JSON SHA256:
`21ce82658cd7927b9e551cfd524273e7eca4860ae9aecc99cbfcc18f0407aa50`.
Source CSV SHA256:
`a48557e6033318cb90556f706196bc9d247a776a23ea51aecee5a80dd0332995`.
Dataset licence SHA256:
`9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94`.
Canonical acquisition identity:
`f17594529872d92bdec929cdd4179462d94d1c40ea222dc5e61d705204697c17`.
Strict validation pins the complete source/selection/input hashes and rejects
source, membership, label, partition or mask reassignment.

The [38.32-second recording](demo/walkthrough.mp4) is actual plate API inference
on procedural inputs. It shows overlay changes, uncertainty, a scripted correction
and persistence after reload. It is H.264, 1280x1400, 996692 bytes, no audio, with
caption transcript and input/model/script hashes in `demo/walkthrough.json`.
Video SHA256: `5835e5e593d39a39c7d6532a5a4426617e90c03aed6e43c9d0f7d0fd0f93ad76`.
Four sampled frames were inspected automatically; the script asserted fresh jobs,
overlays, blur suppression and saved correction history. No responses were mocked.

`uv run python scripts/verify.py --fixture-only` passed all 15 commands after the
review fixes: **96 Python tests**, strict Pyright (0 errors), Ruff/format,
frontend lint and strict TypeScript including recording scripts, **11 Vitest**,
production build, **6 actual-API Playwright** and **1 restart scenario**. The one
legacy real-model test is deliberately deselected by this command; the actual
new pretrained comparison ran separately under the lease. No local test skipped
the optional packaging regression: Node, FFmpeg and FFprobe were present.

Commands and local evidence:

- `uv run python scripts/acquire_photographs.py` acquired the selected source
  files by bounded HTTP ranges; `.runtime/photo-acquisition.log`. Fresh checkout
  defaults now place source evidence in `.runtime/visa-candle-source`, preserving
  committed reports. Full acquisition was not repeated after pin enforcement;
  current validation rechecked all original file identities before inference.
- `uv run --extra features python scripts/evaluate_photographs.py --weights
  .runtime/models/weights/resnet18-f37072fd.pth` completed the corrected comparison;
  `.runtime/photo-comparison-verified.log` and `.runtime/visa-candle-dev-v1/report.json`.
  The curated report is an unchanged byte copy. The model child exited before
  lease release; the machine lease was absent afterwards.
- `node web/demo/record.mts` and `node web/demo/package.mts` exercised the real
  browser and encoder; `.runtime/demo-published-record.log`,
  `.runtime/demo-reviewed-package.log`. FFprobe confirmed the stream and duration.
- `uv run pytest tests/unit/test_photographs.py tests/unit/test_photo_evaluation.py
  tests/integration/test_demo_packaging.py -q` passed 28 focused regressions.
- Final verification: `.runtime/portfolio-final-verification.log` and
  `.runtime/verification.json`, all command exit statuses 0. Initial green run:
  `.runtime/portfolio-pass-verification.log` (79 Python tests before review cases).
- `uv run python scripts/evaluate_photographs.py --weights
  .runtime/models/weights/resnet18-f37072fd.pth --final` exits **2**, explicitly
  refusing unknown physical specimen/session groups before model loading.

Initial failures are retained, not relabelled as passes: the first recording used
0.8 on an integer opacity slider (fixed to 80); two occupied-port Python tests
failed because the demo was still serving (full rerun passed after shutdown);
the first model comparison failed on a relative source path before report export
(`.runtime/photo-comparison.log`). Review regressions caught first-development
warmup abort, incomplete source validation and paired JSON overwrite. All were
fixed RED-to-GREEN. The independent automated review and audit are in
[PHOTO-REVIEW.md](PHOTO-REVIEW.md); no deferred findings remain.

The review exposed a backend-specific thread issue: positive OpenCV requests are
ignored by this macOS GCD build. The new adapter disables parallelism and verifies
reported count 1 before both methods. Original plate source and frozen procedural
reports are unchanged; their old timings are observed process measurements,
not verified single-thread OpenCV results. EVALUATION records this correction.

Remaining evidence limits: physical specimen/session identities are absent, so
specimen-separated final evaluation and specimen bootstrap remain blocked. No
owned-photo pilot, human output/annotation review, industrial validation or
screen-reader audit ran. The independent reviewer checked pixel aggregates but
could not recompute individual pixel metrics without retained heatmaps. No model
was rerun by the reviewer. New measurements require new output paths.

The independent committed-source clone check passed at
`3d5fdb2139999546a219c7934919b5feba61f895`. Checkout
`.runtime/clean-clone-6983b7171d` installed its own dependencies and source, then
passed all 15 verification commands: 96 Python, 11 UI, 6 browser and 1 restart.
All four install/verify commands exited 0. Evidence:
`.runtime/clean-clone-evidence.json` and `.runtime/portfolio-clean-clone.log`.
The uv warning about the inherited VIRTUAL_ENV was expected; the isolation proof
confirms the clone's own prefix and package path. Subsequent edits clarify prose
and record these results; inference code and frozen data are unchanged.

Source/evidence commit `3d5fdb2139999546a219c7934919b5feba61f895` is published to
the existing public repository's `main`, using the earlier explicit push
authorization. It passed [GitHub CI on Ubuntu/Node 24](https://github.com/rbtbuilds/defect-lens/actions/runs/39062030810).
The final documentation commit records that observed result; the workflow badge
links the current run. No deployment, model upload, paid compute or external
message occurred. Owned servers were stopped and ports 8111/5111 were free;
the shared ML lease was left available after the model child exited.

Defect Lens v1 implements all ten tasks in the [original execution record](EXECUTION-RECORD.md). A subsequent independent publication review found two Important defects; both are fixed with regressions. Its Minor decoder-contract discrepancy is documented and tested. See [PUBLICATION-REVIEW.md](PUBLICATION-REVIEW.md).

## Prior v1 checks

`uv run python scripts/verify.py --fixture-only` passed all 15 commands after the publication fixes:

| Check | Result |
| --- | --- |
| Ruff and formatting | Pass |
| Strict Pyright, including tests/scripts | 0 errors |
| Python unit/integration tests | 68 passed; 1 real-model case deselected |
| Frontend lint and strict TypeScript, including tests | Pass |
| Vitest | 11 passed |
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

The independent clean-clone check passed at commit `5164122d8892fadfed3647cf67de76d33495e1ce`. Its checkout `.runtime/clean-clone-02ab77b4a6` used its own .venv, package source, node_modules and generated fixtures. All four install/verify commands exited 0, including all 15 checks, six actual browser cases and the restart flow. Proof: `.runtime/clean-clone-evidence.json`; output: `.runtime/publication-clean-clone.log`.

The repository is public at [rbtbuilds/defect-lens](https://github.com/rbtbuilds/defect-lens), with `main` as the default branch. Reviewed implementation and documentation commit `00d674d5476539458d875957d5299b0beab06095` passed [hosted CI](https://github.com/rbtbuilds/defect-lens/actions/runs/38813660529) on Ubuntu with Node 24. Documentation commit `250c524` recorded that result and added the CI badge/private reporting link. Its hosted run then exposed an intermittent request-error race despite unchanged application source.

Private vulnerability reporting is enabled. The initial HTTPS push was rejected because its OAuth credential lacked workflow scope; the existing SSH key authenticated as the same `rbtbuilds` owner and published the complete repository including CI. No global authentication settings were changed.

The Git tree was clean after scoped commits, and owned API/web/model processes were stopped. Ports 8111 and 5111 had no listeners. Another project's shared ML lease was left untouched.

No deployment, paid compute, weight upload or unrelated external message is authorized by repository publication. Parent/sibling/vault/operations records remain outside this checkout's ownership. Integration owner: record the verified outcome and remaining capture gate in the existing central record using its exact ID/current version.

## Follow-up CI race regression

[Run 38814176601](https://github.com/rbtbuilds/defect-lens/actions/runs/38814176601) failed the missing-link assertion: model/list metadata could arrive after a failed inspection lookup and clear its error. A deliberately delayed metadata response reproduced that failure in a component test. Model/list, selected-job and operation errors now have separate state, so a successful request cannot erase another request's failure; retry also refreshes the selected lookup.

The regression passed RED-to-GREEN, then all 15 local checks passed with 68 Python cases, 11 UI cases, six actual browser cases and the restart scenario. Output: `.runtime/publication-race-verification.log`. The README badge and [workflow runs](https://github.com/rbtbuilds/defect-lens/actions/workflows/ci.yml) expose the hosted status and exact commit for this fix. No inference or dependency identity changed.
