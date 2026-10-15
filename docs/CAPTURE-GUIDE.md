# Owned-photo capture guide

No owned capture set has been supplied. This is an acquisition recipe, not a statement that these assets exist.

Use nine genuinely distinct matte gray square plates/cards, each with four dark circular fasteners. Assign three physical assemblies to each split before photography. Moving the same assembly does not create another specimen. Use three exclusive capture sessions per split; no session or physical specimen crosses a split. Place the assembly in a jig beneath a fixed overhead camera, on a neutral background. Record camera height/distance, lighting, background, camera settings and date. Keep the plate within the central 192-square region after normalization to 256-square.

For every specimen/session pair capture two good views, a removed-fastener view, a staged visible surface mark and an ambiguous quality view. Keep all originals locally with their SHA256. Training fits only good views: include its 18 good images in the model manifest; keep the other training-side observations in a separate acquisition ledger. Validation and test each contain 18 good, 18 known defect and 9 ambiguous views. Never call marker/tape a crack or infer damage causes.

Write the DatasetManifest schema from src/defect_lens/contracts.py. Use mode owned_capture, generator_revision null, source owned_photo, explicit rights_note and timezone-aware captured_at for each sample. Unique specimen/session/sample IDs, relative contained paths and matching image/mask hashes are required. Do not publish private captures.

Every sample needs capture_review with reviewer_alias (an unverified local label), physical_specimen_confirmed true, annotation good/missing_fastener/staged_surface_mark/quality, setup_notes and positive distance_cm. Quality images are ambiguous, not labelled defects. Inspect originals yourself before confirming these fields; a script cannot establish consent or truth.

Review masks in the 256-square coordinate frame. Set mask_coordinate_frame normalized for masks that will follow the image ECC transform, or aligned for masks already transformed to the selected first lexicographic good training anchor. Save the six-value affine mask_transform. For aligned masks also record mask_anchor_sample_id; preparation checks the selected anchor and avoids a second transform. Keep the corresponding unmodified original and annotation record.

Run:

```bash
uv run defect-lens captures validate --manifest .runtime/data/captures/manifest.json
```

Exit 2 means validation failed. valid checks schema/provenance consistency, not photographic authenticity. pilot_counts_met separately checks the target specimen/session group counts. Bootstrap intervals require five held-out groups and therefore remain unavailable for the three-specimen pilot. Acquire more genuinely distinct test assemblies for intervals; do not duplicate records to pass a count.

Only after human review and successful validation prepare separate owned-capture revisions and run the same frozen comparison. Never mix procedural and photographic metrics or tune thresholds on held-out images. No third-party benchmark download is needed.
