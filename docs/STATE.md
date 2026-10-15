# Defect Lens state

Updated: 2026-10-15. Implementation in progress on feat/defect-lens-v1.
Git root and working directory verified as /Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens.

## Task ledger

| Task | State | Evidence |
| --- | --- | --- |
| 1. Bootstrap | Complete | d6a1702; Python 3.12.14, Node 26.7.0 compatibility exception, isolated locks and dependencies. |
| 2. Fixtures/decoder | Complete | 91d0139; 216 original procedural samples, 36 good train, repeat generation matches. |
| 3. Difference/calibration | Complete | 19 tests pass; good/pass, missing/fail, blur/review in actual pipeline test. |
| 4. Pretrained/lease | Complete | 23 light tests and actual pretrained integration pass; 45 MiB checkpoint verified and local only. |
| 5. Durable workflow | Complete | 30 light tests pass; actual child inference, timeout/restart budget, memory monitor, atomic rollback and corrections. |
| 6. API/batch | Complete | Actual five-image HTTP batch: 5 succeeded,0 failed. Upload/replay/review/queue tests and generated contract checks pass. |
| 7. Interface | Complete | 7 Vitest tests, strict TypeScript/build and 5 actual API Playwright tests pass; desktop/mobile both palettes inspected. |
| 8. Evaluation | Next | Frozen measured comparison pending. |
| 9-10 | Pending | Capture gate and release checks remain. |

## Verification

Task 1: config/health RED to GREEN; strict Python and TypeScript and web build passed.
Task 2: manifests/decoder RED to GREEN; full suite 10 passed; CLI fixtures and fixtures-repeat each 216 samples; strict checks passed.
Task 3: missing implementation RED, then import-path correction (pytest pythonpath=['.']); full suite 19 passed, Ruff and strict Pyright passed. `uv run defect-lens prepare --method difference --dataset .runtime/data/fixtures/manifest.json --output .runtime/models/demo-difference` succeeded. Tests verify checksum tampering, no held-out image reads, repeated revision reuse and preservation after configuration identity change. Git provenance is outside revision identity.

## Decisions

Use the assigned isolated child repository directly. Node 24 unavailable locally; Vite engine >=22.12 supports installed Node 26.7.0, while CI targets 24. pytest temporary files stay under .runtime/pytest to avoid shared test-root cleanup. PreparedFrame retains the ECC transform to align validation masks consistently.

## Evidence gates

Procedural software workflow: in progress. Actual pretrained execution: passed real ResNet18 layer2 shape, finite varied scores and full checkpoint hash checks. Comparison remains pending. Owned-photo evaluation: not run; no capture set supplied. Screen reader: not tested. No publishing, push, deployment, paid compute or external sends authorized.

## Next action

Task 8: frozen procedural evaluation and measured comparison.

Task 7: `npm --prefix web run typecheck`, `test -- --run` (7 tests), `build` and `test:e2e` (5 tests) passed. Actual browser uploads good/missing/blur, adjusts overlay with keyboard, saves correction and retrieves after reload. Selected-job reselection bug reproduced RED then fixed GREEN. Browser checks 390px/1280px light/dark, keyboard correction/theme and reduced motion, no horizontal overflow and muted-text contrast >=4.5. Screenshots .runtime/screenshots reviewed for alignment/spacing/detail. Chromium installed by Playwright locally; screen-reader testing not performed.

Task 6: focused HTTP tests passed (upload/replay/stale revision/origin, chunked and image caps, two-upload gate, 33rd job, review conflicts), generated OpenAPI/TypeScript consistency checked; strict Pyright/Ruff pass. Real server API8111 batch command submitted5/succeeded5/failed0, JSONL at .runtime/outputs/batch-task6.jsonl. Normalized duplicate/rejected artifacts are cleaned; originals never stored beyond request. Body bytes are capped before multipart parsing, whose bounded memory spool cannot spill into shared temporary storage.

Task 5: `uv run --extra features pytest -m "not real_model" -q` ->30 passed,1 deselected; strict Pyright and Ruff pass. Spawned real difference worker completes exactly one inspection; timeout kills/join, one restart then degraded; 1 MiB test ceiling exercises RSS recovery. Competing admission respects one-slot capacity; a simulated post-artifact/pre-commit crash rolls back and startup marks INTERRUPTED. Correction replay/version conflict and reopen persistence pass. Server lock refuses a second owner. No feature worker remains resident.

Task 4 exact checks: `uv run --extra features pytest -m "not real_model" -q` (23 passed), `uv run --extra features pytest tests/integration/test_feature_prepare.py -m real_model -q` (1 passed), strict Pyright and Ruff passed. Feature prepare succeeded under the shared lease; the child exited before token-checked release. Weight origin/checksum is in MODEL-CARD and model manifest. No owned photographs were used. Narrow local torchvision signature stubs cover its untyped public entry points; no missing-import exclusion.
