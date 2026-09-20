from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from lambert_lab.inventory import PRODUCT_SEMANTICS, build_inventory, write_inventory


def _fits_bytes(filename: str) -> bytes:
    output = io.BytesIO()
    if filename == "Lz_Vr_fig9.fits":
        columns = [
            fits.Column(name="angular momentum [kpc km/s]", format="D", array=[1.0]),
            fits.Column(name="radial velocity [km/s]", format="D", array=[2.0]),
            fits.Column(name="radial velocity uncertainty [km/s]", format="D", array=[0.1]),
        ]
        fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns(columns)]).writeto(output)
    elif filename == "FFT_fig10.fits":
        columns = [
            fits.Column(name="Frequency of Vr in 1/Lz", format="D", array=[1.0]),
            fits.Column(name="Power", format="D", array=[2.0]),
            fits.Column(name="1-sigma on the Power", format="D", array=[0.1]),
        ]
        fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns(columns)]).writeto(output)
    elif filename == "fig13_and_fig14_table.fits":
        columns = [
            fits.Column(name="Galactic latitude [deg]", format="D", array=[25.0]),
            fits.Column(name="Galactic longitude [deg]", format="D", array=[175.0]),
            fits.Column(name="vertical velocity [km/s]", format="D", array=[3.0]),
            fits.Column(name="radial velocity [km/s]", format="D", array=[-4.0]),
        ]
        fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns(columns)]).writeto(output)
    else:
        fits.PrimaryHDU(np.array([[1.0]], dtype=np.float64)).writeto(output)
    return output.getvalue()


def _synthetic_release(tmp_path: Path) -> tuple[Path, Path]:
    archive = tmp_path / "release.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for filename in PRODUCT_SEMANTICS:
            output.writestr(filename, _fits_bytes(filename))
        output.writestr("__MACOSX/._FFT_fig10.fits", b"AppleDouble metadata")
    digest = hashlib.md5(archive.read_bytes()).hexdigest()  # noqa: S324
    provenance = {
        "requested_record_id": "1",
        "resolved_record_id": "1",
        "concept_record_id": "0",
        "doi": "10.5281/zenodo.1",
        "record_url": "https://example.invalid/records/1",
        "metadata_source_url": "https://example.invalid/api/records/1",
        "title": "Synthetic release",
        "version": None,
        "publication_date": "2026-01-01",
        "creators": ["Example, A."],
        "license": "cc-by-4.0",
        "citation": None,
        "retrieved_at": "2026-01-01T00:00:00+00:00",
        "files": [
            {
                "filename": archive.name,
                "byte_size": archive.stat().st_size,
                "advertised_checksum": f"md5:{digest}",
                "verified_checksum": f"md5:{digest}",
                "source_url": "https://example.invalid/release.zip",
            }
        ],
    }
    provenance_path = tmp_path / "provenance.json"
    provenance_path.write_text(json.dumps(provenance))
    return archive, provenance_path


def test_inventory_generation_is_offline_and_deterministic(tmp_path: Path) -> None:
    archive, provenance = _synthetic_release(tmp_path)
    first = build_inventory(archive, provenance)
    second = build_inventory(archive, provenance)
    assert first == second
    assert first["summary"]["valid_fits_files"] == 26
    assert first["summary"]["fits_hdus"] == 29
    assert first["summary"]["fits_image_files"] == 23
    assert first["summary"]["fits_table_files"] == 3

    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    write_inventory(first, first_path)
    write_inventory(second, second_path)
    assert first_path.read_bytes() == second_path.read_bytes()


def test_inventory_rejects_checksum_mismatch(tmp_path: Path) -> None:
    archive, provenance = _synthetic_release(tmp_path)
    metadata = json.loads(provenance.read_text())
    metadata["files"][0]["advertised_checksum"] = "md5:" + "0" * 32
    provenance.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="does not match"):
        build_inventory(archive, provenance)


def test_committed_inventory_covers_every_archive_member_and_hdu() -> None:
    inventory_path = Path(__file__).parents[1] / "data" / "data_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    summary = inventory["summary"]
    assert summary == {
        "appledouble_metadata_members": 14,
        "archive_members": 40,
        "fits_hdus": 29,
        "fits_image_files": 23,
        "fits_table_files": 3,
        "unreleased_paper_figures_or_panels": [
            "Figure 1 data",
            "Figure 2 data",
            "Figure 3 top-left R-Z count panel",
            "Figure 7 data",
        ],
        "valid_fits_files": 26,
    }
    valid = [member for member in inventory["archive_members"] if member["valid_fits"]]
    assert sum(member["fits"]["hdu_count"] for member in valid) == 29
    assert all(member["figure_mapping"] for member in valid)
    images = [member for member in valid if member["asset_type"] == "FITS 2-D image array"]
    assert all(member["fits"]["image_axes"]["orientation_for_paper"]["transpose_required"] is False for member in images)
    assert all(member["fits"]["image_axes"]["orientation_for_paper"]["origin"] == "lower" for member in images)


def test_focal_figure_capabilities_are_explicit() -> None:
    inventory_path = Path(__file__).parents[1] / "data" / "data_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    assert inventory["focused_findings"]["figure_9"]["lz_or_inverse_lz"].startswith("L_Z is released")
    assert inventory["focused_findings"]["figure_13"]["row_representation"].startswith("Individual rows")
    assert inventory["capability_matrix"]["notebook_2"]["figure_13_vr_sign_split"]["classification"].startswith("YES")
    assert inventory["capability_matrix"]["notebook_3"]["independent_fourier_transform"]["classification"].startswith("PARTIAL")
