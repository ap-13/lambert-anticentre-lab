"""Small plotting helpers for the teaching notebooks."""

from __future__ import annotations

from collections.abc import Iterable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

from .data import ReleasedImage

EVIDENCE_LEVELS = (
    "OBSERVABLE / MEASUREMENT",
    "COMPUTATIONAL OPERATION",
    "DATA-SUPPORTED INFERENCE",
    "MODEL-DEPENDENT INTERPRETATION",
    "SPECULATION / PHYSICAL EXPLANATION",
)


def zero_centered_norm(values: np.ndarray, *, limit: float | None = None) -> TwoSlopeNorm:
    """Return a symmetric normalization whose neutral colour is exactly zero."""

    finite = np.asarray(values, dtype=float)[np.isfinite(values)]
    if finite.size == 0:
        raise ValueError("Cannot normalize an array without finite values")
    bound = float(np.max(np.abs(finite))) if limit is None else float(limit)
    if not np.isfinite(bound) or bound <= 0:
        raise ValueError("limit must be a positive finite number")
    return TwoSlopeNorm(vmin=-bound, vcenter=0.0, vmax=bound)


def display_released_image(
    ax: plt.Axes,
    product: ReleasedImage,
    *,
    cmap: str = "viridis",
    norm: TwoSlopeNorm | None = None,
    title: str | None = None,
):
    """Display an inventoried fixed array without transposition or rebinning."""

    image = ax.imshow(
        product.data,
        origin="lower",
        extent=product.extent,
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        norm=norm,
    )
    x = product.horizontal_axis
    y = product.vertical_axis
    ax.set(
        xlabel=f"{x['name']} [{x['unit']}]",
        ylabel=f"{y['name']} [{y['unit']}]",
        title=title or product.quantity,
    )
    return image


def constant_lz_curves(
    radius: np.ndarray, angular_momenta: Iterable[float]
) -> dict[float, np.ndarray]:
    """Evaluate pedagogical constant-L_Z guide curves, V_phi=L_Z/R."""

    radius = np.asarray(radius, dtype=float)
    if radius.ndim != 1 or np.any(~np.isfinite(radius)) or np.any(radius <= 0):
        raise ValueError("radius must be a finite positive one-dimensional array")
    return {float(lz): float(lz) / radius for lz in angular_momenta}
