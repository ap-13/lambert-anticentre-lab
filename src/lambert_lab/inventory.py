"""Deterministic forensic inventory of the Lambert Zenodo figure release.

The inventory is built directly from the immutable release ZIP.  Scientific
semantics in :data:`PRODUCT_SEMANTICS` are transcribed from the author FITS
headers and Lambert et al. (2026); they are deliberately kept separate from
the numerical inspection so that array appearance is never used as evidence.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import re
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import astropy
import numpy as np
from astropy.io import fits

from . import __version__
from .validation import file_checksum

INVENTORY_SCHEMA_VERSION = 1
DEFAULT_ARCHIVE_NAME = "Lambert_DESI_DR2_MW_outer_disk_figures_data.zip"
PAPER_DOI = "10.3847/1538-3881/ae5100"
ARXIV_ID = "2601.14562"


def _axis(
    name: str,
    unit: str,
    minimum: float,
    maximum: float,
    bins: int,
    *,
    paper_binning: str | None = None,
    issue: str | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "unit": unit,
        "range_from_header": [minimum, maximum],
        "bins": bins,
        "nominal_bin_width_from_range": (maximum - minimum) / bins,
        "paper_binning_statement": paper_binning,
        "issue": issue,
    }


# The first NumPy dimension is the vertical/y axis and the second is the
# horizontal/x axis for every released image.  No WCS keywords or bin-edge
# vectors are present in the files.
PRODUCT_SEMANTICS: dict[str, dict[str, Any]] = {
    "XY_hist_fig2.fits": {
        "figure": 3,
        "panel": "top right",
        "quantity": "star count",
        "value_kind": "raw binned count",
        "value_unit": "count",
        "axes": [_axis("X", "kpc", 8, 25, 85), _axis("Y", "kpc", -8, 8, 80)],
        "selection": "MSTO anticenter sample",
        "mapping_note": "Filename says fig2, but header quantity/axes and the published Figure 3 caption identify the top-right panel.",
    },
    "XY_vphi_fig2.fits": {
        "figure": 3,
        "panel": "bottom right",
        "quantity": "median azimuthal velocity V_phi",
        "value_kind": "binned median",
        "value_unit": "km / s",
        "axes": [_axis("X", "kpc", 8, 25, 85), _axis("Y", "kpc", -8, 8, 80)],
        "selection": "MSTO anticenter sample",
        "mapping_note": "Filename says fig2, but header quantity/axes and the published Figure 3 caption identify the bottom-right panel.",
    },
    "RZ_vphi_fig2.fits": {
        "figure": 3,
        "panel": "bottom left",
        "quantity": "median azimuthal velocity V_phi",
        "value_kind": "binned median",
        "value_unit": "km / s",
        "axes": [_axis("R", "kpc", 8, 25, 85), _axis("Z", "kpc", -1, 11, 60)],
        "selection": "MSTO anticenter sample",
        "mapping_note": "Filename says fig2, but header quantity/axes and the published Figure 3 caption identify the bottom-left panel.",
    },
    "lb_completeness_N.fits": {
        "figure": 4,
        "panel": "top",
        "quantity": "uncorrected density distribution",
        "value_kind": "binned count",
        "value_unit": "count",
        "axes": [_axis("l", "deg", 150, 220, 70), _axis("b", "deg", 15, 45, 60)],
        "selection": "MSTO sample",
        "display_note": "The released array covers b=15--45 deg; the published panel is displayed over b=20--40 deg.",
    },
    "lb_completeness_N_corrected.fits": {
        "figure": 4,
        "panel": "middle",
        "quantity": "completeness-corrected density distribution",
        "value_kind": "weighted binned count",
        "value_unit": "effective count",
        "axes": [_axis("l", "deg", 150, 220, 70), _axis("b", "deg", 15, 45, 60)],
        "selection": "MSTO sample",
        "display_note": "The released array covers b=15--45 deg; the published panel is displayed over b=20--40 deg.",
    },
    "lb_completeness_ratio.fits": {
        "figure": 4,
        "panel": "bottom",
        "quantity": "spectroscopic completeness ratio",
        "value_kind": "binned ratio",
        "value_unit": "dimensionless",
        "axes": [_axis("l", "deg", 150, 220, 70), _axis("b", "deg", 15, 45, 60)],
        "selection": "MAIN-BLUE targeting/spectroscopic completeness applied to the MSTO sample",
        "display_note": "The released array covers b=15--45 deg; the published panel is displayed over b=20--40 deg.",
    },
    "lb_VR_fig5.fits": {
        "figure": 5,
        "panel": "top left",
        "quantity": "median radial velocity V_R",
        "value_kind": "binned median",
        "value_unit": "km / s",
        "axes": [_axis("l", "deg", 150, 220, 42, paper_binning="one bin per degree", issue="Header/shape imply 0.6 bin per degree, conflicting with the paper caption."), _axis("b", "deg", 20, 40, 12, paper_binning="one bin per degree", issue="Header/shape imply 0.6 bin per degree, conflicting with the paper caption.")],
        "selection": "MSTO anticenter sample with R > 14 kpc",
    },
    "lb_VZ_fig5.fits": {
        "figure": 5, "panel": "top middle", "quantity": "median vertical velocity V_Z",
        "value_kind": "binned median", "value_unit": "km / s",
        "axes": [_axis("l", "deg", 150, 220, 42, paper_binning="one bin per degree", issue="Header/shape imply 0.6 bin per degree, conflicting with the paper caption."), _axis("b", "deg", 20, 40, 12, paper_binning="one bin per degree", issue="Header/shape imply 0.6 bin per degree, conflicting with the paper caption.")],
        "selection": "MSTO anticenter sample with R > 14 kpc",
    },
    "lb_feh_fig5.fits": {
        "figure": 5, "panel": "top right", "quantity": "median [Fe/H]",
        "value_kind": "binned median", "value_unit": "dex",
        "axes": [_axis("l", "deg", 150, 220, 42, paper_binning="one bin per degree", issue="Header/shape imply 0.6 bin per degree, conflicting with the paper caption."), _axis("b", "deg", 20, 40, 12, paper_binning="one bin per degree", issue="Header/shape imply 0.6 bin per degree, conflicting with the paper caption.")],
        "selection": "MSTO anticenter sample with R > 14 kpc",
    },
    "RZ_VR_fig5.fits": {
        "figure": 5, "panel": "bottom left", "quantity": "median radial velocity V_R",
        "value_kind": "binned median", "value_unit": "km / s",
        "axes": [_axis("R", "kpc", 8, 24, 48), _axis("Z", "kpc", 0, 10, 30)],
        "selection": "MSTO anticenter sample",
    },
    "RZ_VZ_fig5.fits": {
        "figure": 5, "panel": "bottom middle", "quantity": "median vertical velocity V_Z",
        "value_kind": "binned median", "value_unit": "km / s",
        "axes": [_axis("R", "kpc", 8, 24, 48), _axis("Z", "kpc", 0, 10, 30)],
        "selection": "MSTO anticenter sample",
    },
    "RZ_feh_fig5.fits": {
        "figure": 5, "panel": "bottom right", "quantity": "median [Fe/H]",
        "value_kind": "binned median", "value_unit": "dex",
        "axes": [_axis("R", "kpc", 8, 24, 48), _axis("Z", "kpc", 0, 10, 30)],
        "selection": "MSTO anticenter sample",
    },
    "XY_overdensity_fig6.fits": {
        "figure": 6, "panel": "left", "quantity": "completeness-corrected density minus exponential disk model",
        "value_kind": "binned residual", "value_unit": "effective count",
        "axes": [_axis("X", "kpc", 8, 23, 28, paper_binning="two bins per kpc", issue="28 bins across the stated 15 kpc range do not equal two bins per kpc; no bin edges are released."), _axis("Y", "kpc", -8, 8, 16, paper_binning="one bin per kpc")],
        "selection": "MSTO anticenter sample with 0 < Z < 5 kpc; bins with <=5 stars removed",
    },
    "XY_VR_fig6.fits": {
        "figure": 6, "panel": "second from left", "quantity": "median radial velocity V_R",
        "value_kind": "binned median", "value_unit": "km / s",
        "axes": [_axis("X", "kpc", 8, 23, 28, paper_binning="two bins per kpc", issue="28 bins across the stated 15 kpc range do not equal two bins per kpc; no bin edges are released."), _axis("Y", "kpc", -8, 8, 16, paper_binning="one bin per kpc")],
        "selection": "MSTO anticenter sample with 0 < Z < 5 kpc; bins with <=5 stars removed",
    },
    "XY_local_Vphi_fig6.fits": {
        "figure": 6, "panel": "third from left", "quantity": "median V_phi - <V_phi(R)>",
        "value_kind": "binned median of a per-star transformed quantity", "value_unit": "km / s",
        "axes": [_axis("X", "kpc", 8, 23, 28, paper_binning="two bins per kpc", issue="28 bins across the stated 15 kpc range do not equal two bins per kpc; no bin edges are released."), _axis("Y", "kpc", -8, 8, 16, paper_binning="one bin per kpc")],
        "selection": "MSTO anticenter sample with 0 < Z < 5 kpc; bins with <=5 stars removed",
    },
    "XY_VZ_fig6.fits": {
        "figure": 6, "panel": "right", "quantity": "median vertical velocity V_Z",
        "value_kind": "binned median", "value_unit": "km / s",
        "axes": [_axis("X", "kpc", 8, 23, 28, paper_binning="two bins per kpc", issue="28 bins across the stated 15 kpc range do not equal two bins per kpc; no bin edges are released."), _axis("Y", "kpc", -8, 8, 16, paper_binning="one bin per kpc")],
        "selection": "MSTO anticenter sample with 0 < Z < 5 kpc; bins with <=5 stars removed",
    },
    "RVphi_count_fig8.fits": {
        "figure": 8, "panel": "left", "quantity": "completeness-corrected number density",
        "value_kind": "weighted binned count", "value_unit": "effective count",
        "axes": [_axis("R", "kpc", 9, 24, 30, paper_binning="two bins per kpc"), _axis("V_phi", "km / s", 140, 270, 32, paper_binning="0.25 bins per km/s", issue="The stated range and rate imply 32.5 bins, while 32 rows are released; no bin edges are supplied.")],
        "selection": "MSTO anticenter MRi-region sample with 0 < Z < 5 kpc and Y > 0 kpc; bins with <20 stars removed",
    },
    "RVphi_VR_fig8.fits": {
        "figure": 8, "panel": "middle", "quantity": "median radial velocity V_R",
        "value_kind": "binned median", "value_unit": "km / s",
        "axes": [_axis("R", "kpc", 9, 24, 30, paper_binning="two bins per kpc"), _axis("V_phi", "km / s", 140, 270, 32, paper_binning="0.25 bins per km/s", issue="The stated range and rate imply 32.5 bins, while 32 rows are released; no bin edges are supplied.")],
        "selection": "MSTO anticenter MRi-region sample with 0 < Z < 5 kpc and Y > 0 kpc; bins with <20 stars removed",
    },
    "RVphi_VZ_fig8.fits": {
        "figure": 8, "panel": "right", "quantity": "median vertical velocity V_Z",
        "value_kind": "binned median", "value_unit": "km / s",
        "axes": [_axis("R", "kpc", 9, 24, 30, paper_binning="two bins per kpc"), _axis("V_phi", "km / s", 140, 270, 32, paper_binning="0.25 bins per km/s", issue="The stated range and rate imply 32.5 bins, while 32 rows are released; no bin edges are supplied.")],
        "selection": "MSTO anticenter MRi-region sample with 0 < Z < 5 kpc and Y > 0 kpc; bins with <20 stars removed",
    },
    "Lz_Vr_fig9.fits": {
        "figure": 9, "panel": "single panel", "quantity": "binned V_R versus L_Z with uncertainty",
        "value_kind": "binned summary table", "value_unit": "per-column",
        "selection": "Paper: MSTO anticenter MRi-region selection, 8 < R < 23 kpc, Z < 5 kpc, 175 < l < 185 deg",
        "mapping_note": "Filename and published Figure 9 caption.",
    },
    "FFT_fig10.fits": {
        "figure": 10, "panel": "single panel", "quantity": "Monte-Carlo Fourier power spectrum and 1-sigma spread",
        "value_kind": "derived Fourier table", "value_unit": "per-column / partly undocumented",
        "selection": "Derived by the authors from the Figure 9 product under the paper's timing workflow",
        "mapping_note": "Filename and published Figure 10 caption.",
    },
    "lb_panstarrs_fig11.fits": {
        "figure": 11, "panel": "single panel", "quantity": "Pan-STARRS star count",
        "value_kind": "binned count", "value_unit": "count",
        "axes": [_axis("l", "deg", 150, 220, 140), _axis("b", "deg", 20, 40, 40)],
        "selection": "Pan-STARRS photometry with 0.2 < g-r < 0.4 and 18 < g < 21 mag",
    },
    "lb_VR_fig12.fits": {
        "figure": 12, "panel": "left", "quantity": "median radial velocity V_R",
        "value_kind": "binned median", "value_unit": "km / s",
        "axes": [_axis("l", "deg", 150, 220, 35, paper_binning="2 degrees per bin"), _axis("b", "deg", 20, 40, 10, paper_binning="2 degrees per bin")],
        "selection": "MSTO anticenter sample with heliocentric distance >10 kpc",
    },
    "lb_VZ_fig12.fits": {
        "figure": 12, "panel": "middle", "quantity": "median vertical velocity V_Z",
        "value_kind": "binned median", "value_unit": "km / s",
        "axes": [_axis("l", "deg", 150, 220, 35, paper_binning="2 degrees per bin"), _axis("b", "deg", 20, 40, 10, paper_binning="2 degrees per bin")],
        "selection": "MSTO anticenter sample with heliocentric distance >10 kpc",
    },
    "lb_feh_fig12.fits": {
        "figure": 12, "panel": "right", "quantity": "median [Fe/H]",
        "value_kind": "binned median", "value_unit": "dex",
        "axes": [_axis("l", "deg", 150, 220, 35, paper_binning="2 degrees per bin"), _axis("b", "deg", 20, 40, 10, paper_binning="2 degrees per bin")],
        "selection": "MSTO anticenter sample with heliocentric distance >10 kpc",
    },
    "fig13_and_fig14_table.fits": {
        "figure": [13, 14], "panel": "source rows for paper-defined panel subsets",
        "quantity": "selected-star l, b, V_Z, and V_R rows",
        "value_kind": "individual selected-star rows (not binned values)", "value_unit": "per-column",
        "selection": "MSTO anticenter sample with heliocentric distance >10 kpc; Figure 13 additionally uses 10-degree longitude bins from 150 to 200 deg; Figure 14 uses 160--170 and 190--200 deg",
        "mapping_note": "Filename plus published Figures 13/14 captions and methods. The paper describes scatter plots of all stars and sign-filtered subsets; the four continuous per-row columns supply those operations.",
    },
}


def _unresolved_questions(filename: str) -> list[str]:
    questions = []
    if filename.endswith(".fits") and filename not in TABLE_COLUMN_CONTEXT:
        questions.append(
            "Physical units are described in the filename/header/paper but are not encoded with FITS CUNIT/BUNIT keywords."
        )
    if "fig5" in filename and (filename.startswith("lb_")):
        questions.append(
            "Why do the l-b shape/header bin counts conflict with the published one-bin-per-degree statement?"
        )
    if "fig6" in filename:
        questions.append(
            "What exact X bin edges produce 28 bins over the stated 8--23 kpc range when the paper says two bins per kpc?"
        )
    if "fig8" in filename:
        questions.extend(
            [
                "What exact V_phi bin edges produce 32 rows over the stated 140--270 km/s range?",
                "Why does the FITS COMMENT say 'negative azimuthal velocity' while the paper defines/displays positive V_phi over this range?",
            ]
        )
    if filename == "Lz_Vr_fig9.fits":
        questions.append(
            "Is the released V_R statistic a mean or median, and which stated bin range/count is authoritative?"
        )
    if filename == "FFT_fig10.fits":
        questions.extend(
            [
                "Was the Monte-Carlo power combined by a mean or median?",
                "What resampling, preprocessing, normalization, seed, and peak-fit procedure produced this spectrum?",
            ]
        )
    if filename == "lb_panstarrs_fig11.fits":
        questions.append(
            "What coefficients, points, and fitting procedure define the two unreleased ACS parabolas?"
        )
    if filename == "fig13_and_fig14_table.fits":
        questions.append(
            "What are the unreleased ACS boundary/width values, and can the exact upstream distance/quality selection be audited without identifiers or selection columns?"
        )
    return questions


TABLE_COLUMN_CONTEXT: dict[str, dict[str, dict[str, Any]]] = {
    "Lz_Vr_fig9.fits": {
        "angular momentum [kpc km/s]": {"physical_quantity": "L_Z", "interpreted_unit": "kpc km / s", "description": "Released L_Z bin coordinate; this is L_Z, not 1/L_Z."},
        "radial velocity [km/s]": {"physical_quantity": "V_R bin summary", "interpreted_unit": "km / s", "description": "Paper conflict: Figure 9 caption calls this the mean, while the body calls it the median."},
        "radial velocity uncertainty [km/s]": {"physical_quantity": "V_R uncertainty", "interpreted_unit": "km / s", "description": "Paper identifies this as the standard error on the mean."},
    },
    "FFT_fig10.fits": {
        "Frequency of Vr in 1/Lz": {"physical_quantity": "Fourier frequency for V_R in L_Z^-1", "interpreted_unit": "1 / ((kpc km / s)^-1), equivalently kpc km / s for n=0", "description": "Released frequency grid in descending order."},
        "Power": {"physical_quantity": "median/average Monte-Carlo Fourier power", "interpreted_unit": None, "description": "Paper caption says median power; body says average power. Normalization and physical unit are not documented."},
        "1-sigma on the Power": {"physical_quantity": "1-sigma spread in power", "interpreted_unit": None, "description": "Spread from 1,000 Monte-Carlo samples according to the paper; random seed is not published."},
    },
    "fig13_and_fig14_table.fits": {
        "Galactic latitude [deg]": {"physical_quantity": "b", "interpreted_unit": "deg", "description": "Per-row Galactic latitude."},
        "Galactic longitude [deg]": {"physical_quantity": "l", "interpreted_unit": "deg", "description": "Per-row Galactic longitude."},
        "vertical velocity [km/s]": {"physical_quantity": "V_Z", "interpreted_unit": "km / s", "description": "Per-row Galactocentric vertical velocity used for Figure 14 sign subsets and Figure 13 ordinate."},
        "radial velocity [km/s]": {"physical_quantity": "V_R", "interpreted_unit": "km / s", "description": "Per-row Galactocentric radial velocity used for Figure 13 sign subsets and Figure 14 ordinate."},
    },
}


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, np.generic):
        return _json_value(value.item())
    return str(value)


def _numeric_stats(array: np.ndarray) -> dict[str, Any]:
    values = np.asarray(array)
    result: dict[str, Any] = {"elements": int(values.size)}
    if not np.issubdtype(values.dtype, np.number):
        result.update({"finite": None, "invalid": None, "minimum": None, "maximum": None})
        return result
    finite = np.isfinite(values)
    result.update(
        {
            "finite": int(finite.sum()),
            "nan": int(np.isnan(values).sum()) if np.issubdtype(values.dtype, np.inexact) else 0,
            "positive_infinity": int(np.isposinf(values).sum()) if np.issubdtype(values.dtype, np.inexact) else 0,
            "negative_infinity": int(np.isneginf(values).sum()) if np.issubdtype(values.dtype, np.inexact) else 0,
            "invalid": int((~finite).sum()),
            "zero": int((values == 0).sum()),
            "minimum": _json_value(values[finite].min()) if finite.any() else None,
            "maximum": _json_value(values[finite].max()) if finite.any() else None,
        }
    )
    return result


def _header_inventory(header: fits.Header) -> dict[str, Any]:
    cards = []
    for card in header.cards:
        cards.append(
            {
                "keyword": card.keyword,
                "value": _json_value(card.value),
                "comment": card.comment or None,
            }
        )
    return {
        "cards": cards,
        "comments": [str(value) for value in header.get("COMMENT", [])]
        if "COMMENT" in header
        else [],
        "history": [str(value) for value in header.get("HISTORY", [])]
        if "HISTORY" in header
        else [],
        "wcs_axis_keywords_present": sorted(
            key
            for key in header
            if re.fullmatch(r"(CTYPE|CUNIT|CRPIX|CRVAL|CDELT|CD|PC)\d+(_\d+)?", key)
        ),
    }


def _column_inventory(filename: str, hdu: fits.BinTableHDU) -> list[dict[str, Any]]:
    context = TABLE_COLUMN_CONTEXT.get(filename, {})
    columns = []
    for column in hdu.columns:
        values = np.asarray(hdu.data[column.name])
        item = {
            "name": column.name,
            "fits_format": column.format,
            "dtype": str(values.dtype),
            "unit": column.unit,
            "dimensions": column.dim,
            "null_sentinel": column.null,
            "description_in_fits": None,
            "statistics": _numeric_stats(values),
        }
        item.update(context.get(column.name, {}))
        columns.append(item)
    return columns


def _hdu_inventory(filename: str, index: int, hdu: fits.hdu.base.ExtensionHDU) -> dict[str, Any]:
    data = hdu.data
    item: dict[str, Any] = {
        "index": index,
        "extname": hdu.header.get("EXTNAME"),
        "astropy_name": hdu.name,
        "hdu_class": type(hdu).__name__,
        "shape": list(data.shape) if data is not None else [],
        "dimensionality": int(data.ndim) if data is not None else 0,
        "dtype": str(data.dtype) if data is not None else None,
        "row_count": int(len(data)) if isinstance(hdu, fits.BinTableHDU) else None,
        "column_count": len(hdu.columns) if isinstance(hdu, fits.BinTableHDU) else None,
        "columns": _column_inventory(filename, hdu) if isinstance(hdu, fits.BinTableHDU) else [],
        "header": _header_inventory(hdu.header),
        "statistics": _numeric_stats(np.asarray(data)) if data is not None and not isinstance(hdu, fits.BinTableHDU) else None,
        "mask_or_sentinel": None,
    }
    if data is not None and not isinstance(hdu, fits.BinTableHDU):
        stats = item["statistics"]
        if stats["nan"]:
            item["mask_or_sentinel"] = "NaN marks unavailable/removed image bins; no separate mask HDU is present."
        elif stats["zero"] and "count" in PRODUCT_SEMANTICS[filename]["value_kind"]:
            item["mask_or_sentinel"] = "Zero is a finite zero-count bin, not a FITS null sentinel."
        else:
            item["mask_or_sentinel"] = "No invalid values or declared FITS sentinel."
    return item


def _fits_inventory(filename: str, payload: bytes) -> dict[str, Any]:
    with fits.open(io.BytesIO(payload), memmap=False, checksum=True) as hdus:
        result = {
            "valid_fits": True,
            "hdu_count": len(hdus),
            "hdus": [_hdu_inventory(filename, index, hdu) for index, hdu in enumerate(hdus)],
            "panel_or_slice_structure": (
                "One 2-D panel in the primary HDU; no cube, slice axis, or additional panel HDU."
                if filename not in TABLE_COLUMN_CONTEXT
                else "One empty primary HDU plus one binary table; paper panels/subsets are derived from table rows rather than stored as separate HDUs."
            ),
        }
    semantics = PRODUCT_SEMANTICS[filename]
    if "axes" in semantics:
        result["image_axes"] = {
            "fits_wcs_or_explicit_edges_present": False,
            "horizontal_axis": semantics["axes"][0],
            "vertical_axis": semantics["axes"][1],
            "numpy_axis_order": [semantics["axes"][1]["name"], semantics["axes"][0]["name"]],
            "orientation_for_paper": {
                "transpose_required": False,
                "origin": "lower",
                "extent": [
                    semantics["axes"][0]["range_from_header"][0],
                    semantics["axes"][0]["range_from_header"][1],
                    semantics["axes"][1]["range_from_header"][0],
                    semantics["axes"][1]["range_from_header"][1],
                ],
                "evidence": "NumPy/FITS axis ordering plus direct morphology comparison with the published author panel; axis meaning itself comes from the FITS COMMENT and paper caption, not numerical appearance.",
                "caveat": "Ranges are header-stated extents, not released WCS/bin edges; see per-axis issues and display notes.",
            },
        }
    return result


def _paper_sources() -> dict[str, Any]:
    return {
        "published": {
            "doi": PAPER_DOI,
            "url": f"https://doi.org/{PAPER_DOI}",
            "journal": "The Astronomical Journal",
            "volume": "171",
            "issue": "5",
            "article": "292",
            "online_date": "2026-04-15",
        },
        "arxiv": {"identifier": ARXIV_ID, "url": f"https://arxiv.org/abs/{ARXIV_ID}"},
        "locations_used": {
            "figures_3_to_8": "published captions and Sections 2.3--3.4",
            "figures_9_and_10": "published Section 3.5, Figure 9/10 captions, and Equation (1)",
            "figures_11_to_14": "published Sections 3.6--3.7 and Figure 11--14 captions",
        },
    }


def _figure_mapping(filename: str) -> dict[str, Any]:
    semantics = PRODUCT_SEMANTICS[filename]
    figure = semantics["figure"]
    filename_evidence = bool(re.search(r"fig(?:ure)?_?\d+|fig\d+", filename, re.I))
    zenodo_specific = figure == 9 or figure == 10 or figure == [13, 14]
    return {
        "paper_figure": figure,
        "panel": semantics["panel"],
        "evidence": {
            "filename": filename_evidence,
            "fits_header": filename not in {"Lz_Vr_fig9.fits", "FFT_fig10.fits", "fig13_and_fig14_table.fits"},
            "zenodo_description": zenodo_specific,
            "paper_caption_or_method": True,
        },
        "basis": "Exact mapping uses the combination of filename, FITS axis/quantity metadata where present, Zenodo's table-vs-array statement, and the published caption/method; numerical appearance alone is not used.",
        "note": semantics.get("mapping_note"),
    }


def _special_findings() -> dict[str, Any]:
    return {
        "figure_9": {
            "released_variables": ["L_Z", "binned V_R summary", "V_R uncertainty"],
            "lz_or_inverse_lz": "L_Z is released; 1/L_Z is not a column but can be computed exactly from released L_Z values.",
            "representation": "70 uniformly spaced L_Z-bin summary rows; not individual stars and not a Fourier-ready uniformly spaced 1/L_Z series.",
            "uncertainties": "One V_R uncertainty per bin is released; the paper identifies it as standard error on the mean.",
            "paper_conflict": "Figure 9 caption says mean, 70 bins, 1400--4500; body says median, 75 bins, 2000--4500. Release has 70 rows with centers 1500--4457.142857 in steps of 42.857143.",
        },
        "figure_10": {
            "released_variables": ["Fourier frequency of V_R in 1/L_Z", "power", "1-sigma on power"],
            "representation": "35-row author-computed spectrum on a descending, uniformly spaced frequency grid; not Fourier inputs.",
            "uncertainties": "Power spread is released, but Gaussian peak centers/widths and their fit covariance are not columns.",
            "independent_fft": "Blocked for exact reproduction: Figure 9 supplies the binned wave, but the paper does not specify resampling/interpolation from uniform L_Z to nonuniform 1/L_Z, FFT normalization/window/detrending, or the Monte-Carlo seed/statistic consistently.",
        },
        "figure_13": {
            "row_representation": "Individual rows from the authors' already-selected MSTO anticenter sample with heliocentric distance >10 kpc; not binned values and not the full DR2 source catalogue.",
            "vr_availability": "V_R is present per row; author-produced sign-subset labels are not stored.",
            "sign_experiment": "The all-stars -> V_R>0 -> V_R<0 split can be independently recomputed for the paper longitude bins from the released columns.",
            "limits": "No source identifier, distance, selection flags, weights, uncertainties, photometry, metallicity, or photometric ACS boundary coefficients are released in this table.",
        },
        "figure_14": {
            "row_representation": "Uses the same individual selected-star table as Figure 13.",
            "vz_availability": "V_Z is present per row, so all/+V_Z/-V_Z subsets can be recomputed for the two published longitude bins.",
            "limits": "The photometric boundary/width overlays are absent, as are per-star uncertainties and upstream selection variables.",
        },
    }


def _capabilities() -> dict[str, Any]:
    return {
        "notebook_2": {
            "figures_5_6_style_products": {"classification": "YES — directly supported by released data", "evidence": "The release contains fixed 2-D arrays for the Figure 5 and 6 panels, with header/paper semantics."},
            "change_binning": {"classification": "NO — required source information is absent", "evidence": "The Figure 5/6 products are already-binned arrays and contain no source rows or bin edges."},
            "change_minimum_count_thresholds": {"classification": "NO — required source information is absent", "evidence": "Counts per velocity/metallicity bin are not released, so NaN masks cannot be recalculated at another threshold."},
            "change_source_level_selections": {"classification": "NO — required source information is absent", "evidence": "The image products do not contain stellar rows or upstream selection columns."},
            "acs_mri_velocity_sign_result": {"classification": "PARTIAL — only some stages are supported", "evidence": "Author-binned Figure 5/6 velocity maps encode the opposite-sign regions, but the full all-star selection and binning cannot be independently rebuilt."},
            "figure_13_vr_sign_split": {"classification": "YES — directly supported by released data", "evidence": "The 7,708-row table contains per-row l, b, V_Z, and V_R, allowing the paper longitude and V_R-sign subsets to be applied."},
            "photometric_acs_boundary": {"classification": "NO — required source information is absent", "evidence": "The Pan-STARRS count array is released, but the fitted parabola coefficients, fit points/procedure, and boundary/width vectors are not."},
        },
        "notebook_3": {
            "lz_vr_wave": {"classification": "YES — directly supported by released data", "evidence": "Figure 9 releases 70 L_Z-bin coordinates, V_R summaries, and V_R uncertainties."},
            "transform_to_inverse_lz": {"classification": "YES — directly supported by released data", "evidence": "Every released L_Z coordinate is finite and nonzero, so 1/L_Z is an exact data re-expression."},
            "independent_fourier_transform": {"classification": "PARTIAL — only some stages are supported", "evidence": "The binned wave and errors are present, but the required resampling/interpolation and FFT preprocessing/normalization are undocumented."},
            "published_fourier_peaks": {"classification": "PARTIAL — only some stages are supported", "evidence": "The released Figure 10 spectrum supports grid-level peak localization, but Gaussian fit samples/windows and fitted centers/widths are absent."},
            "timing_conversion": {"classification": "YES — directly supported by released data", "evidence": "Published Equation (1), n=0, V0=239.26 km/s, R0=8.277 kpc, and the quoted peak frequencies reproduce about 0.24 and 1.08 Gyr before rounding."},
            "paper_assumptions": {"classification": "PARTIAL — only some stages are supported", "evidence": "The paper supplies the circular-curve form/slope, epicycle approximation, corotating tidal-arm mapping, Equation (1), V0, R0, Monte-Carlo count, and the interpretation of Fourier frequencies as winding times."},
        },
    }


def build_inventory(archive: str | Path, provenance: str | Path) -> dict[str, Any]:
    """Inspect ``archive`` and return the canonical nested inventory."""

    archive_path = Path(archive)
    provenance_path = Path(provenance)
    transfer = json.loads(provenance_path.read_text(encoding="utf-8"))
    advertised = next(
        (item for item in transfer["files"] if item["filename"] == archive_path.name), None
    )
    if advertised is None:
        raise ValueError(f"Provenance does not describe {archive_path.name}")
    algorithm, expected = advertised["advertised_checksum"].split(":", 1)
    actual = file_checksum(archive_path, algorithm)
    if archive_path.stat().st_size != advertised["byte_size"] or actual.lower() != expected.lower():
        raise ValueError("Cached archive does not match its recorded Zenodo size/checksum")

    members = []
    fits_files = 0
    hdu_count = 0
    with zipfile.ZipFile(archive_path) as archive_zip:
        bad_member = archive_zip.testzip()
        if bad_member is not None:
            raise ValueError(f"ZIP CRC verification failed at {bad_member}")
        for info in archive_zip.infolist():
            payload = archive_zip.read(info)
            member: dict[str, Any] = {
                "archive_path": info.filename,
                "filename": Path(info.filename).name,
                "byte_size": info.file_size,
                "compressed_byte_size": info.compress_size,
                "crc32": f"{info.CRC:08x}",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "is_directory": info.is_dir(),
            }
            if info.filename.startswith("__MACOSX/._"):
                member.update(
                    {
                        "asset_type": "AppleDouble metadata (not FITS)",
                        "valid_fits": False,
                        "fits_error": "No SIMPLE card; resource-fork metadata despite .fits suffix.",
                        "figure_mapping": None,
                    }
                )
            elif info.filename in PRODUCT_SEMANTICS:
                inspected = _fits_inventory(info.filename, payload)
                fits_files += 1
                hdu_count += inspected["hdu_count"]
                member.update(
                    {
                        "asset_type": "FITS binary table" if info.filename in TABLE_COLUMN_CONTEXT else "FITS 2-D image array",
                        "valid_fits": True,
                        "figure_mapping": _figure_mapping(info.filename),
                        "scientific_semantics": PRODUCT_SEMANTICS[info.filename],
                        "unresolved_semantic_questions": _unresolved_questions(info.filename),
                        "fits": inspected,
                    }
                )
            else:
                member.update({"asset_type": "unmapped archive member", "valid_fits": False, "figure_mapping": None})
            members.append(member)

    missing = sorted(set(PRODUCT_SEMANTICS) - {m["archive_path"] for m in members})
    if missing:
        raise ValueError(f"Expected release products are missing: {missing}")

    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "inventory_kind": "Lambert author-released figure-data forensic inventory",
        "generation": {
            "generator": "scripts/build_lambert_inventory.py via lambert_lab.inventory.build_inventory",
            "package_version": __version__,
            "python_dependency": f"astropy {astropy.__version__}",
            "parameters": {"read_directly_from_zip": True, "network_access": False},
            "determinism": "No generation timestamp or filesystem-dependent path is recorded; sorted JSON output is byte-deterministic for fixed inputs and software.",
        },
        "release": {
            "requested_record_id": transfer["requested_record_id"],
            "resolved_record_id": transfer["resolved_record_id"],
            "concept_record_id": transfer["concept_record_id"],
            "doi": transfer["doi"],
            "record_url": transfer["record_url"],
            "metadata_source_url": transfer["metadata_source_url"],
            "title": transfer["title"],
            "version": transfer["version"],
            "publication_date": transfer["publication_date"],
            "creators": transfer["creators"],
            "license": transfer["license"],
            "citation": transfer["citation"],
            "retrieval_timestamp": transfer["retrieved_at"],
            "zenodo_description": "Supplementary figure data: Figures 9, 10, 13, and 14 are FITS tables; the other supplied products are 2-D arrays; descriptions are in FITS headers.",
            "archive": {
                "filename": archive_path.name,
                "byte_size": archive_path.stat().st_size,
                "advertised_checksum": advertised["advertised_checksum"],
                "verified_checksum": f"{algorithm}:{actual}",
                "sha256": file_checksum(archive_path, "sha256"),
                "zip_crc_verified": True,
                "source_url": advertised["source_url"],
                "preservation": "Inspected read-only and unchanged; extraction is optional and ignored.",
            },
        },
        "authoritative_sources": _paper_sources(),
        "summary": {
            "archive_members": len(members),
            "valid_fits_files": fits_files,
            "fits_image_files": sum(m["asset_type"] == "FITS 2-D image array" for m in members),
            "fits_table_files": sum(m["asset_type"] == "FITS binary table" for m in members),
            "appledouble_metadata_members": sum(m["asset_type"].startswith("AppleDouble") for m in members),
            "fits_hdus": hdu_count,
            "unreleased_paper_figures_or_panels": [
                "Figure 1 data", "Figure 2 data", "Figure 3 top-left R-Z count panel", "Figure 7 data"
            ],
        },
        "archive_members": members,
        "focused_findings": _special_findings(),
        "capability_matrix": _capabilities(),
    }


def write_inventory(inventory: Mapping[str, Any], destination: str | Path) -> None:
    """Write a canonical, byte-deterministic JSON representation."""

    output = json.dumps(inventory, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    Path(destination).write_text(output, encoding="utf-8")
