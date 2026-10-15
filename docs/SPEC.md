# Defect Lens v1 specification

Status: approved planning scope for implementation when Matthew pastes CHAT-HANDOFF.md. Code, tests, weights and measured results do not exist yet. Read EVALUATION.md alongside this specification; its evidence requirements remain in force.

## Product and claim

Build a local visual inspection workbench for one object type: a matte gray square tabletop plate/card with four dark circular fasteners, one near each corner. Inspect a missing fastener or an unexpected surface mark. A fixed overhead view, neutral background and placement jig keep the plate inside the central 192 x 192 pixels of a 256 x 256 normalized frame. The application says where appearance differs; it does not diagnose damage causes.

The procedural demonstration uses original generated images of this assembly. An owned-photo pilot uses actual physical assemblies of the same definition, photographed with permission. No owned capture set is assumed to exist. A marker line or tape used in a capture is labelled a staged surface mark, not a real crack. Real photographs, procedural fixtures and pretrained-weight execution are separate evidence dimensions.

The operator uploads a PNG/JPEG, follows a queued job, views the aligned image and heatmap, reads a pass/review/fail decision with model revision, and records a correction. A queue exposes processing failures. A local batch command uses the same API. File input only; webcam, industrial controls, authentication, cloud hosting and automatic retraining are outside v1.

## Acceptance contract

| ID | Observable requirement | Owning tasks |
| --- | --- | --- |
| A1 | Clean checkout runs deterministic sample without cloud keys or model downloads. | 1, 2, 3, 6, 7, 10 |
| A2 | Both methods share preprocessing, produce versioned scores and spatial overlays, and calibrate only on validation. | 3, 4, 8 |
| A3 | Bad files, bounded queue, timeout, memory ceiling and interrupted work have explicit states. | 2, 5, 6, 10 |
| A4 | A correction survives restart with original decision and model revision. | 5, 6, 7, 10 |
| A5 | Measured held-out report includes misses, false rejects, review burden, localisation where labels exist, and actual Mac resource data. | 8, 9 |
| A6 | Fixture evidence is labelled; absent owned photographs leave the real-photo claim pending. | 2, 8, 9, 10 |
| A7 | Both themes, keyboard operation, small screens, readable failure states and reduced motion work. | 7, 10 |
| A8 | Ports, isolated dependencies, machine lease, clean clone and owned-process shutdown are verified. | 1, 4, 5, 10 |

Software is fixture-complete after A1-A4 and A6-A8 pass. The feature comparison needs actual pretrained execution. A real-photo demonstration additionally needs the capture evidence in Task 9. Do not mark A5 real-photo complete from synthetic examples. No numerical accuracy, latency or memory outcome is promised.

## Runtime and bounds

