"""Offline Lambert-product loaders and verified data download infrastructure.

Network access occurs only when :func:`fetch_zenodo_release` is called explicitly.
"""

from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, BinaryIO

import astropy.units as u
import numpy as np
from astropy.io import fits
from astropy.table import QTable

from .validation import file_checksum, require_local_file

DEFAULT_RECORD_ID = "18236902"
DEFAULT_API_BASE = "https://zenodo.org/api/records"
PROVENANCE_FILENAME = "_release_provenance.json"
USER_AGENT = "lambert-anticentre-lab/0.1 (+verified educational data fetch)"


@dataclass(frozen=True)
class ReleasedImage:
    """One fixed author-binned Lambert image plus inventory display metadata."""

    filename: str
    data: np.ndarray
    extent: tuple[float, float, float, float]
    horizontal_axis: Mapping[str, Any]
    vertical_axis: Mapping[str, Any]
    quantity: str
    value_kind: str
    value_unit: str
    figure: int
    panel: str
    selection: str
    sha256: str


FIGURE_13_COLUMNS = {
    "Galactic latitude [deg]": ("b", u.deg),
    "Galactic longitude [deg]": ("l", u.deg),
    "vertical velocity [km/s]": ("V_Z", u.km / u.s),
    "radial velocity [km/s]": ("V_R", u.km / u.s),
}


@lru_cache(maxsize=4)
def _read_inventory(inventory_path: Path) -> dict[str, Any]:
    with inventory_path.open(encoding="utf-8") as stream:
        inventory = json.load(stream)
    if inventory.get("inventory_kind") != "Lambert author-released figure-data forensic inventory":
        raise ValueError(f"Not the expected Lambert inventory: {inventory_path}")
    return inventory


def load_lambert_inventory(repository_root: str | Path) -> dict[str, Any]:
    """Load the committed Task 2 inventory without any network access."""

    root = Path(repository_root).expanduser().resolve()
    return _read_inventory(root / "data" / "data_inventory.json")


def _inventory_member(repository_root: Path, filename: str) -> dict[str, Any]:
    inventory = load_lambert_inventory(repository_root)
    matches = [
        member for member in inventory["archive_members"]
        if member.get("filename") == filename and member.get("valid_fits") is True
    ]
    if len(matches) != 1:
        raise KeyError(f"Expected one valid inventory entry for {filename!r}; found {len(matches)}")
    return matches[0]


def lambert_product_path(
    repository_root: str | Path, filename: str, *, verify_checksum: bool = True
) -> Path:
    """Resolve an extracted cached product and optionally verify its Task 2 checksum."""

    root = Path(repository_root).expanduser().resolve()
    member = _inventory_member(root, filename)
    path = root / "data" / "raw" / "lambert_zenodo" / "extracted" / filename
    require_local_file(path, purpose=f"Lambert released product {filename}")
    if verify_checksum:
        actual = file_checksum(path)
        if actual != member["sha256"]:
            raise CacheIntegrityError(
                f"SHA-256 mismatch for {path}: expected {member['sha256']}, found {actual}"
            )
    return path


def load_released_image(repository_root: str | Path, filename: str) -> ReleasedImage:
    """Load a fixed 2-D author product using orientation/extents from the inventory."""

    root = Path(repository_root).expanduser().resolve()
    member = _inventory_member(root, filename)
    if member["asset_type"] != "FITS 2-D image array":
        raise TypeError(f"{filename} is not inventoried as a 2-D image array")
    image_axes = member["fits"]["image_axes"]
    orientation = image_axes["orientation_for_paper"]
    if orientation["origin"] != "lower" or orientation["transpose_required"]:
        raise ValueError(f"Unsupported inventoried orientation for {filename}")
    path = lambert_product_path(root, filename)
    values = np.asarray(fits.getdata(path, ext=0), dtype=float)
    expected_shape = tuple(member["fits"]["hdus"][0]["shape"])
    if values.shape != expected_shape:
        raise ValueError(f"Shape mismatch for {filename}: {values.shape} != {expected_shape}")
    semantics = member["scientific_semantics"]
    return ReleasedImage(
        filename=filename,
        data=values,
        extent=tuple(orientation["extent"]),
        horizontal_axis=image_axes["horizontal_axis"],
        vertical_axis=image_axes["vertical_axis"],
        quantity=semantics["quantity"],
        value_kind=semantics["value_kind"],
        value_unit=semantics["value_unit"],
        figure=semantics["figure"],
        panel=semantics["panel"],
        selection=semantics["selection"],
        sha256=member["sha256"],
    )


