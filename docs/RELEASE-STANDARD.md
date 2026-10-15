# Portfolio release standard

A project is ready for the portfolio when another engineer can run it, inspect the evidence and understand its limits. A documented design is a planned project, not a shipped application.

## Repository contents

Every project owns its Git history, dependency lockfiles, code licence, data provenance and release. Use MIT for original project code and documentation. Keep third-party model and dataset terms separate; the MIT licence does not relicense their assets. Do not copy existing private product code or client records into these repositories.

At first application release, include a README with a screenshot or short recording, a concrete problem, a quickstart tested from a clean checkout, architecture, evaluation results, limitations and operating instructions. Include CONTRIBUTING.md, SECURITY.md, a documented configuration example containing no credentials, and a changelog for releases. Add only files that have a concrete purpose.

The demo must have a deterministic, account-free sample path. Real model execution and external-provider modes must be labelled separately from fixtures and mocks. A live public demo is optional; it requires its own access, cost and deployment decision.

## Validation

Run strict checks for the languages actually used, including test files. For Python, use strict static checking plus functional tests; for TypeScript, enable strict checking and include test code in a checked project. Test the full user flow on a clean environment, not just individual functions.

Each project has an EVALUATION.md defining the baseline, data split, measurements and end-to-end scenario. Freeze held-out inputs before tuning. Report the model revision, dataset manifest hash, hardware, commands, seeds, sample counts and failures. Keep targets separate from observed results and publish results even if a proposed method loses to the baseline.

CI should run deterministic offline tests and checks without paid credentials. Real inference benchmarks run explicitly and save their provenance; mocks must not be reported as model quality measurements.

## Interface and operation

Before implementation, define typography, spacing, palette, responsive behavior, light and dark themes, keyboard operation and accessible status/error presentation. Motion should communicate a state change and respect reduced-motion settings. Review alignment, spacing and consistency after exercising the real flow.

Bound file sizes, job duration, concurrency and model calls. Provide cancellation, readable failures, request identifiers and health status where relevant. Document restart and recovery behavior. Do not claim deployment, latency or throughput on hardware that was not tested.

## Portfolio case study

Explain the intended user, current manual workflow, constraints and acceptance criteria. Show the baseline and the measured change, a meaningful failure, and a technical decision made from evidence. Use a reproducible local simulation where no real customer pilot exists. Never describe simulated time savings as customer impact.

A two-minute walkthrough should show input, processing, evidence, an error or uncertainty case and the final result. A longer engineering note should explain architecture and the evaluation in enough detail to reproduce it.

## Publication boundary

Publish each child repository independently after its scope is accepted. Never initialise or publish a repository at the portfolio parent: its legacy folders are unrelated and may contain private material. Exclude local datasets, recordings, model weights, credentials, caches and generated benchmark output by default. Review explicit release artifacts separately.