- Python 3.12.x through uv; requires-python >=3.12,<3.13. Python 3.12.14 was found on this machine during planning. Do not select the shell's Python 3.14.7.
- Node 24 LTS through an existing version manager. The shell currently reports Node 26.7.0; record a verified local compatibility exception only if Node 24 is unavailable, while CI remains Node 24. Never change global runtimes.
- FastAPI, Pydantic, SQLite, Pillow, NumPy and OpenCV headless; optional torch/torchvision extra for pretrained features. React, TypeScript and Vite in web. Resolve compatible actual dependency versions at bootstrap and commit uv.lock and web/package-lock.json; do not copy speculative version numbers.
- API binds 127.0.0.1:8111; web binds 127.0.0.1:5111 with strictPort. Allow CORS only http://127.0.0.1:5111. An occupied port is an error requiring owner inspection, never automatic termination or port drift.
- One API instance, one inference child process, one job at a time, at most 32 queued/running jobs combined. Two simultaneous uploads maximum; excess requests receive 429. No tensors/images in the work queue, only UUID job IDs.
- Upload body maximum 9 MiB including multipart overhead; image part maximum 8 MiB. Limit one image per request; allow decoded PNG/JPEG only, 128-4096 pixels on each side, at most 8,000,000 pixels. Reject animated images, corrupt/truncated files and decompression bombs. Ignore client filenames as paths.
- Read upload chunks of 64 KiB into a task-owned temporary file. Enforce the body cap before multipart parsing, independent of Content-Length. Inspect Pillow dimensions before decoding; EXIF transpose once, convert RGB, strip metadata, contain-fit and pad to 256 x 256. Persist this normalized image and raw-file SHA256. Raw uploads are removed after processing; real evaluation originals stay in the separate local capture set.
- Image aspect ratio outside 0.9-1.1 is a successful review result with reason framing, not a claimed pass. Detect blur using Laplacian variance below 20 on uint8 normalized luminance and clipping when more than 25% of ROI pixels are <=5 or >=250. These are explicit demo heuristics stored in the model manifest, not calibrated industrial quality limits.
- Job deadline 30 seconds after dispatch; worker RSS ceiling 1,536 MiB sampled every 100 ms. Kill only the registered child after exceeding either limit. Store TIMEOUT or MEMORY_LIMIT and recover worker. One automatic worker restart after a crash/limit per API lifetime; further failures set readiness degraded until operator restart.
- Stored normalized inputs/artifacts total <=512 MiB and <=10,000 jobs; reject new work with 507 STORAGE_LIMIT before admission when the reservation cannot fit. Reserve 1 MiB per accepted job and reconcile actual artifact sizes on completion. Artifacts larger than that reservation fail STORAGE_LIMIT before promotion; no completion may overrun the quota. List endpoints limit 1-100 with opaque cursor. Batch maximum 100 files, submitted sequentially.
- Full source/typecheck/CI environments install `uv sync --locked --extra features` so optional torch/torchvision imports resolve without global packages. Installing these libraries does not download weights or run a model. The default demo never loads pretrained weights. Keep runtime imports behind the feature loader; no Pyright exclusions or broad missing-import ignores.
- CPU execution only, torch threads 2 and BLAS/OpenCV threads 1. Patch bank <=4,096 vectors x 128 float32; compare query chunks of 128 against bank chunks of 512. All quality and memory limits are configuration with a frozen manifest hash; API requests cannot override them.

## Source map

