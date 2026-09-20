from __future__ import annotations

from pathlib import Path

import astropy.units as u
import numpy as np
import pytest

from lambert_lab.data import load_figure10_spectrum, load_figure9_wave
from lambert_lab.spectral import (
    legacy_frequency_grid,
    legacy_raw_power,
    local_maxima,
    lomb_scargle_on_grid,
    monte_carlo_periodogram,
    spectral_resolution,
    uniform_resample,
)


ROOT = Path(__file__).resolve().parents[1]
FREQUENCY_UNIT = u.kpc * u.km / u.s

pytestmark = pytest.mark.requires_lambert_release


def released_arrays() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    wave = load_figure9_wave(ROOT)
    return (
        wave.lz.to_value(FREQUENCY_UNIT),
        wave.vr.to_value(u.km / u.s),
        wave.vr_uncertainty.to_value(u.km / u.s),
    )


def test_figure9_rows_units_and_sampling() -> None:
    wave = load_figure9_wave(ROOT)
    assert len(wave.lz) == 70
    assert wave.lz.unit == FREQUENCY_UNIT
    assert wave.vr.unit == u.km / u.s
    assert wave.vr_uncertainty.unit == u.km / u.s
    lz = wave.lz.to_value(FREQUENCY_UNIT)
    assert np.allclose(np.diff(lz), np.diff(lz)[0], rtol=1e-12)
    assert not np.allclose(np.diff(1 / lz), np.diff(1 / lz)[0], rtol=1e-3, atol=0)


def test_figure10_order_and_forensic_fingerprint() -> None:
    lz, vr, _ = released_arrays()
    released = load_figure10_spectrum(ROOT)
    assert len(released.frequency) == 35
    assert released.power.shape == (35,)
    assert released.power_spread.shape == (35,)
    assert np.all(np.diff(released.frequency.value) < 0)
    np.testing.assert_allclose(
        legacy_frequency_grid(1 / lz),
        released.frequency.to_value(FREQUENCY_UNIT),
        rtol=1e-12,
        atol=1e-9,
    )
    correlation = np.corrcoef(legacy_raw_power(vr), released.power)[0, 1]
    assert correlation > 0.999


def test_uniform_x_mc_is_deterministic_and_support_preserving() -> None:
    lz, vr, uncertainty = released_arrays()
    x = 1 / lz
    grid, _ = uniform_resample(x, vr, sample_count=70)
    assert grid[0] == np.min(x)
    assert grid[-1] == np.max(x)
    assert np.allclose(np.diff(grid), np.diff(grid)[0], rtol=1e-12)
    first = monte_carlo_periodogram(x, vr, uncertainty, realizations=12, seed=20260920)
    second = monte_carlo_periodogram(x, vr, uncertainty, realizations=12, seed=20260920)
    assert first.realization_power.shape == (12, 35)
    assert first.median_power.shape == first.frequency.shape == (35,)
    np.testing.assert_array_equal(first.realization_power, second.realization_power)


def test_lomb_scargle_and_resolution_diagnostics() -> None:
    lz, vr, uncertainty = released_arrays()
    x = 1 / lz
    frequencies = np.linspace(771.428571, 27000.0, 300)
    weighted = lomb_scargle_on_grid(x, vr, uncertainty, frequencies)
    unweighted = lomb_scargle_on_grid(x, vr, None, frequencies)
    assert weighted.shape == unweighted.shape == frequencies.shape
    assert np.all(np.isfinite(weighted))
    assert np.all(np.isfinite(unweighted))
    span, resolution, cycles = spectral_resolution(x, np.array([1313.0, 5878.6]))
    np.testing.assert_allclose(span, 0.00044230769230769226, rtol=1e-12)
    np.testing.assert_allclose(resolution, 2260.8695652173915, rtol=1e-12)
    np.testing.assert_allclose(cycles, [0.58075, 2.60015], rtol=1e-10)


def test_local_maxima_excludes_boundary_bins() -> None:
    power = np.array([9.0, 2.0, 5.0, 1.0, 7.0])
    np.testing.assert_array_equal(local_maxima(power), np.array([2]))
    assert local_maxima(np.array([3.0])).size == 0
