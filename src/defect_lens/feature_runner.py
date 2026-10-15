import json
import sys
from pathlib import Path

import numpy as np

from defect_lens.fixtures import render_frame
from defect_lens.inference.patch import PatchScorer
from defect_lens.inference.preprocess import PreparedFrame
from defect_lens.models import load_model, prepare_model


def probe(directory: Path, token: str) -> None:
    bundle = load_model(directory, token)
    if not isinstance(bundle.scorer, PatchScorer):
        raise TypeError("Expected patch model")
    frames = [
        np.asarray(render_frame(kind)[0], dtype=np.uint8) for kind in ("good", "missing", "mark")
    ]
    vectors = bundle.scorer.encoder.encode(frames[0])
    scores = [bundle.scorer.score(PreparedFrame(frame, 1, ())).score for frame in frames]
    print(
        json.dumps(
            {
                "shape": list(vectors.shape),
                "scores": scores,
                "revision": bundle.manifest.revision,
                "weight_sha": bundle.manifest.artifact_hashes["weights.pth"],
            }
        )
    )


if __name__ == "__main__":
    if sys.argv[1] == "--probe":
        probe(Path(sys.argv[2]), sys.argv[3])
    else:
        prepare_model(
            Path(sys.argv[1]), "resnet18_patch", Path(sys.argv[2]), _lease_token=sys.argv[3]
        )
