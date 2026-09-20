"""Small validation helpers shared by scripts and later notebooks."""

from __future__ import annotations

import hashlib
from pathlib import Path


def require_local_file(path: str | Path, *, purpose: str) -> Path:
    """Return an existing regular file or raise an actionable error."""

    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(
            f"Missing file required for {purpose}: {resolved}. "
            "Follow data/README.md to obtain the appropriate public product."
        )
    return resolved


def file_checksum(path: str | Path, algorithm: str = "sha256") -> str:
    """Calculate a hexadecimal checksum for a local file."""

    try:
        digest = hashlib.new(algorithm)
    except ValueError as error:
        raise ValueError(f"Unsupported checksum algorithm: {algorithm}") from error

    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

