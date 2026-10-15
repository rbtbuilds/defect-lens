# Native execution record

Plan: `superpowers/plans/2026-10-15-v1.md`. Project source edits were confined to the assigned checkout; the documented path-escape test probe was removed, and heavy work used the shared lease protocol. This durable copy preserves task outcomes, rulings and one fresh-review fix pass before removal of this plan's temporary skill workspace. Historical suite counts refer to their respective revisions.

# SDD ledger - plan: docs/superpowers/plans/2026-10-15-v1.md

Pre-flight: Tasks2->3 share RgbFrame/manifest; Tasks3->4 share Scorer/calibration/model manifest; Tasks3/4->5 share verified model and worker contracts; Tasks5->6 share Repository jobs/reviews; Tasks6->7 share HTTP wire types; Tasks2/3/4->8 share frozen evaluation; Tasks2/8->9 share capture manifests; Tasks1-9->10 share runnable CLI and evidence. Interfaces checked against SPEC.
Ruling: Use the explicitly assigned child checkout directly on feat/defect-lens-v1 rather than creating a second worktree; independent repositories already isolate concurrent work. Cost if wrong: an additional local worktree can be introduced without changing API behavior.
Ruling: Use installed Node26.7.0 as the documented local exception because no Node24 installation/version manager was found and Vite's published engine supports >=22.12. CI remains Node24. Cost if wrong: pin a project-local supported Node binary and rerun frontend checks.
Task1: started; initial documentation baseline a9a731f.
Task1: Ruling: Scope pytest temporary files to .runtime/pytest because the default pytest temp root attempted cleanup of another suite's protected artifacts. No outside artifacts changed by our cleanup code. Cost if wrong: change only the local test runner path.
Task 1: complete (commits a9a731f..d6a1702, tests: uv run pytest -q -> 2 passed in 0.18s)
Task 2: complete (commits d6a1702..91d0139, tests: uv run pytest -q -> 10 passed in 4.08s)
Task 3: Ruling: Add the ECC transform to PreparedFrame for consistent validation-mask alignment; public scorer fields remain compatible. Cost if wrong: remove the internal transform field and pass it separately.
Task 3: complete (commits 91d0139..fdb15e8, tests: uv run pytest -q -> 19 passed in 5.65s)
Task 4: complete (commits fdb15e8..09717cf, tests: uv run --extra features pytest -m 'not real_model' -q -> 23 passed, 1 deselected in 6.46s)
Task 5: Ruling: Correct the representative completion INSERT to ten schema columns (the snippet had eleven values); preserve the specified atomic transaction. Cost if wrong: completion tests and migration must be revised together.
Task 5: complete (commits 09717cf..1205f65, tests: uv run --extra features pytest -m 'not real_model' -q -> 30 passed, 1 deselected in 10.86s)
Task 6: complete (commits 1205f65..34f0763, tests: uv run --extra features pytest -m 'not real_model' -q -> 38 passed, 1 deselected in 13.70s)
Task 7: complete (commits 34f0763..6e5dcca, tests: npm --prefix web run test -- --run ->    Duration  766ms (environment 69%, setup 14%, tests 13%, import 2%, transform 2%))
Task 8: Ruling: Add explicit keyword dataset_root/model_directories to evaluate because manifests intentionally contain relative data and no host artifact paths; never infer them from inherited cwd. Cost if wrong: adjust the CLI adapter and callers.
Task 8: Ruling: Defer the measured run while Casework owns the shared lease and execute independent capture/runbook work; leave Task 8 incomplete until actual evidence. Cost if wrong: rerun final model preparation after any inference identity changes.
Task 9: complete (commits d1c2231..469ee42, tests: uv run pytest tests/unit/test_captures.py -q -> 2 passed in 0.96s)
Final: Ruling: Start the single fresh source review while lease-dependent measurements remain pending; only measured report/docs will be added afterward, and behavior fixes require RED-to-GREEN verification. Cost if wrong: unreviewed measurement interpretation must be checked against the saved schema and raw rows.