def load_figure13_stars(repository_root: str | Path) -> QTable:
    """Load the 7,708 released Figure 13/14 rows with explicit physical units."""

    root = Path(repository_root).expanduser().resolve()
    filename = "fig13_and_fig14_table.fits"
    member = _inventory_member(root, filename)
    path = lambert_product_path(root, filename)
    raw = QTable.read(path, hdu=1)
    if set(raw.colnames) != set(FIGURE_13_COLUMNS):
        raise ValueError(f"Unexpected columns in {filename}: {raw.colnames}")
    table = QTable()
    for released_name, (short_name, unit) in FIGURE_13_COLUMNS.items():
        table[short_name] = np.asarray(raw[released_name], dtype=float) * unit
    expected_rows = member["fits"]["hdus"][1]["row_count"]
    if len(table) != expected_rows:
        raise ValueError(f"Row-count mismatch for {filename}: {len(table)} != {expected_rows}")
    table.meta.update(
        source_filename=filename,
        source_hdu=1,
        source_sha256=member["sha256"],
        representation="individual rows from the authors' already-selected sample",
    )
    return table


class FetchError(RuntimeError):
    """Base class for actionable release-fetch errors."""


class ReleaseMetadataError(FetchError):
    """Raised when release metadata cannot support a verified fetch."""


class CacheIntegrityError(FetchError):
    """Raised when an existing or downloaded file fails verification."""


UrlOpener = Callable[..., BinaryIO]


def _request_bytes(url: str, *, timeout: float, opener: UrlOpener) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener(request, timeout=timeout) as response:
            return response.read()
    except (OSError, urllib.error.URLError) as error:
        raise FetchError(f"Unable to retrieve {url}: {error}") from error


def _request_json(url: str, *, timeout: float, opener: UrlOpener) -> Mapping[str, Any]:
    payload = _request_bytes(url, timeout=timeout, opener=opener)
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseMetadataError(f"Invalid JSON metadata returned by {url}") from error
    if not isinstance(value, dict):
        raise ReleaseMetadataError(f"Expected a JSON object from {url}")
    return value


def _checksum_parts(value: object, *, filename: str) -> tuple[str, str]:
    if not isinstance(value, str) or ":" not in value:
        raise ReleaseMetadataError(
            f"Zenodo metadata has no usable checksum for {filename!r}"
        )
    algorithm, expected = value.split(":", 1)
    algorithm = algorithm.lower()
    if algorithm not in {"md5", "sha256"} or not expected:
        raise ReleaseMetadataError(
            f"Unsupported checksum declaration for {filename!r}: {value!r}"
        )
    return algorithm, expected.lower()


