#!/usr/bin/env python3
"""Prepare the verified Lambert figure products required by Notebooks 2--4."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lambert_lab.prepare import PreparationError, prepare_lambert_products


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify and prepare Lambert's author-released FITS figure products."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Fetch the pinned Zenodo release before preparing it (the only network option).",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Cache directory (default: data/raw/lambert_zenodo).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        summary = prepare_lambert_products(
            root, cache_directory=args.cache_dir, download=args.download
        )
    except PreparationError as error:
        print(f"Lambert data preparation failed: {error}", file=sys.stderr)
        return 1
    print(
        "Lambert data are ready for Notebooks 2–4: "
        f"{summary.products} verified FITS products in {summary.extracted_directory}."
    )
    print(
        f"Archive verified ({summary.verified_archive_checksum}); "
        f"reused {summary.reused}, extracted {summary.extracted}, repaired {summary.repaired}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
