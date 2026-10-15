from defect_lens.inference.calibration import Calibration, LabelledScore, calibrate, decide


def test_decision_boundaries_and_quality_review() -> None:
    config = Calibration(
        low=0.05,
        high=0.2,
        pixel_threshold=0.1,
        heatmap_display_max=1,
        validation_manifest_sha="a" * 64,
    )
    assert decide(0.05, config, ()) == "pass"
    assert decide(0.2, config, ()) == "fail"
    assert decide(0.01, config, ("blur",)) == "review"
    trained = calibrate(
        [LabelledScore("g", "one", "good", 0.01), LabelledScore("d", "two", "defect", 0.4)],
        "b" * 64,
    )
    assert 0.01 < trained.high < 0.4
