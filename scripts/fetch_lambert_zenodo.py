#!/usr/bin/env python3
"""Explicit CLI for the verified Lambert Zenodo release fetch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lambert_lab.data import DEFAULT_RECORD_ID, FetchError, fetch_zenodo_release


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch and checksum-verify the exact Lambert Zenodo release. "
            "This command does not inspect FITS contents."
        )
    )
    parser.add_argument(
        "--destination", type=Path, required=True,
        help="Explicit raw-cache destination directory",
    )
    parser.add_argument(
        "--record-id", default=DEFAULT_RECORD_ID,
        help=f"Exact Zenodo record id (default: {DEFAULT_RECORD_ID})",
    )
    parser.add_argument(
        "--timeout", type=float, default=60.0,
        help="Per-request timeout in seconds (default: 60)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = fetch_zenodo_release(
            args.destination, record_id=args.record_id, timeout=args.timeout
        )
    except (FetchError, OSError, ValueError) as error:
        print(f"Fetch failed: {error}", file=sys.stderr)
        return 1

    statuses: dict[str, int] = {}
    for item in manifest["files"]:
        status = item["cache_status"]
        statuses[status] = statuses.get(status, 0) + 1
    print(
        json.dumps(
            {
                "resolved_record_id": manifest["resolved_record_id"],
                "doi": manifest["doi"],
                "destination": str(args.destination.resolve()),
                "files": len(manifest["files"]),
                "status_counts": statuses,
                "provenance": str(
                    (args.destination / "_release_provenance.json").resolve()
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

