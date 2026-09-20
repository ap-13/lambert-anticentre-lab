from __future__ import annotations

import hashlib
import importlib
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.table import QTable

import lambert_lab.public_sample as public_sample


def _fixture(path: Path, rows: int = 80) -> None:
    index = np.arange(rows)
    targetid = 10_000 + index
    source_id = 20_000 + index
    ra = 120.0 + index * 1e-4
    dec = 30.0 + index * 1e-4
    rv = fits.BinTableHDU.from_columns(
        [
            fits.Column(name="TARGETID", format="K", array=targetid),
            fits.Column(name="TARGET_RA", format="D", array=ra),
            fits.Column(name="TARGET_DEC", format="D", array=dec),
            fits.Column(name="VRAD", format="D", unit="km s-1", array=index - 40.0),
            fits.Column(name="VRAD_ERR", format="D", unit="km s-1", array=np.full(rows, 1.0)),
            fits.Column(name="SN_R", format="E", array=100.0 - index),
            fits.Column(name="SUCCESS", format="L", array=np.ones(rows, dtype=bool)),
            fits.Column(name="RVS_WARN", format="K", array=np.zeros(rows, dtype=np.int64)),
            fits.Column(name="RR_SPECTYPE", format="6A", array=np.full(rows, "STAR")),
        ],
        name="RVTAB",
    )
    fibermap = fits.BinTableHDU.from_columns(
        [
            fits.Column(name="TARGETID", format="K", array=targetid),
            fits.Column(name="TARGET_RA", format="D", array=ra),
            fits.Column(name="TARGET_DEC", format="D", array=dec),
            fits.Column(name="COADD_FIBERSTATUS", format="J", array=np.zeros(rows, dtype=np.int32)),
        ],
        name="FIBERMAP",
    )
    scores = fits.BinTableHDU.from_columns(
        [fits.Column(name="TARGETID", format="K", array=targetid)], name="SCORES"
    )
    gaia_columns = [
        fits.Column(name="SOURCE_ID", format="K", array=source_id),
        fits.Column(name="RA", format="D", array=ra),
        fits.Column(name="RA_ERROR", format="E", array=np.full(rows, 0.05)),
        fits.Column(name="DEC", format="D", array=dec),
        fits.Column(name="DEC_ERROR", format="E", array=np.full(rows, 0.05)),
        fits.Column(name="PARALLAX", format="D", array=np.full(rows, 2.0)),
        fits.Column(name="PARALLAX_ERROR", format="E", array=np.full(rows, 0.05)),
        fits.Column(name="PARALLAX_OVER_ERROR", format="E", array=np.full(rows, 40.0)),
        fits.Column(name="PMRA", format="D", array=index / 10.0),
        fits.Column(name="PMRA_ERROR", format="E", array=np.full(rows, 0.05)),
        fits.Column(name="PMDEC", format="D", array=-index / 10.0),
        fits.Column(name="PMDEC_ERROR", format="E", array=np.full(rows, 0.05)),
        fits.Column(name="ASTROMETRIC_PARAMS_SOLVED", format="I", array=np.full(rows, 31)),
        fits.Column(name="VISIBILITY_PERIODS_USED", format="I", array=np.full(rows, 12)),
        fits.Column(name="RUWE", format="E", array=np.full(rows, 1.0)),
        fits.Column(name="DUPLICATED_SOURCE", format="L", array=np.zeros(rows, dtype=bool)),
    ]
    fits.HDUList([fits.PrimaryHDU(), rv, fibermap, scores, fits.BinTableHDU.from_columns(gaia_columns, name="GAIA")]).writeto(path)


def test_deterministic_generation_from_local_fixture(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "fixture.fits"
    _fixture(source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(public_sample, "SOURCE_SIZE", source.stat().st_size)
    monkeypatch.setattr(public_sample, "SOURCE_SHA256", digest)

    first, first_provenance = public_sample.build_sample(source, max_stars=70, seed=123)
    second, second_provenance = public_sample.build_sample(source, max_stars=70, seed=123)
    np.testing.assert_array_equal(first["source_row"], second["source_row"])
    assert first_provenance == second_provenance
    assert len(first) == 70
    assert len(np.unique(first["gaia_dr3_source_id"])) == 70


def test_committed_sample_schema_units_and_provenance() -> None:
    root = Path(__file__).parents[1]
    sample_path = root / "data" / "derived" / "public_demo_sample.ecsv"
    provenance_path = root / "data" / "derived" / "public_demo_sample.provenance.json"
    sample = QTable.read(sample_path)
    provenance = json.loads(provenance_path.read_text())
    assert len(sample) == 256
    assert {"source_row", "targetid", "gaia_dr3_source_id", "ra", "dec", "parallax", "pmra", "pmdec", "radial_velocity", "distance"}.issubset(sample.colnames)
    assert "l" not in sample.colnames and "R" not in sample.colnames and "V_phi" not in sample.colnames
    assert str(sample["ra"].unit) == "deg"
    assert str(sample["parallax"].unit) == "mas"
    assert str(sample["pmra"].unit) == "mas / yr"
    assert str(sample["radial_velocity"].unit) == "km / s"
    assert str(sample["distance"].unit) == "kpc"
    assert provenance["not_lambert_dr2"] is True
    assert provenance["source_checksums"]["sha256"] == public_sample.SOURCE_SHA256
    assert provenance["source_byte_size"] == public_sample.SOURCE_SIZE
    assert provenance["output"]["sha256"] == hashlib.sha256(sample_path.read_bytes()).hexdigest()


def test_public_sample_import_has_no_network_side_effect(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("public_sample import attempted network access")

    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)
    sys.modules.pop("lambert_lab.public_sample", None)
    imported = importlib.import_module("lambert_lab.public_sample")
    assert imported.SOURCE_FILENAME == "rvpix-sv2-bright.fits"


def test_bad_cache_is_not_overwritten(tmp_path: Path, monkeypatch) -> None:
    bad = tmp_path / "rvpix-sv2-bright.fits"
    bad.write_bytes(b"bad cache")
    monkeypatch.setattr(public_sample, "SOURCE_SIZE", 100)
    with np.testing.assert_raises(public_sample.SampleBuildError):
        public_sample.download_source(bad)
    assert bad.read_bytes() == b"bad cache"
