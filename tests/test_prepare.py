from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from lambert_lab.prepare import PreparationError, prepare_lambert_products


def _fixture(root: Path, *, unsafe_member: str | None = None) -> tuple[Path, bytes]:
    payload = b"small synthetic FITS product"
    checksum = hashlib.sha256(payload).hexdigest()
    (root / "data").mkdir()
    inventory = {
        "inventory_kind": "Lambert author-released figure-data forensic inventory",
        "archive_members": [
            {
                "archive_path": "panel.fits",
                "filename": "panel.fits",
                "valid_fits": True,
                "sha256": checksum,
            },
            {
                "archive_path": "__MACOSX/._panel.fits",
                "filename": "._panel.fits",
                "valid_fits": False,
                "sha256": hashlib.sha256(b"metadata").hexdigest(),
            },
        ],
    }
    (root / "data" / "data_inventory.json").write_text(json.dumps(inventory))
    cache = root / "cache"
    cache.mkdir()
    archive = cache / "Lambert_DESI_DR2_MW_outer_disk_figures_data.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("panel.fits", payload)
        output.writestr("__MACOSX/._panel.fits", b"metadata")
        if unsafe_member is not None:
            output.writestr(unsafe_member, b"unsafe")
    digest = hashlib.md5(archive.read_bytes()).hexdigest()  # noqa: S324
    provenance = {
        "requested_record_id": "18236902",
        "resolved_record_id": "18236902",
        "files": [
            {
                "filename": archive.name,
                "byte_size": archive.stat().st_size,
                "advertised_checksum": f"md5:{digest}",
                "verified_checksum": f"md5:{digest}",
            }
        ],
    }
    (cache / "_release_provenance.json").write_text(json.dumps(provenance))
    return cache, payload


def test_prepare_is_offline_reuses_verified_product_and_repairs_bad_one(tmp_path: Path) -> None:
    cache, payload = _fixture(tmp_path)
    first = prepare_lambert_products(tmp_path, cache_directory=cache)
    product = cache / "extracted" / "panel.fits"
    assert product.read_bytes() == payload
    assert (cache / "extracted" / "__MACOSX").exists() is False
    assert (first.products, first.extracted, first.reused, first.repaired) == (1, 1, 0, 0)

    second = prepare_lambert_products(tmp_path, cache_directory=cache)
    assert (second.extracted, second.reused, second.repaired) == (0, 1, 0)

    product.write_bytes(b"corrupted extracted content")
    repaired = prepare_lambert_products(tmp_path, cache_directory=cache)
    assert product.read_bytes() == payload
    assert (repaired.extracted, repaired.reused, repaired.repaired) == (0, 0, 1)


def test_prepare_refuses_unsafe_zip_paths(tmp_path: Path) -> None:
    cache, _ = _fixture(tmp_path, unsafe_member="../escape.fits")
    with pytest.raises(PreparationError, match="Unsafe ZIP member path"):
        prepare_lambert_products(tmp_path, cache_directory=cache)


def test_prepare_requires_provenance_without_download(tmp_path: Path) -> None:
    cache, _ = _fixture(tmp_path)
    (cache / "_release_provenance.json").unlink()
    with pytest.raises(PreparationError, match="No verified Lambert cache provenance"):
        prepare_lambert_products(tmp_path, cache_directory=cache)
