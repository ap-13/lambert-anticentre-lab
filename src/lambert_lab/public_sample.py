"""Build the compact, public DESI DR1/Gaia teaching sample."""

from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import QTable

from . import __version__
from .validation import file_checksum

SOURCE_FILENAME = "rvpix-sv2-bright.fits"
SOURCE_URL = (
    "https://data.desi.lbl.gov/public/dr1/vac/dr1/mws/iron/v1.0/"
    "rv_output/240520/rvpix-sv2-bright.fits"
)
SOURCE_SIZE = 10_186_560
SOURCE_SHA256 = "622ebc4545a08215e2be4b4a8a198e7acfb9ac1d4dbd6cb2ce02f07a91e07487"
SOURCE_RELEASE = "DESI DR1 MWS Iron v1.0; Survey Validation 2 / bright"
SOURCE_DOCUMENTATION = "https://data.desi.lbl.gov/doc/releases/dr1/vac/mws/"
DATA_MODEL_DOCUMENTATION = (
    "https://desi-mws-dr1-datamodel.readthedocs.io/en/latest/"
    "rv_output/RVRUN/rvpix.html"
)
REQUIRED_EXTENSIONS = ("RVTAB", "FIBERMAP", "SCORES", "GAIA")
DEFAULT_SEED = 20260920
DEFAULT_MAX_STARS = 256
MINIMUM_STARS = 64
SCRIPT_VERSION = 1
SOURCE_PROVENANCE_FILENAME = "rvpix-sv2-bright.source.json"


class SampleBuildError(RuntimeError):
    """Raised when a source cannot safely produce the teaching sample."""


def verify_source(path: str | Path) -> Path:
    """Verify the pinned source size and SHA-256 without changing it."""

    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(
            f"Missing cached DESI source: {source}. Re-run with --download to "
            "fetch the one pinned Task 3 product."
        )
    size = source.stat().st_size
    if size != SOURCE_SIZE:
        raise SampleBuildError(
            f"Bad cache size for {source}: expected {SOURCE_SIZE}, found {size}. "
            "The file will not be overwritten; move or remove it explicitly."
        )
    digest = file_checksum(source)
    if digest != SOURCE_SHA256:
        raise SampleBuildError(
            f"Bad cache SHA-256 for {source}: expected {SOURCE_SHA256}, found "
            f"{digest}. The file will not be overwritten; move or remove it explicitly."
        )
    return source


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=f".{path.name}.", suffix=".part",
            dir=path.parent, delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def download_source(path: str | Path, *, timeout: float = 120.0) -> Path:
    """Explicitly download the pinned source, atomically and with verification."""

    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return verify_source(destination)

    request = urllib.request.Request(
        SOURCE_URL, headers={"User-Agent": f"lambert-anticentre-lab/{__version__}"}
    )
    temporary: Path | None = None
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{destination.name}.", suffix=".part",
                dir=destination.parent, delete=False,
            ) as stream:
                temporary = Path(stream.name)
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
        _verify_download(temporary)
        os.replace(temporary, destination)
        temporary = None
    except (OSError, urllib.error.URLError) as error:
        raise SampleBuildError(f"Unable to download {SOURCE_URL}: {error}") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return verify_source(destination)


def _verify_download(path: Path) -> None:
    size = path.stat().st_size
    digest = file_checksum(path)
    if size != SOURCE_SIZE or digest != SOURCE_SHA256:
        raise SampleBuildError(
            "Downloaded source failed verification: expected "
            f"{SOURCE_SIZE} bytes and SHA-256 {SOURCE_SHA256}, found {size} bytes "
            f"and {digest}; cache was not replaced."
        )


def ensure_source_provenance(source: Path) -> dict[str, Any]:
    """Read or create stable retrieval metadata beside a verified cache."""

    path = source.parent / SOURCE_PROVENANCE_FILENAME
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("sha256") != SOURCE_SHA256:
            raise SampleBuildError(f"Source provenance checksum disagrees with {source}")
        return payload
    payload = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "filename": SOURCE_FILENAME,
        "authoritative_source_url": SOURCE_URL,
        "byte_size": SOURCE_SIZE,
        "sha256": SOURCE_SHA256,
        "catalogue_release": SOURCE_RELEASE,
    }
    _atomic_json(payload, path)
    return payload


def _required_columns(table: Any, names: set[str], extension: str) -> None:
    missing = sorted(names.difference(table.names))
    if missing:
        raise SampleBuildError(f"{extension} is missing required columns: {missing}")


