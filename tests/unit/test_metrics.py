from defect_lens.evaluation import PredictionRow, bootstrap_by_specimen, summarize_predictions


def known_rows() -> list[PredictionRow]:
    return [
        PredictionRow(
            sample_id="0",
            specimen_id="0",
            truth="good",
            decision="pass",
            score=0.01,
            binary_fail=False,
        ),
        PredictionRow(
            sample_id="1",
            specimen_id="1",
            truth="good",
            decision="fail",
            score=0.9,
            binary_fail=True,
        ),
        PredictionRow(
            sample_id="2",
            specimen_id="2",
            truth="defect",
            decision="fail",
            score=0.8,
            binary_fail=True,
        ),
        PredictionRow(
            sample_id="3",
            specimen_id="3",
            truth="defect",
            decision="review",
            score=0.3,
            binary_fail=False,
        ),
    ]


def test_binary_and_operational_denominators() -> None:
    metrics = summarize_predictions(known_rows())
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.false_reject_rate == 0.5
    assert metrics.missed_defect_rate == 0.5
    assert metrics.defect_pass_rate == 0
    assert metrics.review_burden == 0.25
    assert metrics.localization_iou is None
    assert bootstrap_by_specimen(known_rows()).intervals is None


def test_undefined_and_ambiguous_are_explicit() -> None:
    row = PredictionRow(
        sample_id="amb",
        specimen_id="one",
        truth="ambiguous",
        decision="review",
        score=None,
        binary_fail=False,
    )
    metrics = summarize_predictions([row])
    assert metrics.precision is None and metrics.recall is None
    assert metrics.labelled_count == 0 and metrics.ambiguous_count == 1
    assert metrics.review_burden == 1