def _safe_filename(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ReleaseMetadataError("Zenodo file entry is missing a filename")
    if Path(value).name != value or value in {".", ".."}:
        raise ReleaseMetadataError(f"Unsafe filename in Zenodo metadata: {value!r}")
    return value


def _verify_file(
    path: Path,
    *,
    expected_size: int,
    checksum_algorithm: str,
    expected_checksum: str,
) -> str:
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise CacheIntegrityError(
            f"Size mismatch for {path}: expected {expected_size} bytes, "
            f"found {actual_size}. Move or remove the unverified file explicitly "
            "before retrying; it will not be overwritten."
        )
    actual_checksum = file_checksum(path, checksum_algorithm)
    if actual_checksum.lower() != expected_checksum.lower():
        raise CacheIntegrityError(
            f"Checksum mismatch for {path}: expected "
            f"{checksum_algorithm}:{expected_checksum}, found "
            f"{checksum_algorithm}:{actual_checksum}. Move or remove the "
            "unverified file explicitly before retrying; it will not be overwritten."
        )
    return actual_checksum


def _download_verified(
    url: str,
    destination: Path,
    *,
    expected_size: int,
    checksum_algorithm: str,
    expected_checksum: str,
    timeout: float,
    opener: UrlOpener,
) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    temporary_path: Path | None = None
    try:
        with opener(request, timeout=timeout) as response:
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{destination.name}.", suffix=".part",
                dir=destination.parent, delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                while chunk := response.read(1024 * 1024):
                    temporary.write(chunk)
        verified = _verify_file(
            temporary_path,
            expected_size=expected_size,
            checksum_algorithm=checksum_algorithm,
            expected_checksum=expected_checksum,
        )
        os.replace(temporary_path, destination)
        temporary_path = None
        return verified
    except CacheIntegrityError:
        raise
    except (OSError, urllib.error.URLError) as error:
        raise FetchError(f"Unable to download {url}: {error}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _creator_names(metadata: Mapping[str, Any]) -> list[str]:
    creators = metadata.get("creators", [])
    if not isinstance(creators, list):
        return []
    return [
        str(creator["name"])
        for creator in creators
        if isinstance(creator, dict) and creator.get("name")
    ]


def _license_value(metadata: Mapping[str, Any]) -> str | None:
    license_metadata = metadata.get("license")
    if isinstance(license_metadata, str):
        return license_metadata
    if isinstance(license_metadata, dict):
        value = license_metadata.get("id") or license_metadata.get("title")
        return str(value) if value is not None else None
    return None


def fetch_zenodo_release(
    destination: str | Path,
    *,
    record_id: str = DEFAULT_RECORD_ID,
    api_base: str = DEFAULT_API_BASE,
    timeout: float = 60.0,
    opener: UrlOpener = urllib.request.urlopen,
) -> dict[str, Any]:
    """Fetch and verify every file in an exact Zenodo record.

    Existing files are accepted only after their size and advertised checksum
    pass. A failed cache entry is never overwritten. The returned dictionary is
    also written atomically as ``_release_provenance.json`` in ``destination``.
    This transfer manifest is not the scientific inventory owned by Task 2.
    """

    if not record_id or any(character not in "0123456789" for character in record_id):
        raise ValueError("record_id must contain only decimal digits")
    if timeout <= 0:
        raise ValueError("timeout must be positive")

    destination_path = Path(destination).expanduser().resolve()
    destination_path.mkdir(parents=True, exist_ok=True)
    if not destination_path.is_dir():
        raise FetchError(f"Destination is not a directory: {destination_path}")

    metadata_url = f"{api_base.rstrip('/')}/{record_id}"
    record = _request_json(metadata_url, timeout=timeout, opener=opener)
    resolved_id = record.get("id")
    if not isinstance(resolved_id, int | str):
        raise ReleaseMetadataError("Zenodo metadata is missing the resolved record id")

    files = record.get("files")
    if not isinstance(files, list) or not files:
        raise ReleaseMetadataError("Zenodo record contains no downloadable files")

    file_manifest: list[dict[str, Any]] = []
    for entry in files:
        if not isinstance(entry, dict):
            raise ReleaseMetadataError("Malformed file entry in Zenodo metadata")
        filename = _safe_filename(entry.get("key"))
        size = entry.get("size")
        if not isinstance(size, int) or size < 0:
            raise ReleaseMetadataError(f"Invalid size for {filename!r}: {size!r}")
        checksum_algorithm, advertised_checksum = _checksum_parts(
            entry.get("checksum"), filename=filename
        )
        links = entry.get("links")
        download_url = links.get("self") if isinstance(links, dict) else None
        if not isinstance(download_url, str) or not download_url:
            raise ReleaseMetadataError(f"No download URL supplied for {filename!r}")

        local_path = destination_path / filename
        if local_path.exists():
            if not local_path.is_file():
                raise CacheIntegrityError(f"Cache path is not a file: {local_path}")
            actual_checksum = _verify_file(
                local_path,
                expected_size=size,
                checksum_algorithm=checksum_algorithm,
                expected_checksum=advertised_checksum,
            )
            cache_status = "verified-cache"
        else:
            actual_checksum = _download_verified(
                download_url,
                local_path,
                expected_size=size,
                checksum_algorithm=checksum_algorithm,
                expected_checksum=advertised_checksum,
                timeout=timeout,
                opener=opener,
            )
            cache_status = "downloaded"

        file_manifest.append(
            {
                "filename": filename,
                "source_url": download_url,
                "byte_size": size,
                "advertised_checksum": f"{checksum_algorithm}:{advertised_checksum}",
                "verified_checksum": f"{checksum_algorithm}:{actual_checksum}",
                "cache_status": cache_status,
            }
        )

    release_metadata = record.get("metadata")
    if not isinstance(release_metadata, dict):
        release_metadata = {}
    links = record.get("links")
    if not isinstance(links, dict):
        links = {}

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "requested_record_id": record_id,
        "resolved_record_id": str(resolved_id),
        "concept_record_id": str(record.get("conceptrecid", "")) or None,
        "doi": record.get("doi") or release_metadata.get("doi"),
        "record_url": links.get("html") or links.get("self") or metadata_url,
        "metadata_source_url": metadata_url,
        "title": release_metadata.get("title"),
        "version": release_metadata.get("version"),
        "publication_date": release_metadata.get("publication_date"),
        "creators": _creator_names(release_metadata),
        "license": _license_value(release_metadata),
        "citation": release_metadata.get("citation"),
        "files": file_manifest,
    }

    manifest_path = destination_path / PROVENANCE_FILENAME
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix=f".{PROVENANCE_FILENAME}.",
        suffix=".part", dir=destination_path, delete=False
    ) as temporary:
        temporary_manifest = Path(temporary.name)
        json.dump(manifest, temporary, indent=2, sort_keys=True)
        temporary.write("\n")
    os.replace(temporary_manifest, manifest_path)
    return manifest
