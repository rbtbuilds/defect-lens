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
| 6. API/batch | Next | HTTP workflow pending. |
| 7-10 | Pending | UI, evaluation and release checks remain. |

## Verification

Task 1: config/health RED to GREEN; strict Python and TypeScript and web build passed.
Task 2: manifests/decoder RED to GREEN; full suite 10 passed; CLI fixtures and fixtures-repeat each 216 samples; strict checks passed.
Task 3: missing implementation RED, then import-path correction (pytest pythonpath=['.']); full suite 19 passed, Ruff and strict Pyright passed. `uv run defect-lens prepare --method difference --dataset .runtime/data/fixtures/manifest.json --output .runtime/models/demo-difference` succeeded. Tests verify checksum tampering, no held-out image reads, repeated revision reuse and preservation after configuration identity change. Git provenance is outside revision identity.

## Decisions

Use the assigned isolated child repository directly. Node 24 unavailable locally; Vite engine >=22.12 supports installed Node 26.7.0, while CI targets 24. pytest temporary files stay under .runtime/pytest to avoid shared test-root cleanup. PreparedFrame retains the ECC transform to align validation masks consistently.

## Evidence gates

Procedural software workflow: in progress. Actual pretrained execution: passed real ResNet18 layer2 shape, finite varied scores and full checkpoint hash checks. Comparison remains pending. Owned-photo evaluation: not run; no capture set supplied. Screen reader: not tested. No publishing, push, deployment, paid compute or external sends authorized.

## Next action

Task 6: bounded HTTP upload, polling, artifacts, review and batch.

Task 5: `uv run --extra features pytest -m "not real_model" -q` ->30 passed,1 deselected; strict Pyright and Ruff pass. Spawned real difference worker completes exactly one inspection; timeout kills/join, one restart then degraded; 1 MiB test ceiling exercises RSS recovery. Competing admission respects one-slot capacity; a simulated post-artifact/pre-commit crash rolls back and startup marks INTERRUPTED. Correction replay/version conflict and reopen persistence pass. Server lock refuses a second owner. No feature worker remains resident.

Task 4 exact checks: `uv run --extra features pytest -m "not real_model" -q` (23 passed), `uv run --extra features pytest tests/integration/test_feature_prepare.py -m real_model -q` (1 passed), strict Pyright and Ruff passed. Feature prepare succeeded under the shared lease; the child exited before token-checked release. Weight origin/checksum is in MODEL-CARD and model manifest. No owned photographs were used. Narrow local torchvision signature stubs cover its untyped public entry points; no missing-import exclusion.
