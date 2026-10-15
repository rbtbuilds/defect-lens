# Contributing

Keep Defect Lens scoped to one tabletop assembly, file input and human review. Read AGENTS.md, docs/SPEC.md and docs/STATE.md before work. Own only this repository; adjacent portfolio projects run concurrently.

Use Python 3.12, Node 24 (or a documented compatible local exception), uv.lock and web/package-lock.json. Install with `uv sync --locked --extra features` and `npm --prefix web ci`. Store generated files only in .runtime. Original source/docs are MIT; third-party weights/data retain their own terms.

Stop this project's servers, install Playwright Chromium and run `uv run python scripts/verify.py --fixture-only`. This runs Ruff, strict Pyright including tests/scripts, pytest, strict TypeScript including browser tests, Vitest, build and actual API browser/restart flows. Regenerate wire contracts with `uv run python scripts/export_contracts.py`; never hand-edit web/src/types.ts. Add meaningful failing tests before behavior changes and inspect the complete affected flow.

Feature tests and full benchmarks require the shared ML lease. Do not steal a busy lease or leave weights resident after releasing it. New code/lock/data identities require new prepared revisions. Preserve frozen reports; add a reviewed revision rather than rewriting measurements. Never call procedural results photographic evidence. Do not add private captures, weights, secrets or customer material to Git.

Local commits are safe for review. Publication, push, deployment, uploads, spending and external messages require Matthew's specific authorization.
