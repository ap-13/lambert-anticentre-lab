#!/usr/bin/env python3
"""Regenerate the canonical Lambert release inventory without network access."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lambert_lab.inventory import DEFAULT_ARCHIVE_NAME, build_inventory, write_inventory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/raw/lambert_zenodo"),
        help="Directory containing the immutable ZIP and _release_provenance.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/data_inventory.json"),
        help="Canonical JSON destination",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive = args.cache_dir / DEFAULT_ARCHIVE_NAME
    provenance = args.cache_dir / "_release_provenance.json"
    try:
        inventory = build_inventory(archive, provenance)
        write_inventory(inventory, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Inventory generation failed: {error}", file=sys.stderr)
        return 1
    print(
        f"Wrote {args.output} with {inventory['summary']['archive_members']} archive "
        f"members, {inventory['summary']['valid_fits_files']} FITS files, and "
        f"{inventory['summary']['fits_hdus']} HDUs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
