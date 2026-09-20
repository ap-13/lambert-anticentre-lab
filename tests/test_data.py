from __future__ import annotations

import hashlib
import importlib
import io
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from lambert_lab.data import CacheIntegrityError, fetch_zenodo_release
from lambert_lab.validation import require_local_file


class OfflineOpener:
    """Serve synthetic Zenodo metadata and bytes without network access."""

    def __init__(self, metadata_url: str, metadata: dict[str, Any], files: dict[str, bytes]):
        self.responses = {
            metadata_url: json.dumps(metadata).encode("utf-8"),
            **files,
        }
        self.calls: list[str] = []

    def __call__(self, request: urllib.request.Request, *, timeout: float) -> io.BytesIO:
        assert timeout > 0
        url = request.full_url
        self.calls.append(url)
        if url not in self.responses:
            raise OSError(f"unexpected offline URL: {url}")
        return io.BytesIO(self.responses[url])


def synthetic_release() -> tuple[str, dict[str, Any], dict[str, bytes]]:
    metadata_url = "https://example.invalid/api/records/123"
    payloads = {
        "https://example.invalid/files/panel.fits": b"synthetic-fits-placeholder",
        "https://example.invalid/files/notes.txt": b"synthetic notes",
    }
    files = []
    for url, payload in payloads.items():
        files.append(
            {
                "key": url.rsplit("/", 1)[-1],
                "size": len(payload),
                "checksum": f"md5:{hashlib.md5(payload).hexdigest()}",  # noqa: S324
                "links": {"self": url},
            }
        )
    metadata = {
        "id": 123,
        "conceptrecid": "100",
        "doi": "10.5281/zenodo.123",
        "links": {
            "self": metadata_url,
            "html": "https://example.invalid/records/123",
        },
        "metadata": {
            "title": "Synthetic Lambert release",
            "version": "1.2.3",
            "publication_date": "2026-01-01",
            "creators": [{"name": "Example, A."}],
            "license": {"id": "cc-by-4.0"},
        },
        "files": files,
    }
    return metadata_url, metadata, payloads


def test_fetch_verifies_download_and_reuses_cache(tmp_path: Path) -> None:
    metadata_url, metadata, payloads = synthetic_release()
    opener = OfflineOpener(metadata_url, metadata, payloads)

    first = fetch_zenodo_release(
        tmp_path,
        record_id="123",
        api_base="https://example.invalid/api/records",
        opener=opener,
    )
    assert {item["cache_status"] for item in first["files"]} == {"downloaded"}
    assert first["resolved_record_id"] == "123"
    assert first["version"] == "1.2.3"
    assert first["doi"] == "10.5281/zenodo.123"
    assert first["record_url"] == "https://example.invalid/records/123"
    assert first["retrieved_at"]

    second = fetch_zenodo_release(
        tmp_path,
        record_id="123",
        api_base="https://example.invalid/api/records",
        opener=opener,
    )
    assert {item["cache_status"] for item in second["files"]} == {"verified-cache"}
    for url in payloads:
        assert opener.calls.count(url) == 1

    saved = json.loads((tmp_path / "_release_provenance.json").read_text())
    assert saved["resolved_record_id"] == "123"
    assert len(saved["files"]) == 2


def test_fetch_refuses_to_overwrite_bad_cache(tmp_path: Path) -> None:
    metadata_url, metadata, payloads = synthetic_release()
    opener = OfflineOpener(metadata_url, metadata, payloads)
    bad_path = tmp_path / "panel.fits"
    bad_path.write_bytes(b"unverified")

    with pytest.raises(CacheIntegrityError, match="will not be overwritten"):
        fetch_zenodo_release(
            tmp_path,
            record_id="123",
            api_base="https://example.invalid/api/records",
            opener=opener,
        )
    assert bad_path.read_bytes() == b"unverified"
    assert "https://example.invalid/files/panel.fits" not in opener.calls


def test_missing_file_error_is_actionable(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="data/README.md"):
        require_local_file(tmp_path / "missing.fits", purpose="an offline test")


def test_package_import_does_not_call_urlopen(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("package import attempted network access")

    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)
    sys.modules.pop("lambert_lab", None)
    imported = importlib.import_module("lambert_lab")
    assert imported.__version__ == "0.1.0"