Final review: one fresh reviewer, eight Important findings accepted, no Critical or Minor findings; no re-review.
Final: fixed sample-ID path escape - absolute/traversal regression RED->GREEN, Python suite 62/62.
Final: fixed incompatible queued revision capacity block - test_model_change_terminalizes_incompatible_queue RED->GREEN, Python suite 62/62.
Final: fixed late review refresh replacing selected inspection - reordered promise test RED->GREEN, UI suite 8/8.
Final: fixed quality override contaminating binary metrics - test_binary_threshold_is_independent_of_quality_review RED->GREEN, Python suite 62/62.
Final: fixed tied-score pixel AP - test_pixel_ap_groups_tied_thresholds RED->GREEN, Python suite 62/62.
Final: fixed corrupt first/all test-image evaluation abort - corrupt/no-usable-image regressions RED->GREEN, Python suite 62/62.
Final: fixed capture label/kind contradiction - test_capture_label_and_kind_must_agree RED->GREEN, Python suite 62/62.
Final: fixed batch discovery failure missing per-item rows - refused/503/malformed discovery regressions RED->GREEN, Python suite 62/62.
Final: additional RED->GREEN repairs cover clean-clone runtime initialization, busy lease leaving no output, numeric thread limits, child/grandchild exit before lease release, borrowed lease ownership and unavailable-database health. Full 14-command verify passed, including 5 browser and 1 restart checks.
Final: Ruling: After a different verified model becomes ready, fail incompatible queued jobs as MODEL_CHANGED instead of retaining them indefinitely - preserve input and original revision while restoring capacity. Cost if wrong: users must explicitly resubmit under the new revision.
Final: Ruling: Add optional benchmark --prepare with one borrowed lease covering preparation and comparison; own POSIX child groups and retain lease if cleanup cannot be confirmed. Cost if wrong: adapt and retest process cleanup for a different operating system; macOS is verified, Linux CI is configured but not run here.
Final: Ruling: Comparative quality/latency/RSS originally set aside by reviewer - now measured on both actual frozen methods, raw rows and 36 gallery images inspected by implementer; difference remains default. Cost if wrong: reproduce benchmark and correct interpretation; procedural evidence cannot establish photographic performance.
Final: Ruling: Owned-photo accuracy/authenticity set aside - no assets supplied, explicit NOT RUN gate and no accuracy claim. Cost if wrong: acquire rights-cleared reviewed captures and run a separate frozen study before relying on real-photo behavior.
Final: Ruling: Screen-reader behavior set aside - keyboard/browser checks pass but screen reader NOT TESTED. Cost if wrong: manual screen-reader audit and remediation before claiming that support.
Final: Ruling: Cloud/authentication/per-job cancellation set aside - local-only v1 with documented process interruption/recovery. Cost if wrong: design those capabilities before networked or multi-user use.
Final: Ruling: Mirrored/rotated alignment defect not established - inverse ECC and translation/EXIF tests stand, arbitrary poses are not certified. Cost if wrong: add pose captures/regressions and adjust alignment before broadening the supported view.
Final: Ruling: Keep feat/defect-lens-v1 and this checkout as-is; no publishing or push authorized and no integration base selected. Cost if wrong: Matthew chooses later local integration/publication steps; no remote state changed.
Deferred minors: none were reported.
Task 8: complete (commits 6e5dcca..d8ac404, tests: uv run pytest tests/unit/test_metrics.py tests/integration/test_evaluation.py -q -> 12 passed in 7.04s)

Final: fixed immediate-repeat port test bind failure - test_occupied_port_refusal_after_server_close reproduced TIME_WAIT RED->GREEN; test listener now uses SO_REUSEADDR as the real server does while still asserting active-owner refusal. Product port/process behavior unchanged. Full suite rerun required.
Task 10: complete (commits 469ee42..d110de4, tests: uv run python scripts/verify.py --fixture-only -> })

Final verification: 63 Python unit/integration tests, 8 UI tests, 5 actual-API browser tests, 1 restart test, strict Python/TypeScript checks and build pass. Separate real-model test: 1 pass. Fresh exact-source clone d110de4 passes all four install/verify commands with independent dependencies/data. No deferred minors.
