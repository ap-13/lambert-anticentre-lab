"""Infrastructure reserved for the educational dynamics notebook."""

from __future__ import annotations

import numpy as np
from numpy.random import Generator


def seeded_rng(seed: int) -> Generator:
    """Return an explicit reproducible random-number generator."""

    return np.random.default_rng(seed)

