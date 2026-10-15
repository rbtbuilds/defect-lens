# Final source review and regression evidence

One fresh-context reviewer inspected a9a731f..47d97ae. The initial verdict was NEEDS WORK: eight Important findings, no established Critical finding and no Minor findings. The implementer accepted all eight and made one fix pass; no second review is represented as having occurred.

| Finding | Fix | Regression |
| --- | --- | --- |
| Sample IDs became output paths | SHA256-derived artifact/gallery names; storage accepts one safe path component | Absolute/traversal IDs in test_evaluation.py |
| Old queued revisions blocked capacity | After a different verified model is ready, incompatible queued jobs fail MODEL_CHANGED with original revision/input retained | test_model_change_terminalizes_incompatible_queue |
| Late correction refresh replaced another inspection | A refresh can update only the currently displayed inspection ID | Deliberately reordered promises in App.test.tsx |
| Quality override changed binary metrics | High-threshold prediction independent of operational review; raw score retained separately | test_binary_threshold_is_independent_of_quality_review |
| Pixel AP depended on tied-pixel order | Group equal-score thresholds before precision-recall integration | test_pixel_ap_groups_tied_thresholds |
| Corrupt first test image aborted evaluation | Cold/warmup selection handles failures; all outcomes remain, unavailable timings are null | First-corrupt and no-usable-image cases in test_evaluation.py |
| Capture label contradicted kind/annotation | Validate the complete label/kind/annotation relationship | test_capture_label_and_kind_must_agree |
| Batch discovery failure skipped failure rows | Validate discovery and emit a failure row for each affected item, exit 4 | Refused/503/malformed model responses in test_batch.py |

Focused tests were observed failing before these fixes and passing afterward. The final full command outcomes are recorded in STATE: 63 Python unit/integration tests, 8 UI tests, 5 browser tests and 1 restart test passed, alongside strict Python/TypeScript checks and a production build. Additional verified repairs cover clean-checkout runtime initialization, busy-lease attempts leaving no output directory, process-local thread limits before numeric imports, child shutdown completion, unavailable-database health responses, and whole-benchmark lease ownership with process-group cleanup. An immediate-repeat port-test failure was reproduced with a recently closed TCP connection and fixed by matching the real server's SO_REUSEADDR setting; active-owner refusal remains tested.

The reviewer set aside comparative measurements pending execution, owned-photo accuracy/authenticity without assets, unperformed screen-reader testing, cloud/authentication/cancellation outside v1, and an unestablished mirrored/rotated alignment defect. The comparison has since run and its raw rows/gallery were inspected by the implementer; the report is limited to procedural inputs. The release does not claim the remaining unsupported outcomes; source uses inverse ECC and tests translation/EXIF direction, but that does not certify arbitrary poses.

One path-escape regression initially created a PNG probe under /tmp. The implementer verified its SHA256 against the test's generated aligned artifact and removed only that probe. The absolute-path regression now stays within this checkout's .runtime/pytest tree; no probe remains outside the project.
