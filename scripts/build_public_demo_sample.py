#!/usr/bin/env python3
"""Build the compact DESI DR1 SV2 / Gaia DR3 teaching sample."""

from __future__ import annotations

import argparse
from pathlib import Path

from lambert_lab.public_sample import (
    DEFAULT_MAX_STARS,
    DEFAULT_SEED,
    SOURCE_FILENAME,
    build_sample,
    download_source,
    verify_source,
    write_sample,
)

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "data" / "raw" / "desi_dr1_mws_iron" / SOURCE_FILENAME,
        help="verified local FITS cache path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "derived" / "public_demo_sample.ecsv",
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        default=ROOT / "data" / "derived" / "public_demo_sample.provenance.json",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="permit download of the one pinned source if the cache is absent",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-stars", type=int, default=DEFAULT_MAX_STARS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = download_source(args.source) if args.download else verify_source(args.source)
    table, provenance = build_sample(source, max_stars=args.max_stars, seed=args.seed)
    for item in provenance["cut_flow"]:
        print(f"{item['remaining']:5d}  {item['cut']}")
    final = write_sample(table, provenance, args.output, args.provenance)
    print(f"Wrote {len(table)} stars to {args.output}")
    print(f"ECSV SHA-256: {final['output']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