| Path | Responsibility |
| --- | --- |
| src/defect_lens/config.py, contracts.py, errors.py | Typed settings, domain/wire models, safe error envelope. |
| src/defect_lens/fixtures.py, manifests.py | Original deterministic data generator and split/provenance validation. |
| src/defect_lens/imaging.py, inference/preprocess.py | Bounded decoding, normalized frame, quality and alignment. |
| src/defect_lens/inference/base.py, difference.py, patch.py, calibration.py | Shared scorer protocol, both methods and validation-only thresholds. |
| src/defect_lens/models.py, lease.py | Immutable artifact manifests, readiness and machine lease. |
| src/defect_lens/db.py, migrations/001_initial.sql, repository.py | SQLite transactions and state transitions. |
| src/defect_lens/worker.py, supervisor.py | Child inference, deadlines, limits, restart and graceful stop. |
| src/defect_lens/api.py, routes.py, cli.py | Local HTTP contract and bounded command-line workflows. |
| src/defect_lens/evaluation.py, reporting.py, captures.py | Frozen split evaluation, real capture checks and reports. |
| web/src/api.ts, types.ts, App.tsx, components/*, styles.css | Typed API client and operator UI. |
| tests/unit, tests/integration, tests/e2e; web/src/*.test.tsx; web/e2e | Typed tests, actual API browser flow and process recovery. |
| scripts/dev.py, scripts/verify.py, scripts/clean_clone.py | Owned process orchestration and reproducible final checks. |
| assets/fixtures/recipe.json, configs/demo.json | Small tracked inputs; no generated bulk assets. |
| docs/RUNBOOK.md, docs/CAPTURE-GUIDE.md, docs/MODEL-CARD.md, reports/* | Operations and curated evidence. |

All generated application state is inside .runtime: PID records/database/logs at its root, .runtime/data for fixtures/captures, .runtime/models for weights/banks, and .runtime/outputs for batch/benchmark artifacts. Never load model artifacts using pickle. Use JSON plus NumPy npz with allow_pickle=False; pretrained state_dict loading uses weights_only=True from a verified local file.

## Typed contracts

Use Python enums and Pydantic models with extra='forbid'; serialize enum values as lowercase strings. IDs are UUID4 strings; revisions/artifact hashes are full lowercase SHA256. Timestamps are UTC RFC3339 strings ending Z. Score floats must be finite. API models are checked into web/src/types.ts and checked against an exported OpenAPI schema in integration tests.

```python
Decision = Literal['pass', 'review', 'fail']
Method = Literal['difference', 'resnet18_patch']
DataMode = Literal['procedural', 'owned_capture']
JobStatus = Literal['queued', 'running', 'succeeded', 'failed']
ModelStatus = Literal['unprepared', 'loading', 'ready', 'busy', 'degraded']
RgbFrame = NDArray[np.uint8]        # shape (256, 256, 3)
Heatmap = NDArray[np.float32]       # shape (256, 256), finite and nonnegative
PatchMatrix = NDArray[np.float32]   # shape (n, 128), n <= 4096

@dataclass(frozen=True)
class PreparedFrame:
    rgb: RgbFrame
    alignment_score: float | None
    quality_reasons: tuple[str, ...]

@dataclass(frozen=True)
class ScoreResult:
    score: float
    heatmap: Heatmap
    reasons: tuple[str, ...]

class Scorer(Protocol):
    def score(self, frame: PreparedFrame) -> ScoreResult: ...
```

`InputMetadata` contains raw_sha256, width, height, aspect_ratio and image_format. `AcceptedInput` contains normalized_path: Path and metadata: InputMetadata. `UploadForm` contains model_revision: str and data_mode: DataMode. `Calibration` contains low: float, high: float, pixel_threshold: float | None, heatmap_display_max: float, validation_manifest_sha: str, missed_cost: int=5, false_reject_cost: int=1 and seed: int=20261015.

`decode_image(path: Path) -> RgbFrame`; retain width/height/aspect/raw SHA in `InputMetadata` before resizing. `prepare_frame(frame: RgbFrame, reference: RgbFrame, metadata: InputMetadata) -> PreparedFrame`. `calibrate(samples: Sequence[LabelledScore], validation_manifest_sha: str) -> Calibration`, where LabelledScore has sample_id, specimen_id, truth good/defect, score and optional mask/heatmap. `decide(score: float, calibration: Calibration, reasons: tuple[str, ...]) -> Decision`. `fit_difference(train: Sequence[RgbFrame]) -> DifferenceScorer`; `fit_patch(train: Sequence[RgbFrame], encoder: PatchEncoder, seed: int) -> PatchScorer`; `PatchEncoder.encode(frame: RgbFrame) -> PatchMatrix` returns the 1,024 ordered grid patches before ROI selection.

ReadyState contains status: ModelStatus, model_revision: str | None, method: Method | None, data_mode: DataMode | None, worker_alive: bool and reason: str | None. Model metadata also exposes calibration low/high and heatmap_display_max for the numeric legend, without filesystem paths.

Job JSON contains id, status, model_revision, data_mode, created_at, started_at|null, finished_at|null, inspection_id|null and error|null. Inspection JSON contains id, job_id, model_revision, data_mode, original_decision, score|null, reasons[], aligned_image_url|null, heatmap_url|null, normalized_image_url, regions[] and latest_review|null. Region uses integer x,y,width,height in the aligned 256-square frame, plus peak_score; maximum 10 regions. A quality review may have score=null and no heatmap. No region text invents a defect cause.

Review JSON contains id, inspection_id, version, decision, note, operator_alias, created_at and model_revision. The alias is an unverified local label, not authenticated identity. Input ReviewCreate contains decision, note<=1,000 characters, operator_alias 1-80 characters and expected_version>=0; initial latest version is zero. An append-only review history preserves model output.

## Algorithms and model identity

1. Use the first lexicographically sorted good training sample as alignment anchor. OpenCV ECC with Euclidean motion aligns frames to it, max 40 iterations and epsilon 1e-5. Use the plate edge ring (24:232 excluding 40:216) as mask; score only ROI [32:224,32:224]. Reject transforms outside +/-5 degrees or +/-12 pixels, correlation <0.80, or ECC nonconvergence into review with reason alignment. Use WARP_INVERSE_MAP to render the aligned image. Unit tests establish transform direction using translated fixtures.
2. Difference baseline: align all good training images to the anchor, require at least four accepted frames, then take a per-pixel median RGB reference. At inference, subtract the clipped per-channel median brightness offset in [-0.10,0.10], compute mean-channel absolute difference in [0,1], and smooth with a 3 x 3 Gaussian. Persist float heatmap; display uses a fixed model-specific scale. This method needs no network and is the default demo.
3. Feature baseline: torchvision ResNet18 with explicit IMAGENET1K_V1 weights, eval mode and inference_mode, using layer2 feature extraction. Do not use DEFAULT aliases. The common aligned frame remains 256-square; normalize RGB with the documented ImageNet channel means/stds without the classification transform's 224 crop. This is a deliberate localisation preprocessing choice, recorded in the manifest. Require output [1,128,32,32]. Unit-normalize each patch vector, retain patches centered within ROI, and use seeded reservoir sampling of good training patches to bank <=4,096. For each query patch use minimum Euclidean distance to bank; interpolate the 32-square distance grid to 256-square and zero outside ROI. No pretrained feature execution is claimed by a fake encoder test.
4. Both methods use mean of the highest ceil(1% of ROI pixel count) heatmap values as image score. A connected component of pixels above the calibrated pixel threshold supplies regions; discard components <4 pixels and retain the 10 largest.
5. Validation-only calibration: enumerate finite candidate thresholds from midpoints of unique validation scores plus endpoints. Binary fail threshold minimizes 5*missed_defects + 1*false_rejects; ties choose the higher threshold. Require both classes; high=max(chosen,1e-6). Set low=min(good-validation 90th percentile,0.9*high). score<=low means pass, score>=high means fail, otherwise review; quality reasons always force review. These are frozen tabletop demo costs, not an industrial operating policy. Select pixel threshold by best validation defect-mask IoU, ties higher; absent masks make localisation threshold/IoU unavailable, not zero. Freeze heatmap_display_max=max(validation ROI heatmap 99.5th percentile,1e-6) for the display legend; this display scale does not alter scores.
6. Revision is SHA256 of canonical JSON covering method, inference source-tree SHA256, dependency lock hashes, preprocessing, quality gates, anchor/reference/bank/weights SHA256, training and validation manifest hashes, calibration and random seed. All file hashes are checked at load. Evaluation test IDs/hashes never enter fit/calibration. Original result stays linked to this revision after correction or model changes. Record Git commit/dirty flag as provenance metadata outside the revision identity so a documentation-only commit does not change the model. Preparation writes immutable output/revisions/<revision>/ artifacts and atomically updates output/CURRENT.json containing only revision. Repeating an identical preparation validates and reuses its revision; a new source/config/data identity adds a new revision without replacing the old one. Loader resolves CURRENT once at startup, validates the path/hashes and retains that revision for all accepted jobs until restart.

Torchvision documents the explicit [ResNet18 weight enum and normalization](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html) and [intermediate feature extraction](https://docs.pytorch.org/vision/stable/feature_extraction.html). OpenCV documents [ECC motion/alignment](https://docs.opencv.org/4.x/dc/d6b/group__video__track.html). APIs were checked on 2026-10-15; bootstrap must resolve a compatible torch/torchvision pair. These references support API choices, not accuracy on this task. Record upstream weight origin and applicable model/data terms in MODEL-CARD; the MIT source licence does not relicense pretrained assets.

## Data and split contract

`DatasetManifest` has schema_version=1, mode, generator_revision|null, seed|null and samples[]. Each sample has id, relative image_path, image_sha256, specimen_id, session_id, split train/validation/test, label good/defect/ambiguous, defect_kind none/missing_fastener/surface_mark/quality, mask_path|null, mask_sha256|null, lighting normal/dim/bright, blur none/mild/strong, source owned_procedural/owned_photo, rights_note and captured_at|null. Reject absolute paths, symlinks escaping the dataset root, duplicate IDs, checksum mismatch and specimen or session overlap across splits.

Procedural seed 20261015 creates six specimens per split with three split-specific sessions each. Each specimen/session pair yields two good views; validation and test additionally yield a missing-fastener view, a surface-mark view and one ambiguous blur view. Counts: train 36 good; validation 36 good + 36 defect + 18 ambiguous; test the same, total 216. Render gray square, four dark circles, surface noise and bounded pose/illumination in original Pillow/NumPy code. Generate pixel masks for known changes; blur samples have no defect mask. Augment after assigning specimen/session splits. Record generated-file hashes, recipe and code revision. Tiny unit tests use their own reduced seed data; fixture figures cannot substitute for owned-photo measurements.

Owned-photo pilot target: nine distinct physical assemblies, three per split, and three capture sessions per split with no session shared across splits. Acquire two good views, one missing-fastener view, one visible-mark view and one ambiguous quality view per specimen/session pair; training fits only good images. Count physical specimens honestly: moving the same plate does not create a new specimen. These target counts are a capture recipe, not assets currently available or a prerequisite for fixture completion. Consent/ownership, scene setup, hashes and reviewer labels are mandatory; private captures remain local. Review masks in the aligned coordinate frame with their transformation recorded.

## Durable state and recovery

SQLite uses WAL, foreign_keys=ON, busy_timeout=5000 and versioned transactional migrations. Tables:

- models(revision PRIMARY KEY, method, data_mode, manifest_json, created_at).
- jobs(id PRIMARY KEY, idempotency_key UNIQUE, request_hash, status CHECK, model_revision REFERENCES models, data_mode, input_relpath, raw_sha256, metadata_json, created_at, started_at, finished_at, error_json, reserved_bytes).
- inspections(id PRIMARY KEY, job_id UNIQUE REFERENCES jobs, model_revision REFERENCES models, original_decision CHECK, score NULLABLE, reasons_json, artifacts_json, regions_json, review_version DEFAULT 0, created_at).
- reviews(id PRIMARY KEY, inspection_id REFERENCES inspections, idempotency_key, request_hash, version, decision CHECK, note, operator_alias, model_revision REFERENCES models, created_at, UNIQUE(inspection_id,version), UNIQUE(inspection_id,idempotency_key)).

`Repository.enqueue(accepted: AcceptedInput, form: UploadForm, key: str, request_hash: str) -> tuple[Job, bool]`, `claim_next() -> Job | None`, `complete(job_id: str, result: StoredResult) -> Inspection`, `fail(job_id: str, error: JobError) -> None`, `recover_interrupted() -> int`, `add_review(inspection_id: str, request: ReviewCreate, idempotency_key: str) -> Review`. StoredResult carries score, decision, reasons, artifact-relative paths/sizes and regions. All status transitions use WHERE status=expected inside BEGIN IMMEDIATE; an unexpected zero row count raises state conflict.

Admission reserves capacity transactionally and deduplicates by idempotency key plus request hash (raw SHA, model revision and data_mode). Same key/same request returns the original job before checking current readiness or capacity; changed request is 409. Review replay checks an existing key/hash before the expected_version check, so a successful retry does not conflict with its own version increment. File promotion uses task-owned UUID paths and atomic rename. A success transaction inserts the unique inspection and changes running->succeeded together. A process crash before commit leaves an interrupted job, never a second review entry. Failures release unused reserved bytes while retaining actual input/artifact accounting.

On API startup obtain the per-project server ownership lock; refuse a second server. Recover running->failed with INTERRUPTED, leave queued jobs queued, then start worker. Do not silently retry interrupted inspections. A user may deliberately resubmit with a fresh key. Startup inspects only temporary files in its own .runtime/tmp directory; report unreferenced completed artifacts for manual cleanup instead of broad deletion.

There is no per-job cancellation endpoint in v1. Interrupt testing stops the owned worker/server and verifies durable recovery; the UI does not advertise a cancel action. Graceful shutdown stops admission, allows current job up to five seconds, then terminates only its child, marks unfinished running work INTERRUPTED and retains queued work. Confirm child exit before releasing the machine lease or server lock. OS hard-kill is covered by next-start recovery.

## HTTP and CLI

| Route | Success | Failure cases |
| --- | --- | --- |
| GET /healthz | 200 {status:'ok',database:'ok'} | 503 when database probe fails; independent of model. |
| GET /readyz | 200 ReadyState when active model and worker ready | 503 ReadyState with unprepared/loading/busy/degraded reason. |
| GET /api/models | 200 active revision, method, data_mode, status | Safe metadata only, no file paths. |
| POST /api/jobs | multipart image, model_revision, data_mode; required UUID Idempotency-Key; 202 Job, repeated request 200 | 400 malformed; 413 caps; 415 format; 422 pixels/corruption; 409 stale revision/key conflict; 429 busy/full; 503 model unavailable; 507 quota. |
| GET /api/jobs?cursor=&limit= | 200 {items:Job[],next_cursor:null|string} | 422 invalid pagination. |
| GET /api/jobs/{id} | 200 Job | 404 unknown; 422 invalid UUID. |
| GET /api/inspections/{id} | 200 Inspection including latest review | 404 unknown. |
| GET /api/inspections/{id}/artifacts/{kind} | 200 image/png for normalized/aligned/heatmap | 404 absent; no arbitrary paths or downloads from supplied URLs. |
| POST /api/inspections/{id}/reviews | ReviewCreate + UUID Idempotency-Key; 201 Review, repeat 200 | 404 missing; 409 expected_version/key conflict; 422 invalid body. |
| GET /api/inspections/{id}/reviews | 200 {items:Review[]} ordered version ascending | 404 missing. |

Every non-readiness error uses {error:{code,message,retryable,request_id,details}}. Details is a typed object containing field errors or safe limits, never exception text or filesystem paths. Codes include INVALID_REQUEST, BODY_TOO_LARGE, UNSUPPORTED_IMAGE, INVALID_IMAGE, IMAGE_DIMENSIONS, QUEUE_FULL, UPLOAD_BUSY, MODEL_UNAVAILABLE, MODEL_CHANGED, IDEMPOTENCY_CONFLICT, REVIEW_CONFLICT, NOT_FOUND, STORAGE_LIMIT, TIMEOUT, MEMORY_LIMIT, INTERRUPTED and INTERNAL. Unknown exceptions log a request ID and return generic INTERNAL. Inference quality reasons belong in successful inspection results.

Commands installed as `defect-lens`: `fixtures --output .runtime/data/fixtures --seed 20261015`; `prepare --method difference --dataset .runtime/data/fixtures/manifest.json --output .runtime/models/demo-difference`; `prepare --method resnet18_patch --dataset .runtime/data/fixtures/manifest.json --output .runtime/models/demo-patch`; `serve --model .runtime/models/demo-difference --host 127.0.0.1 --port 8111`; `batch --manifest .runtime/data/batch/manifest.json --api http://127.0.0.1:8111 --output .runtime/outputs/batch.jsonl`; `benchmark --dataset .runtime/data/fixtures/manifest.json --difference-model .runtime/models/demo-difference --patch-model .runtime/models/demo-patch --output .runtime/outputs/fixture-evaluation`; `captures validate --manifest .runtime/data/captures/manifest.json`; `export-report --input .runtime/outputs/fixture-evaluation --output reports/fixture-v1`. Paths in batch manifests stay within their manifest directory. CLI nonzero codes: 2 invalid input, 3 resource/model unavailable, 4 processing/evaluation failure. JSONL has one record per sample including failures; command exits 4 if any failed.

## Shared machine lease and readiness

Heavy preparation, pretrained model load, feature inference and full benchmarks atomically mkdir /tmp/bentolabs-portfolio-ml.lock. owner.json records project='defect-lens', supervisor PID, UTC start, purpose, random ownership token and process start identity. Busy mkdir means no weight loading or benchmark starts; return model_busy / exit 3 and continue light work. Never delete another owner's lock or spin. Stale recovery requires inspect owner and process identity; a reused PID is not proof. The supervisor owns the lease for the complete lifetime of its model child. On normal/error/interrupt paths, stop and join that child before checking token and releasing its own lease. No resident pretrained model is allowed after release.

The default difference demo can run while another project owns the lease. A feature-configured server still serves health, history and UI if busy, but readyz=503 and submissions=503 MODEL_UNAVAILABLE; it does not switch models. A later explicit restart after resource availability loads the selected model. A full comparison benchmark acquires one lease for both methods and all timings, closes feature workers before release, and excludes concurrent app inference. Missing weights are unprepared, not health failure. Preparation downloads only the named public checkpoint into this project's ignored models directory, records URL/hash, and never needs cloud keys. Publishing, pushes, deployments, model uploads and paid compute need specific authorization.

## UI and accessibility

Use system sans (-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif), 16px body with 1.5 line height, 14px labels, 24px page title and tabular numerals for scores/times. Spacing scale 4/8/12/16/24/32px; 8px radius; borders 1px. Content max width 1440px. At >=1100px use 280px queue plus flexible image workbench and 280px details. Between 720 and 1099px use queue above two columns. Below 720px stack upload, result, image controls, correction and queue; no horizontally scrolling controls. Image aspect ratio remains 1:1.

Light palette: background #F6F7F9, surface #FFFFFF, text #17212B, muted #526171, border #CCD3DB, action #1458C4. Dark: background #11161D, surface #1B2430, text #F2F5F8, muted #B4C0CE, border #445366, action #8DB8FF. Use text/icon labels for pass, review, fail and error. Heatmap is amber-to-magenta with a labelled numeric legend, never a red/green-only signal. Check actual contrast in both themes; do not assume hex values alone prove compliance.

Visible persistent badges identify Procedural demonstration / Owned capture, method, model revision short form with full-copy button, and model readiness. Empty state offers Generate sample instructions and an upload button. A queued/running job shows stable status text; failed jobs show the exact safe error and resubmit action with a new key. Quality review explains framing/blur/alignment and does not display an empty heatmap as success. Corrections show both original and latest decisions and history; conflicts prompt refresh without discarding typed notes.

All controls have visible focus, >=44px target, proper labels and keyboard order. Use native file input and button controls; no drag-only action. Heatmap opacity is an accessible range input with numeric output. Aligned image caption states its coordinate frame; textual regions expose bounding boxes and relative scores for nonvisual review. Poll job every 1 second while nonterminal, stop at terminal or tab hidden, back off to 5 seconds on network error and provide retry. Announce state changes through a polite live region without repeating every poll. Respect prefers-color-scheme, persist explicit theme selection and respect prefers-reduced-motion; only 120ms opacity transitions on state changes, no indefinite decorative animation. Read the available frontend-design skill before UI implementation and review alignment/spacing/details at finish.

## Evidence and finish

Reports contain schema_version, claim_level fixture/owned_capture, separate data_mode and execution_mode real_difference/real_pretrained, code/lock/model/manifest hashes, sample counts, actual OS/chip/RAM/runtime/device, seeds, calibration and timing method. Report binary precision/recall and confusion at high threshold; false reject=good predicted fail/good, missed defect=defect below high/defect. Also report operational defect pass rate and review burden so reviews are not concealed as passes. Ambiguous examples are a separate quality-review slice and excluded from binary truth denominators.

Include lighting/blur slices, pixel average precision and IoU where masks exist, false-reject/miss gallery, warm latency median/p95, cold load+first-inference latency, throughput and peak RSS for parent plus child. Bootstrap 1,000 resamples by specimen, seed 20261015, only with >=5 specimens; otherwise intervals=null with a small-sample reason. Zero denominators yield null, never zero. Freeze validation artifacts before inspecting test outcomes; test data never refits thresholds. For latency use one model load and 3 unmeasured warmups, then all eligible test samples; record whether decode/alignment/inference/storage are included. End-to-end API timing includes all four; scorer timing is separate.

Curate reports/fixture-v1/{report.json,report.md,split-manifest.json,environment.json,failure-gallery/} with explicitly reviewed original fixture images only. Keep bulk outputs ignored. If no owned captures exist, create a factual reports/owned-capture-status.md stating no run/no metrics plus the capture recipe; never fill invented values. MODEL-CARD states limits, sources and which evidence actually ran. Follow docs/RELEASE-STANDARD.md in addition to this specification. docs/STATE.md records exact commands, outcomes, open issues and next task; no claims from file existence alone.
