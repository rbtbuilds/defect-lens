# Defect Lens fork handoff

The plan is ready for a separate implementation chat. Copy the block below into the fork. It authorizes local execution; it does not authorize publishing or paid resources. The inherited app panel may still show the resume repository, so the first directory check is mandatory.

```text
Implement Defect Lens v1 using native superpowers:executing-plans in this chat.

The ONLY project directory you own is:
/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens

Before any write, set every shell tool workdir explicitly to that directory, run pwd, and read:
/Users/matthewgoralczyk/BentoLabs/portfolio/AGENTS.md
/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens/AGENTS.md
/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens/CHAT-HANDOFF.md
/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens/README.md
/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens/docs/SPEC.md
/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens/EVALUATION.md
/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens/docs/superpowers/plans/2026-10-15-v1.md
/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens/docs/RELEASE-STANDARD.md
/Users/matthewgoralczyk/BentoLabs/portfolio/defect-lens/docs/STATE.md

Inspect the actual file tree, Git root/status, selected runtimes and listeners on ports 8111/5111. Do not assume the planning state still matches reality. No repository existed at planning time; if still absent, Task 1 may initialize Git ONLY in this child, on feat/defect-lens-v1. If Git resolves to another directory, stop before writes and report it. Do not commit through the inherited resume app panel, change global config, or edit siblings/parent/vault/registries. All five project chats may run concurrently.

Read and use the installed superpowers:executing-plans skill. Execute the ten tasks natively, test each gate, inspect your diff, and keep docs/STATE.md current. No automatic multiagent cascade or repeated product discovery: the object definition, architecture, algorithms, API, UI and evidence policy are settled in SPEC. If new evidence invalidates a choice, explain the concrete issue and adjust the smallest dependent part. Use the available frontend-design skill before UI implementation.

Use Python 3.12 through uv and Node 24 LTS, isolated .venv and web/node_modules, exact resolved lockfiles, SQLite and all generated state under this project's .runtime. Bind API 127.0.0.1:8111 and web 127.0.0.1:5111 with strictPort; exact CORS origin http://127.0.0.1:5111. An occupied port requires owner inspection, not an automatic kill or new port.

Before any pretrained weight load, feature inference, heavy preparation or full benchmark, atomically acquire /tmp/bentolabs-portfolio-ml.lock with mkdir and record project/PID/UTC/purpose/token/process-start identity. If busy, continue light tasks and record pending evidence. Stop and join the model child before releasing only your own lease. Keep the lease for the whole benchmark; do not leave a resident model or silently switch models/fixtures.

Complete the offline difference-based procedural demo, real API/UI/recovery flow, strict Python and TypeScript tests including test sources, browser verification and clean-clone runbook. Compare the actual ResNet18 patch baseline only when the lease and verified local weights permit it. No owned capture set is assumed available: finish independent work and state the missing real-photo evidence without inventing measurements. Keep fixture results, actual pretrained execution and real captures labelled separately. Preserve correction history and original model revision.

Local reversible development, dependency installation, tests and scoped local commits are authorized. Public repositories, pushes, deployment, releases, model uploads, paid compute and external messages need specific authorization. Stop only the task that requires missing assets/hardware/authorization; continue independent tasks. Do not create automations. Stop owned processes at finish, verify final evidence, and report completed scope, exact checks/skips, report paths and remaining capture limitations. The first word of every reply must be Matthew.
```

Execution starts at Task 1 unless inspection and STATE prove later work already exists. The plan's final commands run from this child, with a separately owned clean-clone workdir only inside .runtime. The source documents are portable inside a standalone clone; application behavior never depends on a sibling repository.
