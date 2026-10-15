import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from defect_lens.lease import LeaseBusy, MachineLease
from defect_lens.models import read_model_manifest

pytestmark = pytest.mark.real_model


def test_actual_pretrained_features() -> None:
    model = Path(".runtime/models/demo-patch")
    assert (model / "CURRENT.json").exists(), "Run the documented feature prepare command first"
    try:
        handle = MachineLease().acquire("actual pretrained integration test")
    except LeaseBusy as error:
        pytest.skip(str(error))
    with handle:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "defect_lens.feature_runner",
                "--probe",
                str(model),
                handle.token,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    data = json.loads(result.stdout)
    assert data["shape"] == [1024, 128]
    assert np.isfinite(data["scores"]).all()
    assert len(set(data["scores"])) > 1
    manifest = read_model_manifest(model)
    assert data["weight_sha"] == manifest.artifact_hashes["weights.pth"]
    assert len(data["weight_sha"]) == 64
