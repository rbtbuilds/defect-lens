import json
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    any(shutil.which(binary) is None for binary in ["node", "ffmpeg", "ffprobe"]),
    reason="Recording packaging regression requires Node, FFmpeg and FFprobe",
)
def test_packager_preserves_existing_sidecar_when_video_is_absent(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    source.write_bytes(Path("docs/demo/walkthrough.mp4").read_bytes())
    recording = json.loads(Path("docs/demo/walkthrough.json").read_text())
    recording["video"] = str(source.resolve())
    manifest = tmp_path / "recording.json"
    manifest.write_text(json.dumps(recording))
    output = tmp_path / "output.mp4"
    sidecar = tmp_path / "output.json"
    sidecar.write_text("prior provenance, must remain intact\n")
    result = subprocess.run(
        ["node", "web/demo/package.mts", str(manifest), str(output)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0
    assert sidecar.read_text() == "prior provenance, must remain intact\n"
    assert not output.exists()
