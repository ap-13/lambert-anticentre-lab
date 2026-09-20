from __future__ import annotations

import numpy as np
import pytest

from lambert_lab.coordinates import cylindrical_velocity_components


def test_cylindrical_velocity_sign_sanity() -> None:
    radial, azimuthal, vertical = cylindrical_velocity_components(
        x=[2.0, 2.0],
        y=[0.0, 0.0],
        velocity_x=[3.0, -3.0],
        velocity_y=[4.0, -4.0],
        velocity_z=[5.0, -5.0],
    )
    np.testing.assert_allclose(radial, [3.0, -3.0])
    np.testing.assert_allclose(azimuthal, [4.0, -4.0])
    np.testing.assert_allclose(vertical, [5.0, -5.0])


def test_cylindrical_velocity_rejects_origin() -> None:
    with pytest.raises(ValueError, match="R = 0"):
        cylindrical_velocity_components(0, 0, 1, 1, 1)

