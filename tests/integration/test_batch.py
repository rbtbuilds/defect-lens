from defect_lens.batch import BatchSummary


def test_batch_failure_exit_is_explicit() -> None:
    assert BatchSummary(submitted=2, succeeded=1, failed=1).exit_code == 4
    assert BatchSummary(submitted=2, succeeded=2, failed=0).exit_code == 0
