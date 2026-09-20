"""Small plotting helpers for the teaching notebooks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

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

SIGN_CATEGORY_LABELS = {
    0: "inward + downward",
    1: "inward + upward",
    2: "outward + downward",
    3: "outward + upward",
}


@dataclass(frozen=True)
class BinnedMedianGuide:
    """A display-only binned median guide and its per-bin support."""

    centers: np.ndarray
    medians: np.ndarray
    counts: np.ndarray
    included: np.ndarray


def zero_centered_norm(values: np.ndarray, *, limit: float | None = None) -> TwoSlopeNorm:
    """Return a symmetric normalization whose neutral colour is exactly zero."""

    finite = np.asarray(values, dtype=float)[np.isfinite(values)]
    if finite.size == 0:
        raise ValueError("Cannot normalize an array without finite values")
    bound = float(np.max(np.abs(finite))) if limit is None else float(limit)
    if not np.isfinite(bound) or bound <= 0:
        raise ValueError("limit must be a positive finite number")
    return TwoSlopeNorm(vmin=-bound, vcenter=0.0, vmax=bound)


def robust_symmetric_limit(values: np.ndarray, *, percentile: float = 95.0) -> float:
    """Return a positive symmetric display limit from finite absolute values.

    This changes colour saturation only; callers retain every supplied value.
    """

    finite = np.asarray(values, dtype=float)[np.isfinite(values)]
    if finite.size == 0:
        raise ValueError("Cannot set a robust limit without finite values")
    if not 0 < percentile <= 100:
        raise ValueError("percentile must be in (0, 100]")
    limit = float(np.percentile(np.abs(finite), percentile))
    if not np.isfinite(limit) or limit <= 0:
        raise ValueError("robust limit must be positive and finite")
    return limit


def positive_run_containing_maximum(values: np.ndarray) -> tuple[int, int]:
    """Return the half-open positive run containing a profile's maximum.

    Non-finite values interrupt a run.  This supports deterministic display
    shading of a released profile; it does not define an object boundary.
    """

    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("values must be a non-empty one-dimensional array")
    finite = np.isfinite(array)
    if not np.any(finite):
        raise ValueError("values contain no finite entries")
    maximum = int(np.nanargmax(array))
    if array[maximum] <= 0:
        raise ValueError("profile maximum is not positive")
    start = maximum
    while start > 0 and np.isfinite(array[start - 1]) and array[start - 1] > 0:
        start -= 1
    stop = maximum + 1
    while stop < array.size and np.isfinite(array[stop]) and array[stop] > 0:
        stop += 1
    return start, stop


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


def display_pixel_centers(product: ReleasedImage) -> tuple[np.ndarray, np.ndarray]:
    """Return nominal image-pixel centres implied by shape and display extent.

    These coordinates support transparent visual reductions of released image
    arrays.  They are not recovered FITS WCS coordinates or exact bin edges.
    """

    values = np.asarray(product.data)
    if values.ndim != 2:
        raise ValueError("released image data must be two-dimensional")
    xmin, xmax, ymin, ymax = map(float, product.extent)
    if not np.all(np.isfinite([xmin, xmax, ymin, ymax])) or xmax <= xmin or ymax <= ymin:
        raise ValueError("display extent must be finite and increasing")
    rows, columns = values.shape
    x = xmin + (np.arange(columns) + 0.5) * (xmax - xmin) / columns
    y = ymin + (np.arange(rows) + 0.5) * (ymax - ymin) / rows
    return x, y


def velocity_sign_categories(vr: np.ndarray, vz: np.ndarray) -> np.ma.MaskedArray:
    """Classify jointly finite, nonzero velocity pixels into four sign states.

    Codes follow :data:`SIGN_CATEGORY_LABELS`.  Missing values and exact zeros
    remain masked because they do not satisfy either strict sign inequality.
    """

    vr = np.asarray(vr, dtype=float)
    vz = np.asarray(vz, dtype=float)
    if vr.shape != vz.shape:
        raise ValueError("V_R and V_Z arrays must have the same shape")
    valid = np.isfinite(vr) & np.isfinite(vz) & (vr != 0) & (vz != 0)
    categories = np.zeros(vr.shape, dtype=np.int8)
    categories[valid] = 2 * (vr[valid] > 0) + (vz[valid] > 0)
    return np.ma.array(categories, mask=~valid)


def released_pixel_profile(
    product: ReleasedImage, *, collapse_axis: int, indices: Iterable[int]
) -> tuple[np.ndarray, np.ndarray]:
    """Average named released pixels and return the remaining display axis.

    This is an unweighted finite-value mean of already-aggregated author bins,
    not a source-level stellar statistic.  ``collapse_axis=0`` selects image
    rows and returns a profile along the horizontal axis; ``collapse_axis=1``
    selects columns and returns a profile along the vertical axis.
    """

    if collapse_axis not in (0, 1):
        raise ValueError("collapse_axis must be 0 (rows) or 1 (columns)")
    selected = np.asarray(tuple(indices), dtype=int)
    if selected.ndim != 1 or selected.size == 0 or np.unique(selected).size != selected.size:
        raise ValueError("indices must be a non-empty sequence of unique integers")
    if np.any(selected < 0) or np.any(selected >= product.data.shape[collapse_axis]):
        raise IndexError("profile index outside released image")
    subset = np.take(np.asarray(product.data, dtype=float), selected, axis=collapse_axis)
    finite = np.isfinite(subset)
    count = np.sum(finite, axis=collapse_axis)
    total = np.sum(np.where(finite, subset, 0.0), axis=collapse_axis)
    profile = np.full(count.shape, np.nan, dtype=float)
    np.divide(total, count, out=profile, where=count > 0)
    x, y = display_pixel_centers(product)
    return (x if collapse_axis == 0 else y), profile


def raw_column_peak(
    product: ReleasedImage, column: int, *, min_finite: int = 10
) -> tuple[int, float, float]:
    """Return a guarded raw argmax for one released image column.

    The result is a visual marker, not a fit.  Columns with too little support
    or a maximum at the edge of their finite support are rejected.
    """

    if not 0 <= column < product.data.shape[1]:
        raise IndexError("column outside released image")
    values = np.asarray(product.data[:, column], dtype=float)
    finite_indices = np.flatnonzero(np.isfinite(values))
    if finite_indices.size < min_finite:
        raise ValueError("column has insufficient finite support")
    peak_index = int(finite_indices[np.argmax(values[finite_indices])])
    if peak_index in (int(finite_indices[0]), int(finite_indices[-1])):
        raise ValueError("column maximum lies at the finite-support boundary")
    _, y = display_pixel_centers(product)
    return peak_index, float(y[peak_index]), float(values[peak_index])


def binned_median_visual_guide(
    x: np.ndarray,
    y: np.ndarray,
    edges: np.ndarray,
    *,
    min_count: int = 20,
) -> BinnedMedianGuide:
    """Compute a declared display-only median guide on fixed bin edges."""

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    edges = np.asarray(edges, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape:
        raise ValueError("x and y must be same-length one-dimensional arrays")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("x and y must be finite")
    if edges.ndim != 1 or edges.size < 2 or not np.all(np.diff(edges) > 0):
        raise ValueError("edges must be a strictly increasing one-dimensional array")
    if min_count < 1:
        raise ValueError("min_count must be positive")
    counts = np.zeros(edges.size - 1, dtype=int)
    medians = np.full(edges.size - 1, np.nan)
    for index, (lower, upper) in enumerate(zip(edges[:-1], edges[1:])):
        members = (x >= lower) & (x < upper)
        counts[index] = int(np.sum(members))
        if counts[index]:
            medians[index] = float(np.median(y[members]))
    return BinnedMedianGuide(
        centers=(edges[:-1] + edges[1:]) / 2,
        medians=medians,
        counts=counts,
        included=counts >= min_count,
    )


def toy_cycle_spectrum(
    cycles: float, *, sample_count: int = 256
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return a unit-baseline sine wave and its rectangular-window spectrum."""

    if not np.isfinite(cycles) or cycles <= 0:
        raise ValueError("cycles must be positive and finite")
    if sample_count < 8:
        raise ValueError("sample_count must be at least eight")
    coordinate = np.arange(sample_count, dtype=float) / sample_count
    signal = np.sin(2 * np.pi * cycles * coordinate)
    transformed = np.fft.rfft(signal - np.mean(signal))
    frequency = np.fft.rfftfreq(sample_count, d=1 / sample_count)
    power = np.abs(transformed) ** 2
    return coordinate, signal, frequency[1:], power[1:]


def constant_lz_curves(
    radius: np.ndarray, angular_momenta: Iterable[float]
) -> dict[float, np.ndarray]:
    """Evaluate pedagogical constant-L_Z guide curves, V_phi=L_Z/R."""

    radius = np.asarray(radius, dtype=float)
    if radius.ndim != 1 or np.any(~np.isfinite(radius)) or np.any(radius <= 0):
        raise ValueError("radius must be a finite positive one-dimensional array")
    return {float(lz): float(lz) / radius for lz in angular_momenta}
