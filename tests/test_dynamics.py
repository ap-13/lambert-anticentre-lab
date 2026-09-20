import numpy as np
import astropy.units as u

from lambert_lab.dynamics import (
    angular_frequency,
    epicyclic_frequency,
    seeded_rng,
    tidal_pattern_speed,
    toy_radial_velocity,
    transformed_angular_momentum,
    winding_time_uncertainty_flat_curve,
)


def test_explicit_seed_is_reproducible() -> None:
    first = seeded_rng(2026).normal(size=8)
    second = seeded_rng(2026).normal(size=8)
    np.testing.assert_array_equal(first, second)


def test_flat_curve_epicycle_and_pattern_speed() -> None:
    omega = angular_frequency(np.array([8.0, 16.0]) * u.kpc, 240 * u.km / u.s)
    kappa = epicyclic_frequency(omega, n=0)
    np.testing.assert_allclose(kappa.value, np.sqrt(2) * omega.value)
    np.testing.assert_allclose(
        tidal_pattern_speed(omega, n=0).value,
        (omega - kappa / 2).value,
    )


def test_toy_wave_winds_more_with_elapsed_time() -> None:
    radius = np.linspace(8, 20, 500) * u.kpc
    early = toy_radial_velocity(radius, 0.2 * u.Gyr).value
    late = toy_radial_velocity(radius, 0.9 * u.Gyr).value
    early_crossings = np.count_nonzero(np.diff(np.signbit(early)))
    late_crossings = np.count_nonzero(np.diff(np.signbit(late)))
    assert late_crossings > early_crossings


def test_flat_curve_transform_is_unit_consistent_with_reciprocal_lz() -> None:
    lz = np.array([1500.0, 3200.0]) * u.kpc * u.km / u.s
    transformed = transformed_angular_momentum(lz, n=0)
    assert transformed.unit.is_equivalent(1 / (u.kpc * u.km / u.s))
    assert u.allclose(transformed, 1 / lz, rtol=1e-14)


def test_published_flat_curve_timing_and_uncertainties() -> None:
    unit = u.kpc * u.km / u.s
    time1, error1 = winding_time_uncertainty_flat_curve(1313.0 * unit, 477.2 * unit)
    time2, error2 = winding_time_uncertainty_flat_curve(5878.6 * unit, 1471.9 * unit)
    np.testing.assert_allclose(time1.to_value(u.Gyr), 0.24055, rtol=2e-4)
    np.testing.assert_allclose(error1.to_value(u.Gyr), 0.08743, rtol=2e-4)
    np.testing.assert_allclose(time2.to_value(u.Gyr), 1.07701, rtol=2e-4)
    np.testing.assert_allclose(error2.to_value(u.Gyr), 0.26967, rtol=2e-4)
    assert round(time1.to_value(u.Gyr), 2) == 0.24
    assert round(time2.to_value(u.Gyr), 1) == 1.1