def _read_and_validate(source: Path) -> tuple[Any, Any, Any, Any, dict[str, Any]]:
    with fits.open(source, memmap=False, checksum=True) as hdus:
        available = [hdu.name for hdu in hdus]
        missing = [name for name in REQUIRED_EXTENSIONS if name not in available]
        if missing:
            raise SampleBuildError(f"Missing required FITS EXTNAMEs: {missing}")
        rv = hdus["RVTAB"].data.copy()
        fibermap = hdus["FIBERMAP"].data.copy()
        scores = hdus["SCORES"].data.copy()
        gaia = hdus["GAIA"].data.copy()

    _required_columns(
        rv,
        {"TARGETID", "TARGET_RA", "TARGET_DEC", "VRAD", "VRAD_ERR", "SN_R", "SUCCESS", "RVS_WARN", "RR_SPECTYPE"},
        "RVTAB",
    )
    _required_columns(fibermap, {"TARGETID", "TARGET_RA", "TARGET_DEC", "COADD_FIBERSTATUS"}, "FIBERMAP")
    _required_columns(scores, {"TARGETID"}, "SCORES")
    _required_columns(
        gaia,
        {
            "SOURCE_ID", "RA", "RA_ERROR", "DEC", "DEC_ERROR", "PARALLAX",
            "PARALLAX_ERROR", "PARALLAX_OVER_ERROR", "PMRA", "PMRA_ERROR",
            "PMDEC", "PMDEC_ERROR", "ASTROMETRIC_PARAMS_SOLVED",
            "VISIBILITY_PERIODS_USED", "RUWE", "DUPLICATED_SOURCE",
        },
        "GAIA",
    )

    lengths = {
        name: len(value)
        for name, value in zip(REQUIRED_EXTENSIONS, (rv, fibermap, scores, gaia), strict=True)
    }
    if len(set(lengths.values())) != 1:
        raise SampleBuildError(f"Extension row counts differ: {lengths}")
    if not np.array_equal(rv["TARGETID"], fibermap["TARGETID"]):
        raise SampleBuildError("RVTAB and FIBERMAP TARGETID row order differs")
    if not np.array_equal(rv["TARGETID"], scores["TARGETID"]):
        raise SampleBuildError("RVTAB and SCORES TARGETID row order differs")
    if not (
        np.array_equal(rv["TARGET_RA"], fibermap["TARGET_RA"])
        and np.array_equal(rv["TARGET_DEC"], fibermap["TARGET_DEC"])
    ):
        raise SampleBuildError("RVTAB and FIBERMAP target coordinates differ by row")

    finite_gaia_position = np.isfinite(gaia["RA"]) & np.isfinite(gaia["DEC"])
    if np.any(finite_gaia_position):
        target = SkyCoord(
            fibermap["TARGET_RA"][finite_gaia_position] * u.deg,
            fibermap["TARGET_DEC"][finite_gaia_position] * u.deg,
        )
        matched = SkyCoord(
            gaia["RA"][finite_gaia_position] * u.deg,
            gaia["DEC"][finite_gaia_position] * u.deg,
        )
        maximum_separation = float(target.separation(matched).max().to_value(u.arcsec))
        if maximum_separation > 2.0:
            raise SampleBuildError(
                "GAIA rows do not align with the DESI objects: maximum target/Gaia "
                f"separation is {maximum_separation:.3f} arcsec"
            )
    else:
        maximum_separation = None

    association = {
        "row_counts": lengths,
        "rvt_fibermap_targetid_exact": True,
        "rvt_scores_targetid_exact": True,
        "rvt_fibermap_target_coordinates_exact": True,
        "finite_gaia_position_rows": int(finite_gaia_position.sum()),
        "maximum_target_gaia_separation_arcsec": maximum_separation,
        "gaia_association_basis": (
            "Official rvpix data model states GAIA contains Gaia DR3 measurements "
            "for each catalogue object; finite row-wise positions were additionally "
            "required to lie within 2 arcsec."
        ),
    }
    return rv, fibermap, scores, gaia, association


def _cut(mask: np.ndarray, condition: np.ndarray, label: str, flow: list[dict[str, Any]]) -> np.ndarray:
    updated = mask & np.asarray(condition, dtype=bool)
    flow.append({"cut": label, "remaining": int(updated.sum())})
    return updated


