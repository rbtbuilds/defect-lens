# Browser walkthrough

[Watch the captioned recording](demo/walkthrough.mp4). It shows actual local
difference inference on three generated fixtures: a good view, a missing
fastener and blur. The correction is submitted by automation, not a person.
The caption bar is a recording annotation; no inference responses are mocked.
There is no audio. Input/model hashes, captions and encoder metadata are in
[walkthrough.json](demo/walkthrough.json).

## Record it again

After the README setup, with ports 8111/5111 free and FFmpeg/FFprobe installed:

```bash
uv run python scripts/dev.py start --model .runtime/models/demo-difference
node web/demo/record.mts
node web/demo/package.mts
uv run python scripts/dev.py stop
```

The recorder asserts each new job succeeds, overlays are available on the
clear examples, blur suppresses localization, and the scripted correction
survives reload. It writes a WebM and `.runtime/demo/latest.json`; the packager
creates `.runtime/demo/walkthrough.mp4` and a portable provenance JSON. Existing
videos are never overwritten. Pass a new output filename as the packager's
second argument to make another recording:

```bash
node web/demo/package.mts .runtime/demo/latest.json .runtime/demo/another-take.mp4
```

The published clip is a single continuous browser recording, transcoded to H.264
with a web-friendly pixel format and fast start. Caption times use wall time;
allow a small video startup offset. The viewport is deliberately tall so the
evidence and correction panels remain visible. Stop owned servers even if a
recording assertion fails. Recordings create real local jobs and review entries.

## Transcript

- Start with a good reference view and its actual saved inference.
- Inspect the missing-fastener overlay and adjust opacity.
- Show blurred input forcing review, with score/localization suppressed.
- Save an explicitly scripted correction; open history and reload.
- Close with the evidence boundary: procedural workflow, separate public-photo
  development diagnostics, no industrial validation.

## Longer live walkthrough

0:00-0:20: Show the README scope and the persistent Procedural demonstration, method, readiness and revision labels. Explain the controlled overhead gray plate with four dark fasteners. This is a reproducible local simulation, not a customer pilot.

0:20-0:45: Choose a held-out good PNG from .runtime/data/fixtures, inspect it and follow queued/running/succeeded. Point to the original decision and numeric score. Show normalized versus aligned geometry and copy the full revision.

0:45-1:05: Submit a missing-fastener or staged-mark fixture. Adjust the heatmap with the keyboard. Read the fixed numeric legend and region coordinates; describe unusual appearance without inventing a damage cause.

1:05-1:25: Submit an ambiguous blur fixture. Explain why the quality heuristic forces review and suppresses score/heatmap rather than presenting false localization. Show a corrupt upload failing clearly if time permits.

1:25-1:45: Record an operator correction and note. Open correction history, reload and show both the original output and the latest version. Explain that this feedback does not automatically retrain the model.

1:45-2:00: Open the measured report and model card. Distinguish procedural results, actual pretrained execution and the absent owned-photo study. Mention the clean-clone command and scoped stop command; do not claim industrial accuracy or time savings.
