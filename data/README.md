# Data layout and provenance

The repository has two separate data tracks:

- **Track A:** a future public DESI DR1/Gaia-backed educational sample for
  Notebook 1. It is not Lambert's DESI DR2 source catalogue.
- **Track B:** Lambert's downstream author-released figure products from Zenodo
  DOI `10.5281/zenodo.18236902` for Notebooks 2 and 3.

`raw/` is an ignored cache for immutable downloads. `derived/` is ignored
working space for reproducible generated products. Routine validation figures
under `figures/validation/` are also ignored.

Task 2 will create and commit:

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

