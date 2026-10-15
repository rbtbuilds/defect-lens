# Maintainer handoff

Defect Lens v1 implements a local tabletop inspection workflow with a difference baseline, an optional pretrained patch comparator and versioned human corrections.

Start with [README.md](README.md), [docs/STATE.md](docs/STATE.md) and [docs/REVIEW.md](docs/REVIEW.md). The specification is in [docs/SPEC.md](docs/SPEC.md), evaluation requirements in [EVALUATION.md](EVALUATION.md), and setup/recovery commands in [docs/RUNBOOK.md](docs/RUNBOOK.md). The original task history remains in [docs/EXECUTION-RECORD.md](docs/EXECUTION-RECORD.md).

## Resume safely

1. Verify the actual working directory, Git root, branch and status. Preserve any uncommitted work.
2. Read `AGENTS.md` and the documents relevant to the requested change. Check current evidence rather than restarting completed implementation tasks.
3. Inspect listeners on ports 8111 and 5111 before starting this checkout. Use its own dependencies, database and generated files.
4. Add regression coverage for behavior changes and run `uv run python scripts/verify.py --fixture-only`. A committed-source clone check is available in `scripts/clean_clone.py`.
5. Follow the shared machine lease for real-model work. Never steal a busy lease or leave a model process resident after release.

## Remaining evidence boundaries

The measured comparison uses original procedural images. Actual ResNet18 inference has run, but no owned-photo study or screen-reader audit has been performed. A photographic study must follow [docs/CAPTURE-GUIDE.md](docs/CAPTURE-GUIDE.md), preserve separate model revisions and produce a new frozen report. Do not describe the generated results as industrial validation.

The application remains local and single-operator. Camera integration, authentication, cloud hosting, automatic retraining and per-job cancellation require their own scoped design work.
