# Photographic and recording pass: independent automated review

The reviewer examined changes from `40e5d51`, source acquisition, the actual
recording and the first saved photographic report. This was an independent
AI code-review agent, not human annotation review or physical validation.

## Findings and remediation

Four Important findings were reproduced and fixed in one pass:

- Mixed relative script and absolute module paths aborted provenance export.
  `test_source_identity_accepts_relative_script_and_absolute_module_paths` uses
  known SHA256 values and portable relative keys. RED-to-GREEN.
- OpenCV threading was not controlled before both methods. The macOS GCD backend
  also ignores positive requests. The adapter now disables parallelism before
  input loading and after model construction, verifies reported count 1, and
  records it. `test_comparison_applies_thread_cap_before_even_loading_inputs`
  and the factory-reset case in the corrupt-input regression passed RED-to-GREEN.
  Original plate source/reports remain unchanged; EVALUATION records their
  historical timing-policy limitation.
- Cold/warmup decoding could abort on the first development image before failure
  retention. Warmups now use already decoded fit data; every development input
  runs inside the retained-error path. The hash-valid corrupt-first-image
  regression preserves all rows and marks the report incomplete. RED-to-GREEN.
- File hashes alone did not enforce exact frozen membership, labels and source
  fields. The adapter now pins the complete canonical acquisition manifest plus
  upstream CSV/licence hashes. Ten mutation cases reject changed source fields,
  removed members, labels, partitions and mask assignments. RED-to-GREEN.

The reviewer marked paired provenance overwrite Minor. The implementation owner
treated it as Important because it could destroy the only recording record.
The packager refuses an existing MP4 or JSON. The subprocess regression
`test_packager_preserves_existing_sidecar_when_video_is_absent` first reproduced
actual overwrite, then passed with both the old sidecar and absent output intact.
The CI variant uses a sentinel encoder to assert that encoding never starts
when the sidecar exists. This removes FFmpeg/FFprobe as test dependencies;
actual video conversion was separately exercised with the real tools.

No fixes were re-reviewed. Regression tests and the full verification suite
provide the post-fix evidence; see STATE for exact counts and commands.

## Independent evidence checks

The initial report audit recomputed image thresholds and tie-breaking, decisions,
confusion, review counts and latency quantiles. It checked all 48 image/mask
hashes, exact 12/12/12 selection, upstream labels, protocol/metadata/licence,
checkpoint, six algorithm-source and two dependency-lock identities. No mismatch
was found. The curated JSON is a byte-for-byte copy of that audited report:
`21ce82658cd7927b9e551cfd524273e7eca4860ae9aecc99cbfcc18f0407aa50`.

Video checks matched hashes, encoder metadata, script identities, sampled frames,
actual SQLite jobs and pass/fail/review outcomes. The correction is explicitly
attributed to Automated demo. The packager protection was subsequently verified
by its regression and used to repackage the same WebM; MP4 bytes are unchanged.

Limits: no independent model rerun, per-pixel heatmap recalculation, cold timing
remeasurement, physical specimen confirmation, human label/output review or
screen-reader audit. Pixel aggregates match saved rows; raw heatmaps are not
retained. These are development resubstitution results, not held-out accuracy.
