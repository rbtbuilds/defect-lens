# Contributing

Defect Lens is a local inspection app for one tabletop assembly. Please read the [specification](docs/SPEC.md) before extending the supported object, input method or deployment model. Bug reports should include the command or browser steps, expected behavior, actual behavior and a minimal original or procedural input. Keep private photographs, aliases, notes and logs out of public issues.

## Development setup

Use Python 3.12 through uv and Node 24. Dependencies are resolved in `uv.lock` and `web/package-lock.json`; installs belong to this checkout.

```bash
uv sync --locked --extra features
npm --prefix web ci
npm --prefix web exec -- playwright install chromium
uv run python scripts/verify.py --fixture-only
```

Stop this project's servers before verification. It checks Python and TypeScript strictly, including test files, and exercises the actual API/browser and restart flow. Keep meaningful regression tests with behavior fixes. Source files use ASCII punctuation.

API wire types are generated from the Python contracts:

```bash
uv run python scripts/export_contracts.py
```

Commit both exported contracts when they change. Do not hand-edit `web/src/types.ts`.

## Model and evaluation changes

Use `.runtime/` for generated data, model files and local results. Keep held-out images out of preparation and calibration. Human corrections do not become training labels automatically. Changed source, dependency or data identities require new prepared model revisions.

Feature inference and complete benchmarks acquire the machine lease described in the [runbook](docs/RUNBOOK.md). A busy lease must cause a readable refusal; never delete another process's lease or leave a model resident after release. Lightweight fixture checks can run without it.

Preserve frozen reports and their provenance. A new measurement belongs in a separate report directory with its own configuration and input hashes. Distinguish generated images, actual pretrained execution and reviewed photographs in every result. Do not commit weights, credentials, private captures or customer material.

## Pull requests

Explain the concrete problem, the resulting behavior and how you verified it. Include a screenshot for a visible interface change. Update the runbook or model card when a change affects setup, operation or supported inputs. Original contributions use the repository's MIT licence; identify any separate third-party terms.
