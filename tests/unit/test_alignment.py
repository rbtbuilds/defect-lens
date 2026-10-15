import numpy as np

from defect_lens.contracts import InputMetadata
from defect_lens.inference.preprocess import prepare_frame
from tests.support import make_frame


def test_translation_is_removed_and_blur_forces_review() -> None:
    anchor = make_frame()
    metadata = InputMetadata(raw_sha256="a" * 64, width=256, height=256, aspect_ratio=1)
    aligned = prepare_frame(make_frame(dx=4), anchor, metadata)
    assert aligned.quality_reasons == ()
    assert float(np.abs(aligned.rgb.astype(float) - anchor).mean()) < 2
    assert "blur" in prepare_frame(make_frame("blur"), anchor, metadata).quality_reasons
    assert "alignment" in prepare_frame(make_frame(dx=24), anchor, metadata).quality_reasons
