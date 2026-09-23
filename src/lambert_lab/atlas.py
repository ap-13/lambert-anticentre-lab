"""Deterministic teaching geometry for Notebook 01 (never survey data)."""

from __future__ import annotations

import astropy.units as u
import numpy as np
from astropy.coordinates import Angle, SkyCoord
from astropy.table import QTable

from .coordinates import disc_azimuth, galactocentric_frame


TOY_NAMES = ("A centre", "B anti", "C l90", "D l270", "E above", "F near", "G far", "H outer")
TOY_COLORS = ("#e69f00", "#56b4e9", "#009e73", "#cc79a7", "#d55e00", "#0072b2", "#7b3294", "#a6761d")


def toy_atlas() -> QTable:
    """Eight labelled directions/depths, transformed by the project frame."""

    l = np.array([0, 180, 90, 270, 150, 175, 175, 190]) * u.deg
    b = np.array([0, 0, 0, 0, 35, 28, 28, 25]) * u.deg
    d = np.array([4, 3, 3, 3, 5, 4, 10, 14]) * u.kpc
    sky = SkyCoord(l=l, b=b, distance=d, frame="galactic")
    gc = sky.transform_to(galactocentric_frame())
    result = QTable()
    result["name"] = TOY_NAMES
    result["color"] = TOY_COLORS
    result["l"], result["b"], result["d"] = l, b, d
    result["x"], result["y"], result["z"] = gc.x.to(u.kpc), gc.y.to(u.kpc), gc.z.to(u.kpc)
    result["R"] = np.hypot(gc.x, gc.y).to(u.kpc)
    result["phi"] = disc_azimuth(gc.x, gc.y)
    return result


def sky_display_longitude(l: u.Quantity) -> np.ndarray:
    """mw-plot all-sky horizontal coordinate: minus wrapped Galactic l, degrees."""

    return Angle(-l).wrap_at(180 * u.deg).to_value(u.deg)


def faceon_display_xy(x: u.Quantity, y: u.Quantity) -> tuple[np.ndarray, np.ndarray]:
    """Map project Cartesian positions onto mw-plot's Sun-at-right illustration.

    mw-plot's face-on background has the Sun at (+r0, 0); our Astropy frame
    has the Sun at (-r0, 0). This is a display reflection, not a coordinate
    transform used for any scientific quantity.
    """

    return -x.to_value(u.kpc), y.to_value(u.kpc)
