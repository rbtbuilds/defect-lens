import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    shutil.which("node") is None,
    reason="Recording packaging regression requires Node",
)
def test_packager_preserves_existing_sidecar_when_video_is_absent(tmp_path: Path) -> None:
    node = shutil.which("node")
    assert node is not None
    binaries = tmp_path / "bin"
    binaries.mkdir()
    marker = tmp_path / "encoder-started"
    encoder = binaries / "ffmpeg"
    encoder.write_text('#!/bin/sh\nprintf attempted > "$DEFECT_LENS_ENCODING_MARKER"\nexit 99\n')
    encoder.chmod(0o755)
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
        [node, "web/demo/package.mts", str(manifest), str(output)],
        env={
            **os.environ,
            "PATH": str(binaries) + os.pathsep + os.environ.get("PATH", ""),
            "DEFECT_LENS_ENCODING_MARKER": str(marker),
        },
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0
    assert not marker.exists()
    assert sidecar.read_text() == "prior provenance, must remain intact\n"
    assert not output.exists()
