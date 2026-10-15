from pathlib import Path

import numpy as np

from defect_lens.contracts import DatasetManifest
from defect_lens.fixtures import Kind, generate_fixtures, render_frame
from defect_lens.imaging import RgbFrame


def make_frame(kind: Kind = "good", dx: int = 0) -> RgbFrame:
    image, _ = render_frame(kind, dx=dx)
    return np.asarray(image, dtype=np.uint8).copy()


def make_dataset(root: Path, specimens_per_split: int = 1) -> DatasetManifest:
    return generate_fixtures(root, seed=17, specimens_per_split=specimens_per_split)
