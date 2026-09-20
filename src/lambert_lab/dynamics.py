"""Transparent toy dynamics and winding-clock conversions for Notebook 3."""

from __future__ import annotations

import numpy as np
import astropy.units as u
from numpy.random import Generator

PROJECT_SEED = 20260920


def seeded_rng(seed: int) -> Generator:
    """Return an explicit reproducible random-number generator."""

    return np.random.default_rng(seed)


def angular_frequency(radius: u.Quantity, circular_speed: u.Quantity) -> u.Quantity:
    """Circular angular frequency ``Omega=V_c/R`` with explicit units."""

    radius = u.Quantity(radius).to(u.kpc)
    circular_speed = u.Quantity(circular_speed).to(u.km / u.s)
    if np.any(radius <= 0 * u.kpc) or np.any(circular_speed <= 0 * u.km / u.s):
        raise ValueError("radius and circular_speed must be positive")
    return (circular_speed / radius).to(1 / u.Gyr)


def epicyclic_frequency(omega: u.Quantity, n: float = 0.0) -> u.Quantity:
    """Power-law epicyclic frequency ``kappa=sqrt(2(n+1))*Omega``."""

    if n <= -1:
        raise ValueError("n must be greater than -1")
    return np.sqrt(2 * (n + 1)) * u.Quantity(omega)


def tidal_pattern_speed(omega: u.Quantity, n: float = 0.0) -> u.Quantity:
    """Illustrative two-arm tidal-pattern rate ``Omega-kappa/2``."""

    return u.Quantity(omega) - epicyclic_frequency(omega, n=n) / 2


def transformed_angular_momentum(lz: u.Quantity, n: float = 0.0) -> u.Quantity:
    """Return ``x=L_Z**((n-1)/(n+1))`` for the Antoja coordinate."""

    if n <= -1:
        raise ValueError("n must be greater than -1")
    lz = u.Quantity(lz).to(u.kpc * u.km / u.s)
    if np.any(lz <= 0 * lz.unit):
        raise ValueError("L_Z must be positive")
    exponent = (n - 1) / (n + 1)
    return lz**exponent


def toy_radial_velocity(
    guiding_radius: u.Quantity,
    elapsed_time: u.Quantity,
    *,
    circular_speed: u.Quantity = 239.26 * u.km / u.s,
    amplitude: u.Quantity = 1.0 * u.one,
    observing_azimuth: u.Quantity = 0.0 * u.rad,
    initial_phase: u.Quantity = 0.0 * u.rad,
    n: float = 0.0,
) -> u.Quantity:
    """Illustrative signed m=2 wave at one observing azimuth.

    The amplitude and phase are pedagogical choices, not a fit to the Milky
    Way. Differential winding enters only through ``Omega-kappa/2``.
    """

    radius = u.Quantity(guiding_radius).to(u.kpc)
    time = u.Quantity(elapsed_time).to(u.Gyr)
    omega = angular_frequency(radius, circular_speed)
    pattern = tidal_pattern_speed(omega, n=n)
    phase = 2 * (
        u.Quantity(observing_azimuth).to_value(u.rad)
        - (pattern * time).to_value(u.one)
    ) + u.Quantity(initial_phase).to_value(u.rad)
    return u.Quantity(amplitude) * np.sin(phase)


def winding_time_flat_curve(
    frequency: u.Quantity,
    *,
    circular_speed: u.Quantity = 239.26 * u.km / u.s,
) -> u.Quantity:
    """Convert an n=0 Fourier frequency to time using Lambert's equation.

    ``frequency`` is reciprocal to ``x=1/L_Z`` and therefore has angular-
    momentum units. The conceptual intermediate is ``Delta x=1/f``.
    """

    frequency = u.Quantity(frequency).to(u.kpc * u.km / u.s)
    circular_speed = u.Quantity(circular_speed).to(u.km / u.s)
    if np.any(frequency <= 0 * frequency.unit):
        raise ValueError("frequency must be positive")
    delta_x = 1 / frequency
    coefficient = 1 - np.sqrt(2) / 2
    time = np.pi / (coefficient * circular_speed**2 * delta_x)
    return time.to(u.Gyr)


def winding_time_uncertainty_flat_curve(
    frequency: u.Quantity,
    frequency_uncertainty: u.Quantity,
    *,
    circular_speed: u.Quantity = 239.26 * u.km / u.s,
) -> tuple[u.Quantity, u.Quantity]:
    """Return n=0 time and first-order uncertainty from a frequency width."""

    frequency = u.Quantity(frequency).to(u.kpc * u.km / u.s)
    uncertainty = u.Quantity(frequency_uncertainty).to(frequency.unit)
    if np.any(uncertainty < 0 * uncertainty.unit):
        raise ValueError("frequency uncertainty must be non-negative")
    time = winding_time_flat_curve(frequency, circular_speed=circular_speed)
    return time, (time * uncertainty / frequency).to(u.Gyr)