def build_sample(
    source: str | Path,
    *,
    max_stars: int = DEFAULT_MAX_STARS,
    seed: int = DEFAULT_SEED,
) -> tuple[QTable, dict[str, Any]]:
    """Create a deterministic quality-filtered teaching sample in memory."""

    if max_stars < 1:
        raise ValueError("max_stars must be positive")
    source_path = verify_source(source)
    source_retrieval = ensure_source_provenance(source_path)
    rv, fibermap, _scores, gaia, association = _read_and_validate(source_path)

    mask = np.ones(len(rv), dtype=bool)
    flow: list[dict[str, Any]] = [{"cut": "source rows", "remaining": len(rv)}]
    mask = _cut(mask, rv["SUCCESS"] == True, "SUCCESS == True", flow)  # noqa: E712
    mask = _cut(mask, rv["RVS_WARN"] == 0, "RVS_WARN == 0", flow)
    spectype = np.char.strip(np.asarray(rv["RR_SPECTYPE"], dtype="U"))
    mask = _cut(mask, spectype == "STAR", 'RR_SPECTYPE == "STAR"', flow)
    mask = _cut(mask, fibermap["COADD_FIBERSTATUS"] == 0, "COADD_FIBERSTATUS == 0", flow)
    mask = _cut(mask, np.isfinite(rv["VRAD"]) & np.isfinite(rv["VRAD_ERR"]), "finite VRAD and VRAD_ERR", flow)
    mask = _cut(mask, rv["VRAD_ERR"] <= 5.0, "VRAD_ERR <= 5 km/s", flow)

    finite_columns = (
        "RA", "RA_ERROR", "DEC", "DEC_ERROR", "PARALLAX", "PARALLAX_ERROR",
        "PMRA", "PMRA_ERROR", "PMDEC", "PMDEC_ERROR",
    )
    finite_astrometry = np.logical_and.reduce([np.isfinite(gaia[name]) for name in finite_columns])
    mask = _cut(mask, finite_astrometry, "finite Gaia astrometry and required uncertainties", flow)
    mask = _cut(mask, gaia["ASTROMETRIC_PARAMS_SOLVED"] == 31, "ASTROMETRIC_PARAMS_SOLVED == 31", flow)
    mask = _cut(mask, gaia["VISIBILITY_PERIODS_USED"] >= 8, "VISIBILITY_PERIODS_USED >= 8", flow)
    mask = _cut(mask, gaia["RUWE"] < 1.4, "RUWE < 1.4 (conventional heuristic)", flow)
    mask = _cut(mask, ~gaia["DUPLICATED_SOURCE"], "DUPLICATED_SOURCE == False", flow)
    mask = _cut(mask, gaia["PARALLAX"] > 0.5, "PARALLAX > 0.5 mas", flow)
    mask = _cut(mask, gaia["PARALLAX_OVER_ERROR"] >= 20.0, "PARALLAX_OVER_ERROR >= 20", flow)

    selected = np.flatnonzero(mask)
    snr_rank = np.nan_to_num(rv["SN_R"][selected].astype(float), nan=-np.inf)
    order = np.lexsort(
        (rv["TARGETID"][selected], -snr_rank, rv["VRAD_ERR"][selected], gaia["SOURCE_ID"][selected])
    )
    ranked = selected[order]
    _, first = np.unique(gaia["SOURCE_ID"][ranked], return_index=True)
    deduplicated = ranked[np.sort(first)]
    flow.append(
        {"cut": "deduplicate Gaia DR3 SOURCE_ID by VRAD_ERR, -SN_R, TARGETID", "remaining": int(len(deduplicated))}
    )

    if len(deduplicated) < MINIMUM_STARS:
        raise SampleBuildError(
            f"Only {len(deduplicated)} stars pass the fixed quality cuts (< {MINIMUM_STARS}); "
            f"stop before changing cuts. Cut flow: {flow}"
        )
    if len(deduplicated) > max_stars:
        rng = np.random.default_rng(seed)
        final_rows = np.sort(rng.choice(deduplicated, size=max_stars, replace=False))
        flow.append(
            {"cut": f"deterministic random sample (seed={seed}, maximum={max_stars})", "remaining": int(max_stars)}
        )
    else:
        final_rows = np.sort(deduplicated)
        flow.append({"cut": "retain all because sample is below maximum", "remaining": int(len(final_rows))})

    output = QTable()
    output["source_row"] = final_rows.astype(np.int64)
    output["targetid"] = np.asarray(rv["TARGETID"][final_rows], dtype=np.int64)
    output["gaia_dr3_source_id"] = np.asarray(gaia["SOURCE_ID"][final_rows], dtype=np.int64)
    output["ra"] = np.asarray(gaia["RA"][final_rows], dtype=float) * u.deg
    output["dec"] = np.asarray(gaia["DEC"][final_rows], dtype=float) * u.deg
    output["ra_error"] = np.asarray(gaia["RA_ERROR"][final_rows], dtype=float) * u.mas
    output["dec_error"] = np.asarray(gaia["DEC_ERROR"][final_rows], dtype=float) * u.mas
    output["parallax"] = np.asarray(gaia["PARALLAX"][final_rows], dtype=float) * u.mas
    output["parallax_error"] = np.asarray(gaia["PARALLAX_ERROR"][final_rows], dtype=float) * u.mas
    output["parallax_over_error"] = np.asarray(gaia["PARALLAX_OVER_ERROR"][final_rows], dtype=float)
    output["pmra"] = np.asarray(gaia["PMRA"][final_rows], dtype=float) * u.mas / u.yr
    output["pmra_error"] = np.asarray(gaia["PMRA_ERROR"][final_rows], dtype=float) * u.mas / u.yr
    output["pmdec"] = np.asarray(gaia["PMDEC"][final_rows], dtype=float) * u.mas / u.yr
    output["pmdec_error"] = np.asarray(gaia["PMDEC_ERROR"][final_rows], dtype=float) * u.mas / u.yr
    output["radial_velocity"] = np.asarray(rv["VRAD"][final_rows], dtype=float) * u.km / u.s
    output["radial_velocity_error"] = np.asarray(rv["VRAD_ERR"][final_rows], dtype=float) * u.km / u.s
    output["sn_r"] = np.asarray(rv["SN_R"][final_rows], dtype=float)
    output["astrometric_params_solved"] = np.asarray(gaia["ASTROMETRIC_PARAMS_SOLVED"][final_rows], dtype=np.int16)
    output["visibility_periods_used"] = np.asarray(gaia["VISIBILITY_PERIODS_USED"][final_rows], dtype=np.int16)
    output["ruwe"] = np.asarray(gaia["RUWE"][final_rows], dtype=float)
    output["duplicated_source"] = np.asarray(gaia["DUPLICATED_SOURCE"][final_rows], dtype=bool)
    output["distance"] = (1.0 / output["parallax"].to_value(u.mas)) * u.kpc

    descriptions = {
        "source_row": "Zero-based row index in every associated source extension",
        "targetid": "Unique DESI target identifier",
        "gaia_dr3_source_id": "Gaia DR3 source identifier",
        "ra": "Gaia DR3 ICRS right ascension",
        "dec": "Gaia DR3 ICRS declination",
        "ra_error": "Gaia DR3 right-ascension standard uncertainty",
        "dec_error": "Gaia DR3 declination standard uncertainty",
        "parallax": "Gaia DR3 parallax; no zero-point correction applied",
        "parallax_error": "Gaia DR3 parallax standard uncertainty",
        "parallax_over_error": "Gaia DR3 parallax divided by its uncertainty",
        "pmra": "Gaia DR3 mu_alpha* = d(alpha)/dt cos(delta)",
        "pmra_error": "Gaia DR3 mu_alpha* standard uncertainty",
        "pmdec": "Gaia DR3 declination proper motion",
        "pmdec_error": "Gaia DR3 declination-proper-motion uncertainty",
        "radial_velocity": "DESI RVSpecFit line-of-sight velocity, positive receding",
        "radial_velocity_error": "DESI RVSpecFit radial-velocity uncertainty",
        "sn_r": "DESI RVSpecFit median signal-to-noise in the R arm",
        "astrometric_params_solved": "Gaia DR3 astrometric solution bit field",
        "visibility_periods_used": "Gaia DR3 visibility periods used",
        "ruwe": "Gaia DR3 renormalised unit weight error",
        "duplicated_source": "Gaia DR3 duplicated-source flag",
        "distance": "Pedagogical inverse-parallax distance: 1/parallax[mas] kpc",
    }
    for name, description in descriptions.items():
        output[name].description = description
    output.meta = {
        "title": "Compact DESI DR1 SV2 bright / Gaia DR3 phase-space teaching sample",
        "source_release": SOURCE_RELEASE,
        "source_filename": SOURCE_FILENAME,
        "source_url": SOURCE_URL,
        "source_sha256": SOURCE_SHA256,
        "seed": seed,
        "maximum_rows": max_stars,
        "distance_method": "d[kpc] = 1 / parallax[mas]; no Gaia parallax zero-point correction",
        "limitations": "Nearby high-S/N teaching sample; not DESI main survey, Lambert DR2, or selection-function representative",
    }

    provenance = {
        "schema_version": 1,
        "track": "A: public DESI DR1/Gaia-backed educational workflow",
        "not_lambert_dr2": True,
        "purpose": "Compact real-data sample solely for teaching coordinate transformations",
        "catalogue_release": SOURCE_RELEASE,
        "survey": "sv2",
        "program": "bright",
        "authoritative_source_url": SOURCE_URL,
        "documentation_urls": [SOURCE_DOCUMENTATION, DATA_MODEL_DOCUMENTATION],
        "source_table_or_hdu": list(REQUIRED_EXTENSIONS),
        "source_columns_and_units": {
            "RVTAB": {"VRAD": "km/s", "VRAD_ERR": "km/s", "SN_R": "dimensionless", "TARGETID": None, "SUCCESS": None, "RVS_WARN": None, "RR_SPECTYPE": None},
            "FIBERMAP": {"TARGETID": None, "TARGET_RA": "deg", "TARGET_DEC": "deg", "COADD_FIBERSTATUS": None},
            "SCORES": {"TARGETID": None},
            "GAIA": {"SOURCE_ID": None, "RA": "deg", "RA_ERROR": "mas", "DEC": "deg", "DEC_ERROR": "mas", "PARALLAX": "mas", "PARALLAX_ERROR": "mas", "PARALLAX_OVER_ERROR": None, "PMRA": "mas/yr (mu_alpha*)", "PMRA_ERROR": "mas/yr", "PMDEC": "mas/yr", "PMDEC_ERROR": "mas/yr", "ASTROMETRIC_PARAMS_SOLVED": None, "VISIBILITY_PERIODS_USED": None, "RUWE": None, "DUPLICATED_SOURCE": None},
        },
        "source_units_note": "Several Gaia TUNIT cards are absent in this file; units follow the official rvpix data model and Gaia DR3 definitions.",
        "query_or_extraction_rule": "Read named RVTAB/FIBERMAP/SCORES/GAIA extensions and validate row association before fixed Task 3A cuts.",
        "row_selection_rule": "Sequential cut_flow, deterministic Gaia SOURCE_ID deduplication, then ordinary seeded random selection without replacement.",
        "retrieval_timestamp": source_retrieval["retrieved_at"],
        "source_checksums": {"sha256": SOURCE_SHA256},
        "source_byte_size": SOURCE_SIZE,
        "source_row_association": association,
        "quality_cut_note": "RUWE < 1.4 is a conventional heuristic, not a universal Gaia truth.",
        "distance_note": "Inverse parallax is used only for this nearby, positive-parallax, >=20-sigma pedagogical sample; no parallax zero-point correction is applied.",
        "deduplication": ["smallest VRAD_ERR", "highest SN_R", "lowest TARGETID"],
        "cut_flow": flow,
        "parameters": {"seed": seed, "maximum_rows": max_stars, "minimum_acceptable_rows": MINIMUM_STARS},
        "producing_script": "scripts/build_public_demo_sample.py",
        "producing_script_version": SCRIPT_VERSION,
        "package_version": __version__,
        "parent_filenames_and_checksums": [{"filename": SOURCE_FILENAME, "sha256": SOURCE_SHA256}],
        "final_sample_rows": len(output),
    }
    return output, provenance


def write_sample(
    table: QTable,
    provenance: dict[str, Any],
    output: str | Path,
    provenance_path: str | Path,
) -> dict[str, Any]:
    """Write ECSV and provenance JSON atomically and return final metadata."""

    output_path = Path(output).expanduser().resolve()
    provenance_output = Path(provenance_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_output.parent.mkdir(parents=True, exist_ok=True)

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{output_path.name}.", suffix=".part", dir=output_path.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
        table.write(temporary, format="ascii.ecsv", overwrite=True)
        os.replace(temporary, output_path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    final_provenance = dict(provenance)
    final_provenance["output"] = {
        "filename": output_path.name,
        "row_count": len(table),
        "sha256": file_checksum(output_path),
    }
    _atomic_json(final_provenance, provenance_output)
    return final_provenance
