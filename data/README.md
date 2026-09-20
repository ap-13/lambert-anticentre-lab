# Data layout and provenance

The repository has two separate data tracks:

- **Track A:** a compact public DESI DR1 SV2-bright/Gaia DR3 educational
  sample for Notebook 1. It is not the DR1 main-survey bright sample or
  Lambert's DESI DR2 source catalogue.
- **Track B:** Lambert's downstream author-released figure products from Zenodo
  DOI `10.5281/zenodo.18236902` for Notebooks 2 and 3.

`raw/` is an ignored cache for immutable downloads. Routine files in
`derived/` are ignored, except for the canonical small
`public_demo_sample.ecsv` and its provenance JSON. Routine validation figures
under `figures/validation/` are ignored.

Build the canonical teaching sample from a verified cache (offline):

```bash
uv run python scripts/build_public_demo_sample.py
```

Network access is never implicit. Add `--download` to fetch only the pinned
10,186,560-byte `rvpix-sv2-bright.fits` source. The builder checks its expected
SHA-256, refuses to overwrite a bad cache, reads extensions by `EXTNAME`, and
prints the full cut flow.

Task 2 created and committed:

- `data/data_inventory.json`: canonical release, file, FITS, and HDU inventory;
- `data/lambert_release_ambiguities.md`: unresolved and paper-dependent
  semantics.

Each downloaded release must record the exact resolved record/version, DOI,
source URL, original filenames and sizes, advertised and verified checksums,
retrieval timestamp, title, creators, licence, and citation metadata when
available. Derived products must also record their producing code and
parameters plus parent filenames and checksums.

The Task 1 fetcher writes `_release_provenance.json` inside the ignored raw
cache. That transfer manifest is input to, but not a substitute for, the
canonical committed Task 2 inventory.
