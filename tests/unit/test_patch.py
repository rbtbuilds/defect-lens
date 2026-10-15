import numpy as np

from defect_lens.inference.patch import chunked_nearest, reservoir_bank


def test_block_distances_match_direct_calculation() -> None:
    rng = np.random.default_rng(17)
    query = rng.normal(size=(260, 128)).astype(np.float32)
    bank = rng.normal(size=(530, 128)).astype(np.float32)
    expected = np.linalg.norm(query[:, None] - bank[None, :], axis=2).min(axis=1)
    assert np.allclose(chunked_nearest(query, bank), expected, atol=1e-5)


def test_reservoir_is_seeded_and_bounded() -> None:
    values = np.random.default_rng(9).normal(size=(5000, 128)).astype(np.float32)
    a = reservoir_bank([values], 17)
    assert a.shape == (4096, 128)
    assert np.array_equal(a, reservoir_bank([values], 17))
    assert not np.array_equal(a, reservoir_bank([values], 18))
