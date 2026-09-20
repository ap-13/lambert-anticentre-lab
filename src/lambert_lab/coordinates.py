"""Explicit Galactocentric conventions and phase-space transformations."""

from __future__ import annotations

import astropy.units as u
import numpy as np
from astropy.coordinates import Galactocentric, SkyCoord
from astropy.table import QTable, Table
from numpy.typing import ArrayLike, NDArray

# Lambert et al. (2026), Section 2.3. These are explicit so future Astropy
# default changes cannot silently change notebook results.
GALCEN_DISTANCE = 8.277 * u.kpc
Z_SUN = 20.8 * u.pc
GALCEN_V_SUN = u.Quantity([11.1, 248.5, 7.25], u.km / u.s)
ROLL = 0 * u.deg


def galactocentric_frame() -> Galactocentric:
    """Return the project's explicitly parameterized Astropy frame."""

    return Galactocentric(
        galcen_distance=GALCEN_DISTANCE,
        z_sun=Z_SUN,
        galcen_v_sun=GALCEN_V_SUN,
        roll=ROLL,
    )


def cylindrical_velocity_components(
    x: ArrayLike,
    y: ArrayLike,
    velocity_x: ArrayLike,
    velocity_y: ArrayLike,
    velocity_z: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Return outward, disc-positive, and north-positive velocities.

    Inputs use Astropy's right-handed Galactocentric Cartesian basis: the Sun
    lies at negative ``x`` and Galactic rotation near the Sun is positive
    ``y``. ``v_r`` is positive away from the Galactic centre. ``v_phi`` is
    positive in the Milky Way disc's rotation direction and is thus the
    negative of the component along increasing ``atan2(y, x)``. ``v_z`` is
    positive toward the North Galactic Pole. This matches Lambert's positive
    disc ``V_phi`` and ``L_Z = R V_phi`` meanings.
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
    disc_azimuthal = (y_array * vx_array - x_array * vy_array) / radius
    return radial, disc_azimuthal, vz_array.copy()


def disc_azimuth(x: u.Quantity, y: u.Quantity) -> u.Quantity:
    """Return disc-positive azimuth, zero on the Galactic-centre--Sun ray."""

    return np.arctan2(y, -x).to(u.deg)


def transform_observables(table: Table) -> QTable:
    """Transform the canonical teaching sample to Galactic phase space."""

    sky = SkyCoord(
        ra=u.Quantity(table["ra"]),
        dec=u.Quantity(table["dec"]),
        distance=u.Quantity(table["distance"]),
        pm_ra_cosdec=u.Quantity(table["pmra"]),
        pm_dec=u.Quantity(table["pmdec"]),
        radial_velocity=u.Quantity(table["radial_velocity"]),
        frame="icrs",
    )
    galactic = sky.galactic
    gc = sky.transform_to(galactocentric_frame())
    radius = np.hypot(gc.x, gc.y)
    v_r, v_phi, v_z = cylindrical_velocity_components(
        gc.x.to_value(u.kpc),
        gc.y.to_value(u.kpc),
        gc.v_x.to_value(u.km / u.s),
        gc.v_y.to_value(u.km / u.s),
        gc.v_z.to_value(u.km / u.s),
    )

    result = QTable(table, copy=True)
    result["l"] = galactic.l.to(u.deg)
    result["b"] = galactic.b.to(u.deg)
    result["x"] = gc.x.to(u.kpc)
    result["y"] = gc.y.to(u.kpc)
    result["z"] = gc.z.to(u.kpc)
    result["R"] = radius.to(u.kpc)
    result["phi"] = disc_azimuth(gc.x, gc.y)
    result["V_R"] = v_r * u.km / u.s
    result["V_phi"] = v_phi * u.km / u.s
    result["V_Z"] = v_z * u.km / u.s
    result["L_Z"] = (result["R"] * result["V_phi"]).to(u.kpc * u.km / u.s)
    return result
