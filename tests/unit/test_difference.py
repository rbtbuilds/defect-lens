from defect_lens.inference.difference import fit_difference
from defect_lens.inference.preprocess import PreparedFrame
from tests.support import make_frame


def test_missing_fastener_scores_above_good() -> None:
    scorer = fit_difference([make_frame() for _ in range(4)])
    good = scorer.score(PreparedFrame(make_frame(), 1, ()))
    missing = scorer.score(PreparedFrame(make_frame("missing"), 1, ()))
    assert missing.score > good.score + 0.05
    assert missing.heatmap[68, 68] > 0.3


def test_known_mark_localizes_in_heatmap() -> None:
    import numpy as np

    from defect_lens.fixtures import render_frame

    image, mask = render_frame("mark")
    scorer = fit_difference([make_frame() for _ in range(4)])
    result = scorer.score(PreparedFrame(np.asarray(image, dtype=np.uint8), 1, ()))
    assert mask is not None
    assert float(result.heatmap[np.asarray(mask) > 0].mean()) > 0.1
