# Repository guidance

## Scope

Verify the working directory and Git root before editing. Work only in the assigned checkout, preserve unrelated changes and keep generated state under `.runtime/`. This repository has no dependency on an adjacent project or a parent workspace package.

Read `docs/SPEC.md` for supported behavior, `EVALUATION.md` for measurement rules and `docs/STATE.md` for verified outcomes. Do not treat a document's existence as proof that its checks passed.

## Development

Use Python 3.12 through uv, Node 24 and the committed dependency locks. Do not replace global runtimes. Local compatibility exceptions belong in the verification record.

The API binds to `127.0.0.1:8111` and the web app to `127.0.0.1:5111`, with strict port selection and the exact browser origin. Inspect an occupied port's owner; never stop an unknown process or silently change ports. Use `scripts/dev.py` for owned-process startup and shutdown.

Read affected code, callers and tests before changes. Keep fixes scoped, add meaningful regression coverage and verify the complete affected flow. Source and documentation use ASCII punctuation. UI changes preserve both themes, keyboard operation, responsive layouts and reduced-motion behavior.

## Checks

```bash
uv sync --locked --extra features
npm --prefix web ci
npm --prefix web exec -- playwright install chromium
uv run python scripts/verify.py --fixture-only
```

Run strict Python and TypeScript checks including test files. Browser tests use the actual local API. Do not substitute mocked inference for measured model results. Regenerate API contracts with `scripts/export_contracts.py`; keep the exported OpenAPI and TypeScript types consistent.

## Models and evidence

Before pretrained loading/inference or a complete benchmark, acquire the machine lease at `/tmp/bentolabs-portfolio-ml.lock` through the existing lease implementation. A busy lease means refusal, not automatic recovery. Stop and join owned model children before releasing the matching token/identity. See `docs/RUNBOOK.md` for the protocol.

Keep procedural fixtures, actual pretrained execution and reviewed photographs distinct. Calibration uses validation images only. Preserve frozen report contents and provenance; new measurements use a separate report directory. Human corrections never become automatic training labels. Inference source, dependency or preparation-data changes require a new model revision.

Do not commit private captures, weights, credentials, logs or customer material. Original code/docs/procedural images are MIT licensed; third-party assets keep their own terms. Publication, deployment, paid resources and external messages require the user's authorization. Stop owned processes and report exact checks, failures and skipped evidence when finishing.
