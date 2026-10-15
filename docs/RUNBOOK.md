# Local runbook

Run every command from this repository's Git root. Python is 3.12 via uv; CI uses Node 24. This Mac uses Node 26.7.0, tested against Vite's >=22.12 engine requirement because no Node 24 manager was available. Dependencies are local and locked. Numeric limits apply within these processes before library imports: BLAS/OpenCV threads 1; the CPU feature encoder uses torch threads 2. No global runtime changes or cloud keys are needed.

```bash
uv sync --locked --extra features
npm --prefix web ci
uv run defect-lens fixtures --output .runtime/data/fixtures --seed 20261015
uv run defect-lens prepare --method difference --dataset .runtime/data/fixtures/manifest.json --output .runtime/models/demo-difference
uv run python scripts/dev.py start --model .runtime/models/demo-difference
```

Open http://127.0.0.1:5111 . Choose an original image from .runtime/data/fixtures. A good, missing-fastener, surface-mark and ambiguous blur view are included for every held-out specimen/session. Model output is an appearance comparison in a controlled setup. It does not diagnose a damage cause.

API8111 and web5111 bind to loopback. The helper refuses occupied ports; inspect their owner with `lsof -nP -iTCP:8111 -iTCP:5111 -sTCP:LISTEN`. Do not stop another project's process or select another port. The API also uses an OS file lock under its own .runtime to refuse a second server.

```bash
uv run python scripts/dev.py status
uv run python scripts/dev.py stop
```

The helper records owned PIDs, random tokens and process-start identities in .runtime/dev-processes.json and writes separate local logs. Stop checks every identity before signalling. A changed identity is an error, never permission to kill a reused PID. The API drains a running job for up to five seconds, then stops/joins its child. Queued work for the selected revision stays queued; unfinished running work becomes failed INTERRUPTED, never automatically retried. Once a different verified model becomes ready, incompatible queued jobs become failed MODEL_CHANGED, retaining their original revision/input. This prevents a permanently full queue without processing an image under the wrong model. Deliberately choose the image and submit again for a new request key. No per-job cancellation endpoint exists.

## Models and the machine lease

The default difference method works offline while another project holds the ML lease. Feature serving never silently switches methods or data modes. Stop this project's server before heavy preparation or a full comparison.

```bash
uv run --extra features defect-lens prepare --method resnet18_patch --dataset .runtime/data/fixtures/manifest.json --output .runtime/models/demo-patch
uv run --extra features pytest tests/integration/test_feature_prepare.py -m real_model -q
```

Preparation alone downloads the explicit public ResNet18 IMAGENET1K_V1 checkpoint to ignored project-local storage. It checks the upstream checksum prefix, records the full SHA256 and loads with weights_only=True. Serving requires local verified files and never downloads. See MODEL-CARD for upstream terms.

Heavy work atomically mkdir /tmp/bentolabs-portfolio-ml.lock and writes project, PID, process-start identity, UTC time, purpose and a random token. Busy acquisition exits 3, without spinning or loading weights. Read owner.json and inspect its named PID/start identity if investigating stale ownership. Never remove another owner's lock, and never assume a reused PID proves ownership. Recovery of a stale lock requires an explicit operator decision after process inspection. Normal owners stop/join model children before releasing only their matching token. A benchmark holds one lease across both methods and every model/API child; it does not leave resident weights behind.

A feature server with a busy lease still serves health/history but remains unready. Explicitly restart when resources are available. Missing/invalid artifacts are unprepared; worker loading is loading; a ready handshake is ready; a crash/timeout/RSS failure consumes one restart, after which readiness is degraded until application restart. `/healthz` checks database health independently. Source or lock changes require preparation of a new model revision. CURRENT.json is resolved once by the worker; existing results retain their original revision.

## Bounds and storage

At most two uploads and 32 queued/running jobs are admitted. The body cap is 9 MiB before multipart parsing; one PNG/JPEG image is capped at 8 MiB, 128-4096 pixels per side and 8 million pixels. Animation, undecodable pixel data and unsupported formats fail explicitly. The decoder normalizes pixels rather than certifying container structure; some PNGs with missing trailing metadata remain decodable. Filenames are never paths. Original request bytes are removed; normalized images and bounded PNG artifacts remain local.

A job has 30 seconds after dispatch, monitored every 100 ms, with a 1,536 MiB worker RSS ceiling. Admission reserves 1 MiB per job, limits total retained bytes to 512 MiB and jobs to 10,000. Completion cannot exceed its reservation. STORAGE_LIMIT is a quota error, not a cleanup request. There is no automatic retention deletion. Back up or archive deliberately before deciding what to remove. Orphan artifact folders from a crash remain available for inspection and count toward retained storage when the running job is recovered; never run broad cleanup commands.

SQLite uses WAL, foreign keys, a 5-second busy timeout and versioned transactions. Stop this project before copying .runtime for a backup; include the database, any WAL/SHM files and its referenced inputs/artifacts together. Restore only to this checkout after stopping its processes. Model revisions are immutable and checksummed; do not edit their contents or repoint CURRENT during a running worker.

## Batch, evidence and checks

Batch accepts at most 100 manifest rows with paths contained in the manifest directory. It uses the actual API sequentially with a 60-second per-item deadline, logs failures in JSONL and exits 4 when any item fails. POST retries preserve their original idempotency key; the CLI does not silently resubmit failed jobs.

```bash
uv run defect-lens batch --manifest .runtime/data/batch/manifest.json --api http://127.0.0.1:8111 --output .runtime/outputs/batch.jsonl
uv run --extra features defect-lens benchmark --prepare --dataset .runtime/data/fixtures/manifest.json --difference-model .runtime/models/demo-difference --patch-model .runtime/models/demo-patch --output .runtime/outputs/fixture-evaluation
uv run defect-lens export-report --input .runtime/outputs/fixture-evaluation --output reports/fixture-v1
```

The --prepare benchmark option refreshes selected models and compares them under one lease, avoiding a release/reacquire gap. Model runner process groups contain only their own descendants; interrupted runners stop them before release, and a cleanup failure retains the lease for manual inspection. Choose new output directories for a new benchmark/curated revision. Never overwrite frozen evidence. An API timing failure preserves the pipeline rows, records an unavailable reason and makes the aggregate report incomplete; the benchmark exits unsuccessfully. Reports include actual failures, thresholds, source/model/lock/data hashes, hardware, cold/warm and stage timings, process-tree RSS and separate operational metrics. API timing uses actual ASGI requests and a child worker, excluding TCP. Pretrained execution on procedural inputs is not owned-photo validation. Follow CAPTURE-GUIDE for a separate photographic study.

With both owned servers stopped:

```bash
npm --prefix web exec -- playwright install chromium
uv run python scripts/verify.py --fixture-only
uv run python scripts/clean_clone.py
```

The clean clone requires committed, clean source; it stays under this project's .runtime, installs independent frozen dependencies and runs checks plus browser/restart flow on the same reserved ports. It never pushes or contacts GitHub. Package/browser installation may need public network; the running difference demonstration needs no network or model download. Evidence JSON files and full logs stay local. Screen-reader verification is separate and has not been performed.
