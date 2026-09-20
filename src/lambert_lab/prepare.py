"""Verified, offline-capable preparation of Lambert's released FITS products."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .data import (
    DEFAULT_RECORD_ID,
    PROVENANCE_FILENAME,
    CacheIntegrityError,
    FetchError,
    fetch_zenodo_release,
)
from .inventory import DEFAULT_ARCHIVE_NAME
from .validation import file_checksum


class PreparationError(RuntimeError):
    """Raised when the local Lambert cache cannot be safely prepared."""


@dataclass(frozen=True)
class PreparationSummary:
    """Counts from one deterministic preparation run."""

    archive: Path
    extracted_directory: Path
    verified_archive_checksum: str
    reused: int
    extracted: int
    repaired: int
    products: int


def _load_inventory(path: Path) -> dict[str, Any]:
    try:
        inventory = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PreparationError(f"Cannot read committed data inventory {path}: {error}") from error
    if inventory.get("inventory_kind") != "Lambert author-released figure-data forensic inventory":
        raise PreparationError(f"Not the expected Lambert inventory: {path}")
    return inventory


def _safe_member_name(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or "\\" in name or any(part in {"", ".", ".."} for part in path.parts):
        raise PreparationError(f"Unsafe ZIP member path: {name!r}")
    return path


def _products_from_inventory(inventory: dict[str, Any]) -> dict[str, str]:
    products: dict[str, str] = {}
    for member in inventory.get("archive_members", []):
        if member.get("valid_fits") is not True:
            continue
        name = member.get("archive_path")
        checksum = member.get("sha256")
        if not isinstance(name, str) or not isinstance(checksum, str) or len(checksum) != 64:
            raise PreparationError("Inventory has an invalid scientific-product checksum entry")
        path = _safe_member_name(name)
        # The published inventory intentionally defines the extracted layout as
        # a flat FITS collection.  This also prevents archive path surprises.
        if len(path.parts) != 1 or not name.lower().endswith(".fits"):
            raise PreparationError(f"Inventory scientific product is not a flat FITS file: {name!r}")
        if name in products:
            raise PreparationError(f"Inventory repeats scientific product {name!r}")
        products[name] = checksum.lower()
    if not products:
        raise PreparationError("Inventory contains no valid scientific FITS products")
    return products


def _archive_from_verified_provenance(cache_directory: Path) -> tuple[Path, str]:
    provenance_path = cache_directory / PROVENANCE_FILENAME
    try:
        manifest = json.loads(provenance_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise PreparationError(
            f"No verified Lambert cache provenance at {provenance_path}. "
            "Run this command once with --download."
        ) from error
    except (OSError, json.JSONDecodeError) as error:
        raise PreparationError(f"Cannot read cache provenance {provenance_path}: {error}") from error

    if str(manifest.get("requested_record_id")) != DEFAULT_RECORD_ID or str(manifest.get("resolved_record_id")) != DEFAULT_RECORD_ID:
        raise PreparationError("Cache provenance is not for the pinned Lambert Zenodo record 18236902")
    entries = [entry for entry in manifest.get("files", []) if entry.get("filename") == DEFAULT_ARCHIVE_NAME]
    if len(entries) != 1:
        raise PreparationError(f"Cache provenance must describe exactly one {DEFAULT_ARCHIVE_NAME}")
    entry = entries[0]
    size = entry.get("byte_size")
    advertised = entry.get("advertised_checksum")
    verified = entry.get("verified_checksum")
    if not isinstance(size, int) or size < 0 or not isinstance(advertised, str) or advertised != verified:
        raise PreparationError("Cache provenance has no matching advertised and verified archive checksum")
    try:
        algorithm, expected = advertised.split(":", 1)
    except ValueError as error:
        raise PreparationError("Cache provenance has an invalid archive checksum") from error
    if algorithm.lower() not in {"md5", "sha256"} or not expected:
        raise PreparationError("Cache provenance uses an unsupported archive checksum")
    archive = cache_directory / DEFAULT_ARCHIVE_NAME
    if not archive.is_file():
        raise PreparationError(f"Verified archive is missing: {archive}. Run with --download.")
    if archive.stat().st_size != size:
        raise PreparationError(f"Archive size does not match provenance: {archive}")
    actual = file_checksum(archive, algorithm.lower()).lower()
    if actual != expected.lower():
        raise PreparationError(f"Archive checksum does not match provenance: {archive}")
    return archive, f"{algorithm.lower()}:{actual}"


def prepare_lambert_products(
    repository_root: str | Path,
    *,
    cache_directory: str | Path | None = None,
    download: bool = False,
) -> PreparationSummary:
    """Verify a pinned archive and extract all inventoried FITS products.

    Networking happens only when ``download`` is true.  Existing extracted
    files are checksum-verified and reused; a bad one is atomically repaired
    from the already-verified ZIP rather than being accepted.
    """

    root = Path(repository_root).resolve()
    cache = Path(cache_directory).resolve() if cache_directory is not None else root / "data" / "raw" / "lambert_zenodo"
    inventory = _load_inventory(root / "data" / "data_inventory.json")
    products = _products_from_inventory(inventory)
    if download:
        try:
            fetch_zenodo_release(cache, record_id=DEFAULT_RECORD_ID)
        except (FetchError, OSError, ValueError) as error:
            raise PreparationError(f"Unable to fetch the pinned Lambert release: {error}") from error
    archive, archive_checksum = _archive_from_verified_provenance(cache)
    extracted_directory = cache / "extracted"
    extracted_directory.mkdir(parents=True, exist_ok=True)
    # Earlier private working copies may contain macOS ZIP metadata.  It is not
    # a scientific product and is never retained by this public preparer.
    appledouble_directory = extracted_directory / "__MACOSX"
    if appledouble_directory.is_symlink():
        appledouble_directory.unlink()
    elif appledouble_directory.is_dir():
        shutil.rmtree(appledouble_directory)

    reused = extracted = repaired = 0
    try:
        with zipfile.ZipFile(archive) as source:
            infos: dict[str, zipfile.ZipInfo] = {}
            for info in source.infolist():
                _safe_member_name(info.filename)
                if info.filename in infos:
                    raise PreparationError(f"Duplicate ZIP member for {info.filename!r}")
                infos[info.filename] = info
            missing = sorted(set(products) - set(infos))
            if missing:
                raise PreparationError(f"Verified archive lacks inventoried product(s): {', '.join(missing)}")

            for name, expected_checksum in products.items():
                destination = extracted_directory / name
                if destination.is_symlink() or (destination.exists() and not destination.is_file()):
                    raise PreparationError(f"Extracted product path is not a regular file: {destination}")
                if destination.exists() and destination.is_file() and file_checksum(destination) == expected_checksum:
                    reused += 1
                    continue
                was_corrupt = destination.exists()
                payload = source.read(infos[name])
                actual_checksum = hashlib.sha256(payload).hexdigest()
                if actual_checksum != expected_checksum:
                    raise PreparationError(
                        f"Archive product checksum does not match committed inventory: {name}"
                    )
                with tempfile.NamedTemporaryFile(
                    mode="wb", prefix=f".{name}.", suffix=".part", dir=extracted_directory, delete=False
                ) as temporary:
                    temporary.write(payload)
                    temporary_path = Path(temporary.name)
                try:
                    if file_checksum(temporary_path) != expected_checksum:
                        raise PreparationError(f"Written product checksum mismatch: {name}")
                    os.replace(temporary_path, destination)
                finally:
                    temporary_path.unlink(missing_ok=True)
                if was_corrupt:
                    repaired += 1
                else:
                    extracted += 1
    except zipfile.BadZipFile as error:
        raise PreparationError(f"Verified archive is not a readable ZIP: {archive}") from error

    return PreparationSummary(
        archive=archive,
        extracted_directory=extracted_directory,
        verified_archive_checksum=archive_checksum,
        reused=reused,
        extracted=extracted,
        repaired=repaired,
        products=len(products),
    )
