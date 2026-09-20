#!/usr/bin/env python3
"""Task 1 interface scaffold for a future DESI DR1 teaching sample."""

from __future__ import annotations

import argparse
import json


PROVENANCE_CONTRACT = {
    "track": "A: public DESI DR1/Gaia-backed educational workflow",
    "not_lambert_dr2": True,
    "required_source_fields": [
        "catalogue_release",
        "authoritative_source_url",
        "source_table_or_hdu",
        "source_columns_and_units",
        "query_or_extraction_rule",
        "row_selection_rule",
        "retrieval_timestamp",
        "source_checksums",
    ],
    "required_derived_fields": [
        "producing_script_version",
        "parameters",
        "parent_filenames_and_checksums",
        "output_checksum",
    ],
    "implementation_task": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Describe the provenance contract for the future demo sample."
    )
    parser.add_argument(
        "--describe", action="store_true",
        help="Print the Task 3 sample provenance contract",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.describe:
        raise SystemExit(
            "Demo-sample construction is intentionally unavailable in Task 1. "
            "Use --describe to inspect its provenance contract."
        )
    print(json.dumps(PROVENANCE_CONTRACT, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

