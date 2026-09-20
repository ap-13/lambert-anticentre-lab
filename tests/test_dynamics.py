import numpy as np

from lambert_lab.dynamics import seeded_rng


def test_explicit_seed_is_reproducible() -> None:
    first = seeded_rng(2026).normal(size=8)
    second = seeded_rng(2026).normal(size=8)
    np.testing.assert_array_equal(first, second)

