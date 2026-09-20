"""Declared spectral estimators and forensic diagnostics for Notebook 3."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from astropy.timeseries import LombScargle


@dataclass(frozen=True)
class MonteCarloSpectrum:
    """Median and central 68-percent interval for declared MC spectra."""

    frequency: np.ndarray
    central_power: np.ndarray
    median_power: np.ndarray
    lower_power: np.ndarray
    upper_power: np.ndarray
    uniform_x: np.ndarray
    realization_power: np.ndarray


def legacy_frequency_grid(x: np.ndarray) -> np.ndarray:
    """Positive legacy FFT frequencies using only ``x[1]-x[0]``.

    This intentionally fingerprints the released Figure 10 convention. It is
    not endorsed as a valid FFT for a generally nonuniform coordinate.
    """

    x = _finite_1d(x, "x")
    if x.size % 2:
        raise ValueError("legacy fingerprint expects an even sample count")
    spacing = x[1] - x[0]
    if spacing == 0:
        raise ValueError("first two x samples must differ")
    frequencies = np.fft.fftfreq(x.size, d=spacing)
    return frequencies[x.size // 2 :]


def legacy_raw_power(signal: np.ndarray) -> np.ndarray:
    """Legacy unnormalized ``|FFT(signal)|^2`` in Figure 10 ordering."""

    signal = _finite_1d(signal, "signal")
    if signal.size % 2:
        raise ValueError("legacy fingerprint expects an even sample count")
    return np.abs(np.fft.fft(signal)[signal.size // 2 :]) ** 2


def uniform_resample(
    x: np.ndarray, signal: np.ndarray, *, sample_count: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Sort and linearly interpolate onto a uniform grid over observed support."""

    x = _finite_1d(x, "x")
    signal = _finite_1d(signal, "signal")
    if x.shape != signal.shape:
        raise ValueError("x and signal must have the same shape")
    if np.unique(x).size != x.size:
        raise ValueError("x values must be unique")
    count = x.size if sample_count is None else int(sample_count)
    if count < 3:
        raise ValueError("sample_count must be at least three")
    order = np.argsort(x)
    grid = np.linspace(x[order][0], x[order][-1], count)
    return grid, np.interp(grid, x[order], signal[order])


def window_normalized_periodogram(
    uniform_x: np.ndarray,
    signal: np.ndarray,
    *,
    window: str = "hann",
) -> tuple[np.ndarray, np.ndarray]:
    """Mean-remove and return one-sided ``|FFT|^2/sum(window^2)``.

    The zero-frequency term is omitted. This is a reproducible relative-power
    convention, not a claim of a physical power spectral density.
    """

    x = _finite_1d(uniform_x, "uniform_x")
    signal = _finite_1d(signal, "signal")
    if x.shape != signal.shape:
        raise ValueError("uniform_x and signal must have the same shape")
    differences = np.diff(x)
    if not np.allclose(differences, differences[0], rtol=1e-10, atol=0):
        raise ValueError("uniform_x must be uniformly spaced")
    if window == "hann":
        weights = np.hanning(x.size)
    elif window == "rectangular":
        weights = np.ones(x.size)
    else:
        raise ValueError("window must be 'hann' or 'rectangular'")
    transformed = np.fft.rfft((signal - np.mean(signal)) * weights)
    frequency = np.fft.rfftfreq(x.size, d=differences[0])
    power = np.abs(transformed) ** 2 / np.sum(weights**2)
    return frequency[1:], power[1:]


def monte_carlo_periodogram(
    x: np.ndarray,
    signal: np.ndarray,
    uncertainty: np.ndarray,
    *,
    realizations: int = 1000,
    seed: int = 20260920,
    window: str = "hann",
) -> MonteCarloSpectrum:
    """Independent Gaussian-draw, linear-resampling MC periodogram."""

    x = _finite_1d(x, "x")
    signal = _finite_1d(signal, "signal")
    uncertainty = _finite_1d(uncertainty, "uncertainty")
    if x.shape != signal.shape or x.shape != uncertainty.shape:
        raise ValueError("x, signal, and uncertainty must have the same shape")
    if np.any(uncertainty <= 0):
        raise ValueError("uncertainties must be positive")
    if realizations < 1:
        raise ValueError("realizations must be positive")
    grid, central = uniform_resample(x, signal, sample_count=x.size)
    frequency, central_power = window_normalized_periodogram(grid, central, window=window)
    rng = np.random.default_rng(seed)
    draws = rng.normal(signal, uncertainty, size=(realizations, signal.size))
    powers = np.empty((realizations, frequency.size))
    order = np.argsort(x)
    for index, draw in enumerate(draws):
        resampled = np.interp(grid, x[order], draw[order])
        _, powers[index] = window_normalized_periodogram(grid, resampled, window=window)
    lower, median, upper = np.percentile(powers, [16, 50, 84], axis=0)
    return MonteCarloSpectrum(
        frequency=frequency,
        central_power=central_power,
        median_power=median,
        lower_power=lower,
        upper_power=upper,
        uniform_x=grid,
        realization_power=powers,
    )


def lomb_scargle_on_grid(
    x: np.ndarray,
    signal: np.ndarray,
    uncertainty: np.ndarray | None,
    frequency: np.ndarray,
) -> np.ndarray:
    """Evaluate Lomb–Scargle power on an explicit frequency grid.

    Passing ``uncertainty=None`` gives the unweighted floating-mean Astropy
    estimator. Otherwise, ``uncertainty`` supplies the per-sample scales used
    by Astropy's weighted floating-mean estimator.
    """

    x = _finite_1d(x, "x")
    signal = _finite_1d(signal, "signal")
    frequency = _finite_1d(frequency, "frequency")
    if x.shape != signal.shape:
        raise ValueError("x and signal must have the same shape")
    if np.any(frequency <= 0):
        raise ValueError("frequency must be positive")
    if uncertainty is None:
        return LombScargle(x, signal).power(frequency)
    uncertainty = _finite_1d(uncertainty, "uncertainty")
    if x.shape != uncertainty.shape:
        raise ValueError("x, signal, and uncertainty must have the same shape")
    if np.any(uncertainty <= 0):
        raise ValueError("uncertainty must be positive")
    return LombScargle(x, signal, dy=uncertainty).power(frequency)


def spectral_resolution(x: np.ndarray, frequency: np.ndarray) -> tuple[float, float, np.ndarray]:
    """Return x span, baseline scale ``1/span``, and cycles across support."""

    x = _finite_1d(x, "x")
    frequency = _finite_1d(frequency, "frequency")
    span = float(np.ptp(x))
    if span <= 0:
        raise ValueError("x must span a nonzero interval")
    return span, 1 / span, frequency * span


def local_maxima(power: np.ndarray, *, strongest: int = 5) -> np.ndarray:
    """Return strongest deterministic interior local-maximum indices.

    Endpoints are excluded because they are boundary bins rather than interior
    peaks. Callers should report a scientifically relevant boundary separately.
    """

    power = _finite_1d(power, "power")
    candidates = [
        index for index in range(1, power.size - 1)
        if power[index] > power[index - 1] and power[index] >= power[index + 1]
    ]
    ordered = sorted(candidates, key=lambda index: (-power[index], index))
    return np.asarray(ordered[:strongest], dtype=int)


def _finite_1d(values: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0 or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a non-empty finite one-dimensional array")
    return array
