from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import astropy.units as u
import numpy as np
import pytest

from lambert_lab.data import (
    load_figure13_stars,
    load_figure9_wave,
    load_released_image,
)
from lambert_lab.plotting import (
    binned_median_visual_guide,
    display_pixel_centers,
    positive_run_containing_maximum,
    raw_column_peak,
    released_pixel_profile,
    robust_symmetric_limit,
    toy_cycle_spectrum,
    velocity_sign_categories,
    zero_centered_norm,
)


ROOT = Path(__file__).resolve().parents[1]


def test_nominal_centers_and_figure5_strip_are_deterministic() -> None:
    vr = load_released_image(ROOT, "lb_VR_fig5.fits")
    vz = load_released_image(ROOT, "lb_VZ_fig5.fits")
    longitude, latitude = display_pixel_centers(vr)
    np.testing.assert_allclose(longitude[[15, 20]], [175.8333333333, 184.1666666667])
    np.testing.assert_allclose(latitude[[0, -1]], [20.8333333333, 39.1666666667])
    coordinate_vr, profile_vr = released_pixel_profile(
        vr, collapse_axis=1, indices=range(15, 21)
    )
    coordinate_vz, profile_vz = released_pixel_profile(
        vz, collapse_axis=1, indices=range(15, 21)
    )
    np.testing.assert_array_equal(coordinate_vr, coordinate_vz)
    assert profile_vr.shape == profile_vz.shape == (12,)
    assert np.all(np.isfinite(profile_vr)) and np.all(np.isfinite(profile_vz))


def test_sign_categories_preserve_missing_and_zero_values() -> None:
    vr = np.array([[-1.0, -1.0, 1.0], [1.0, 0.0, np.nan]])
    vz = np.array([[-1.0, 1.0, -1.0], [1.0, 2.0, 1.0]])
    categories = velocity_sign_categories(vr, vz)
    np.testing.assert_array_equal(categories.data, [[0, 1, 2], [3, 0, 0]])
    np.testing.assert_array_equal(categories.mask, [[False, False, False], [False, True, True]])


def test_figure6_products_use_the_identical_central_row_selection() -> None:
    names = ["XY_overdensity_fig6.fits", "XY_VR_fig6.fits", "XY_VZ_fig6.fits"]
    profiles = []
    for name in names:
        product = load_released_image(ROOT, name)
        coordinate, profile = released_pixel_profile(product, collapse_axis=0, indices=[7, 8])
        profiles.append(profile)
        np.testing.assert_allclose(coordinate[[0, -1]], [8.2678571429, 22.7321428571])
    assert all(profile.shape == (28,) for profile in profiles)
    start, stop = positive_run_containing_maximum(profiles[0])
    assert (start, stop) == (14, 18)
    assert start <= int(np.nanargmax(profiles[0])) < stop
    assert np.all(profiles[0][start:stop] > 0)
    assert profiles[0][start - 1] <= 0 and profiles[0][stop] <= 0


def test_figure8_predeclared_columns_have_guarded_interior_peaks() -> None:
    product = load_released_image(ROOT, "RVphi_count_fig8.fits")
    x, _ = display_pixel_centers(product)
    columns = [3, 9, 15, 21]
    np.testing.assert_allclose(x[columns], [10.75, 13.75, 16.75, 19.75])
    peaks = [raw_column_peak(product, column) for column in columns]
    np.testing.assert_allclose([peak[1] for peak in peaks], [235.46875, 219.21875, 219.21875, 194.84375])
    with pytest.raises(ValueError, match="insufficient"):
        raw_column_peak(product, 22)
    boundary_data = np.ones_like(product.data)
    boundary_data[0, 3] = 2.0
    with pytest.raises(ValueError, match="boundary"):
        raw_column_peak(replace(product, data=boundary_data), 3)


def test_figure13_central_slice_and_visual_guide_threshold() -> None:
    stars = load_figure13_stars(ROOT)
    central = (stars["l"] >= 170 * u.deg) & (stars["l"] < 180 * u.deg)
    outward = central & (stars["V_R"] > 0 * u.km / u.s)
    inward = central & (stars["V_R"] < 0 * u.km / u.s)
    assert (int(central.sum()), int(outward.sum()), int(inward.sum())) == (1228, 572, 656)
    outward_guide = binned_median_visual_guide(
        stars["b"][outward].to_value(u.deg),
        stars["V_Z"][outward].to_value(u.km / u.s),
        np.arange(20, 42, 2),
        min_count=20,
    )
    inward_guide = binned_median_visual_guide(
        stars["b"][inward].to_value(u.deg),
        stars["V_Z"][inward].to_value(u.km / u.s),
        np.arange(20, 42, 2),
        min_count=20,
    )
    np.testing.assert_array_equal(
        outward_guide.counts, [73, 72, 76, 85, 63, 59, 54, 55, 23, 12]
    )
    np.testing.assert_array_equal(outward_guide.included, [True] * 9 + [False])
    np.testing.assert_array_equal(outward_guide.centers, inward_guide.centers)
    assert inward_guide.counts.shape == outward_guide.counts.shape
    assert np.all(inward_guide.included == (inward_guide.counts >= 20))

    displayed_vr = stars["V_R"][central].to_value(u.km / u.s)
    limit = robust_symmetric_limit(displayed_vr, percentile=95)
    norm = zero_centered_norm(displayed_vr, limit=limit)
    assert limit > 0
    assert norm.vmin == -limit and norm.vcenter == 0 and norm.vmax == limit
    assert (int(central.sum()), int(outward.sum()), int(inward.sum())) == (1228, 572, 656)


def test_uniform_lz_becomes_nonuniform_inverse_lz() -> None:
    wave = load_figure9_wave(ROOT)
    lz = wave.lz.to_value(u.kpc * u.km / u.s)
    assert np.allclose(np.diff(lz), np.diff(lz)[0], rtol=1e-12)
    assert not np.allclose(np.diff(1 / lz), np.diff(1 / lz)[0], rtol=1e-3, atol=0)


@pytest.mark.parametrize("cycles", [1.0, 3.0, 6.0])
def test_integer_cycle_toy_spectrum_peaks_at_input_frequency(cycles: float) -> None:
    _, _, frequency, power = toy_cycle_spectrum(cycles)
    assert frequency[np.argmax(power)] == cycles


def test_noninteger_cycle_toy_has_leakage() -> None:
    _, _, frequency, power = toy_cycle_spectrum(2.6)
    assert frequency[np.argmax(power)] == 3.0
    assert np.count_nonzero(power > 0.01 * power.max()) > 1
