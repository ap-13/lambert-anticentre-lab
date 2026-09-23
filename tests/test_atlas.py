"""Scientific geometry and mw-plot display checks for Notebook 01."""

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from mw_plot import MWFaceOn, MWSkyMap

from lambert_lab.atlas import faceon_display_xy, sky_display_longitude, toy_atlas
from lambert_lab.coordinates import GALCEN_DISTANCE, galactocentric_frame


def test_toy_radius_and_anticentre_depth() -> None:
    toy = toy_atlas()
    assert len(toy) == 8
    assert u.allclose(toy['R'], np.hypot(toy['x'], toy['y']))
    assert u.isclose(toy['l'][5], toy['l'][6]) and u.isclose(toy['b'][5], toy['b'][6])
    assert toy['d'][6] > toy['d'][5] and toy['R'][6] > toy['R'][5]
    anti = SkyCoord(l=180*u.deg, b=0*u.deg,
                    distance=[1, 4, 10]*u.kpc, frame='galactic').transform_to(galactocentric_frame())
    assert np.all(np.diff(np.hypot(anti.x, anti.y).to_value(u.kpc)) > 0)


def test_mw_plot_sky_orientation_uses_icrs_inputs() -> None:
    sky = MWSkyMap(background='optical')
    gal = SkyCoord(l=[0,90,180,270]*u.deg, b=[0,0,0,0]*u.deg, frame='galactic')
    rendered, latitude = sky.radec_unit_check(gal.icrs.ra, gal.icrs.dec)
    np.testing.assert_allclose(rendered, sky_display_longitude(gal.l), atol=1e-9)
    np.testing.assert_allclose(latitude, 0, atol=1e-9)
    np.testing.assert_allclose(rendered[[0,1,3]], [0,-90,90], atol=1e-9)


def test_mw_plot_faceon_display_reflection() -> None:
    background = MWFaceOn(coord='galactocentric', r0=GALCEN_DISTANCE, radius=20*u.kpc)
    assert u.isclose(background.r0, GALCEN_DISTANCE)
    assert background._ext[0] < 0 < background._ext[1]
    frame = galactocentric_frame()
    sun = SkyCoord(l=0*u.deg,b=0*u.deg,distance=0*u.kpc,frame='galactic').transform_to(frame)
    anti = SkyCoord(l=180*u.deg,b=0*u.deg,distance=4*u.kpc,frame='galactic').transform_to(frame)
    ninety = SkyCoord(l=90*u.deg,b=0*u.deg,distance=4*u.kpc,frame='galactic').transform_to(frame)
    sx, sy = faceon_display_xy(sun.x, sun.y)
    ax, ay = faceon_display_xy(anti.x, anti.y)
    nx, ny = faceon_display_xy(ninety.x, ninety.y)
    assert np.isclose(sx, GALCEN_DISTANCE.to_value(u.kpc), atol=1e-3)
    assert ax > sx and nx > 0 and ny > sy
    assert np.isclose(ay, sy, atol=1e-3)
