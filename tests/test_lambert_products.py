from __future__ import annotations

from pathlib import Path

import astropy.units as u
import numpy as np
import pytest

from lambert_lab.data import load_figure13_stars, load_released_image
from lambert_lab.plotting import constant_lz_curves, zero_centered_norm


ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.requires_lambert_release


def test_fixed_image_loading_preserves_inventory_orientation() -> None:
    product = load_released_image(ROOT, "lb_VR_fig5.fits")
    assert product.data.shape == (12, 42)
    assert product.extent == (150, 220, 20, 40)
    assert product.horizontal_axis["name"] == "l"
    assert product.vertical_axis["name"] == "b"
    assert product.value_unit == "km / s"
    assert product.value_kind == "binned median"


def test_relevant_fixed_product_shapes_and_extents() -> None:
    expected = {
        "XY_overdensity_fig6.fits": ((16, 28), (8, 23, -8, 8)),
        "XY_VR_fig6.fits": ((16, 28), (8, 23, -8, 8)),
        "XY_VZ_fig6.fits": ((16, 28), (8, 23, -8, 8)),
        "RVphi_count_fig8.fits": ((32, 30), (9, 24, 140, 270)),
    }
    for filename, (shape, extent) in expected.items():
        product = load_released_image(ROOT, filename)
        assert product.data.shape == shape
        assert product.extent == extent


def test_figure13_columns_units_and_deterministic_sign_split() -> None:
    stars = load_figure13_stars(ROOT)
    assert len(stars) == 7708
    assert stars.colnames == ["b", "l", "V_Z", "V_R"]
    assert stars["b"].unit == u.deg
    assert stars["V_R"].unit == u.km / u.s
    published_longitudes = (stars["l"] >= 150 * u.deg) & (stars["l"] < 200 * u.deg)
    outward = published_longitudes & (stars["V_R"] > 0 * u.km / u.s)
    inward = published_longitudes & (stars["V_R"] < 0 * u.km / u.s)
    assert (int(np.sum(published_longitudes)), int(np.sum(outward)), int(np.sum(inward))) == (
        6047,
        2769,
        3278,
    )
    assert not np.any(stars["V_R"] == 0 * u.km / u.s)


def test_zero_centered_velocity_norm_and_lz_guides() -> None:
    norm = zero_centered_norm(np.array([-4.0, 1.0, 3.0, np.nan]))
    assert norm.vmin == -4.0
    assert norm.vcenter == 0.0
    assert norm.vmax == 4.0
    assert norm(0.0) == 0.5
    curves = constant_lz_curves(np.array([10.0, 20.0]), [2000.0])
    assert np.allclose(curves[2000.0], [200.0, 100.0])
