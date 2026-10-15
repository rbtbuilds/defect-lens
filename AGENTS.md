# Defect Lens execution instructions

## Entry and scope

Own only `/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens` in the current multi-chat workspace. Before edits read this file, `../AGENTS.md`, `CHAT-HANDOFF.md`, `README.md`, `docs/SPEC.md`, `EVALUATION.md`, `docs/superpowers/plans/2026-10-15-v1.md`, `docs/RELEASE-STANDARD.md` and `docs/STATE.md`; inspect actual files and Git state. A standalone checkout uses the mirrored rules here and its local documents; it has no sibling service or parent-package dependency.

Set every shell tool's workdir explicitly to this child and prove it with pwd. A fork may retain the resume workspace in the app. Do not commit through an unrelated app panel. Never initialize Git in the parent; if this child has no repository, Task 1 may run git init -b feat/defect-lens-v1 here. If Git resolves outside this directory, stop before writes. Never replace uncommitted work or change global Git configuration.

Do not edit siblings, parent coordination files, the resume workspace, vault, registry, archive or machine settings. Other chats are active. Report an integration-owner update request when verified work requires a central operations record; preserve unknown commitments. No monitors or scheduled automations.

## Execution discipline

The v1 implementation is authorized and tracked in docs/STATE.md. Resume from that state and Git evidence; do not restart completed tasks. Use native superpowers:executing-plans, work task by task, and update STATE with exact commands/outcomes. Do not repeat discovery for settled product choices or automatically delegate a chain of agents. Read the files/callers/tests being changed before editing. Keep source and prose ASCII.

The first word of every user-facing reply is Matthew. Before the first tool call say what will happen in one sentence. Report measured outcomes, skipped checks and remaining evidence precisely; a file's existence is not a passing test.

Local reversible development, tests and scoped local commits are authorized by the execution prompt. Public GitHub repository creation, pushes, release publishing, deployment, paid compute, model uploads and external messages require specific authorization. Inspect before deletion or overwrite of pre-existing material. Do not install product dependencies or run models during the planning pass.

## Runtime isolation

Python 3.12.x through uv, requires-python >=3.12,<3.13. Python 3.12.14 was found during planning; the shell default 3.14.7 is not selected. Node 24 LTS through an existing supported manager; shell Node 26.7.0 requires a documented compatibility check if used as a local exception, while CI remains Node 24. Pin actual resolved versions in uv.lock and web/package-lock.json. No global runtime replacement.

Own .venv and web/node_modules. All generated database, images, model artifacts, logs, PIDs and outputs live under this repository's .runtime. Curated original reports are explicitly tracked under reports/. Do not share mutable dependencies or use sibling APIs.

Reserve API 127.0.0.1:8111 and web 127.0.0.1:5111. Vite strictPort is required; CORS is exactly http://127.0.0.1:5111. Inspect an occupied port's owner; do not change ports or stop unknown processes. The full workspace also reserves 8112-8115, 5112-5115 and 8212/8312/8412 for other chats.

## Machine lease

The machine has an M5 Pro and 24 GiB memory. Edits/light tests may run concurrently; pretrained model load/inference, heavy preparation and full benchmarks run one at a time. Acquire before loading weights with atomic mkdir `/tmp/bentolabs-portfolio-ml.lock`. Write owner.json containing project defect-lens, supervisor PID, UTC start, purpose, random token and process-start identity. mkdir failure means busy: return model_busy / exit 3 and continue light work. Never spin, steal or auto-delete the lease.

Keep the lease for the full model-child lifetime and for an entire comparison benchmark. Stop/join/unload the worker before releasing only the token-matching owned lease in finally/shutdown. No resident model may survive lease release. Stale recovery requires inspecting owner and actual process identity; reused PID is not proof. Default image-difference mode may remain usable while the lease is busy; feature mode reports unready and never silently switches models.

## Product and verification boundaries

One tabletop plate/card with four dark fasteners; inspect missing fastener or unexpected surface mark. Original procedural fixtures are the offline sample. No real photographs are assumed present. A synthetic demonstration, actual pretrained execution and owned capture validation are distinct evidence states. Human corrections are append-only feedback, not automatic training labels. There is no per-job cancel API; interrupt/recovery tests stop owned processes and check resulting durable states.

Read the available frontend-design skill before UI implementation. Implement both palettes, typography, spacing, responsive behavior, keyboard operation and reduced motion from SPEC; finish with alignment/spacing/detail review. Do not claim screen-reader testing unless performed.

Install full check environments with uv sync --locked --extra features so optional feature imports typecheck without global packages; this downloads no weights and runs no model. Run Ruff, strict Pyright covering src/tests/scripts, pytest, strict TypeScript covering source/unit/browser tests and configs, Vitest, production build and Playwright against the actual API. Test clean clone, correction persistence across restart, invalid/oversized images, interrupted jobs, deduplication and owned-process shutdown. Record skipped real-model/capture checks with precise reasons; do not substitute a stub. Preserve actual environment, model/data/config hashes, sample counts and report provenance. MIT applies to original code/docs, not third-party weights/data.
