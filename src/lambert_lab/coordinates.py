"""Coordinate-convention helpers.

Full sky-to-Galactocentric transformations belong to Task 3. The small helper
here makes the local cylindrical velocity sign convention explicit enough to
test before that work begins. Its convention must later be reconciled with the
chosen Astropy frame and Lambert's documented definitions.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def cylindrical_velocity_components(
    x: ArrayLike,
    y: ArrayLike,
    velocity_x: ArrayLike,
    velocity_y: ArrayLike,
    velocity_z: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Return ``(v_r, v_phi, v_z)`` for a right-handed Cartesian basis.

    Positive ``v_r`` points away from the origin. Positive ``v_phi`` points in
    the direction of increasing ``phi = atan2(y, x)``. No solar parameters or
    Lambert-specific convention are implied.
    """

    x_array, y_array, vx_array, vy_array, vz_array = np.broadcast_arrays(
        np.asarray(x, dtype=float),
        np.asarray(y, dtype=float),
        np.asarray(velocity_x, dtype=float),
        np.asarray(velocity_y, dtype=float),
        np.asarray(velocity_z, dtype=float),
    )
    radius = np.hypot(x_array, y_array)
    if np.any(radius == 0):
        raise ValueError("cylindrical velocity is undefined at R = 0")

    radial = (x_array * vx_array + y_array * vy_array) / radius
    azimuthal = (-y_array * vx_array + x_array * vy_array) / radius
    return radial, azimuthal, vz_array.copy()

