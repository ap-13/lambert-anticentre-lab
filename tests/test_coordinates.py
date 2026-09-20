from __future__ import annotations

import numpy as np
import pytest
import astropy.units as u
from astropy.coordinates import SkyCoord

from lambert_lab.coordinates import (
    GALCEN_DISTANCE,
    GALCEN_V_SUN,
    Z_SUN,
    cylindrical_velocity_components,
    disc_azimuth,
    galactocentric_frame,
)


def test_cylindrical_velocity_sign_sanity() -> None:
    radial, azimuthal, vertical = cylindrical_velocity_components(
        x=[2.0, 2.0],
        y=[0.0, 0.0],
        velocity_x=[3.0, -3.0],
        velocity_y=[4.0, -4.0],
        velocity_z=[5.0, -5.0],
    )
    np.testing.assert_allclose(radial, [3.0, -3.0])
    np.testing.assert_allclose(azimuthal, [-4.0, 4.0])
    np.testing.assert_allclose(vertical, [5.0, -5.0])


def test_cylindrical_velocity_rejects_origin() -> None:
    with pytest.raises(ValueError, match="R = 0"):
        cylindrical_velocity_components(0, 0, 1, 1, 1)


def test_project_frame_parameters_are_explicit() -> None:
    frame = galactocentric_frame()
    assert u.isclose(frame.galcen_distance, GALCEN_DISTANCE)
    assert u.isclose(frame.z_sun, Z_SUN)
    assert u.allclose(frame.galcen_v_sun.xyz, GALCEN_V_SUN)


def test_analytic_anticentre_geometry_and_astropy_round_trip() -> None:
    frame = galactocentric_frame()
    synthetic = SkyCoord(
        x=-10 * u.kpc,
        y=0 * u.kpc,
        z=1 * u.kpc,
        v_x=-30 * u.km / u.s,
        v_y=220 * u.km / u.s,
        v_z=15 * u.km / u.s,
        frame=frame,
        representation_type="cartesian",
        differential_type="cartesian",
    )
    observed = synthetic.transform_to("icrs")
    recovered = observed.transform_to(frame)
    radial, azimuthal, vertical = cylindrical_velocity_components(
        recovered.x.to_value(u.kpc),
        recovered.y.to_value(u.kpc),
        recovered.v_x.to_value(u.km / u.s),
        recovered.v_y.to_value(u.km / u.s),
        recovered.v_z.to_value(u.km / u.s),
    )
    np.testing.assert_allclose([radial, azimuthal, vertical], [30, 220, 15], atol=1e-9)
    assert u.isclose(disc_azimuth(recovered.x, recovered.y), 0 * u.deg, atol=1e-10 * u.deg)
