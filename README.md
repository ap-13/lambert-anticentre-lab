# Lambert Anticentre Lab

This repository is a three-notebook journal-club laboratory for understanding
the observational and dynamical logic of Lambert et al. (2026). The governing
scope and scientific guardrails are in
[`CODEX_BUILD_SPEC.md`](CODEX_BUILD_SPEC.md).

The repository deliberately keeps two data tracks separate:

- a compact public DESI DR1 SV2-bright/Gaia DR3 teaching sample for the
  coordinate workflow in Notebook 1;
- Lambert's author-released Zenodo figure products for Notebooks 2 and 3 and
  the optional visual-intuition companion.

The Zenodo release is a collection of downstream figure products. It is not the
unpublished source-level DESI DR2 stellar catalogue used by Lambert. This
repository does not claim to reproduce that source-level analysis.

## Current status

The three core notebooks are complete. Notebook 4,
`04_visual_intuition_lab.ipynb`, is an optional companion/workbench that uses
the same released products while introducing clearly labelled pedagogical
display transformations and one-dimensional reductions.

## Environment

Python 3.11 or newer and
[`uv`](https://docs.astral.sh/uv/) are required.

```bash
uv sync
```

The base package uses NumPy, SciPy, Matplotlib, and Astropy. Notebook and test
tools are installed through uv's default development dependency group.

## Offline validation

The default suite never uses the network:

```bash
uv run pytest
```

The notebook execution harness starts a fresh kernel for all three core
notebooks and the optional visual-intuition companion.

## Notebook 1 public sample

The committed teaching product is generated from the official DESI DR1 MWS
Iron `rvpix-sv2-bright.fits` combined product. It is Survey Validation 2 data,
not the DESI main survey, not representative population data, and not the
Lambert DR2 sample. To rebuild from a verified local cache:

```bash
uv run python scripts/build_public_demo_sample.py
```

Add `--download` only when explicit network access is intended.

## Lambert release fetch smoke test

Network access is explicit. After authorization, the Task 1 smoke test is:

```bash
uv run python scripts/fetch_lambert_zenodo.py \
  --destination data/raw/lambert_zenodo
```

Run the same command a second time to exercise verified-cache behavior. The
fetcher resolves the exact Zenodo record, verifies every advertised checksum,
and writes `_release_provenance.json` beside the ignored raw files. It refuses
to overwrite an existing file that fails verification.

The smoke test verifies transfer integrity only. FITS inspection, figure
mapping, and scientific interpretation belong to Task 2.

## Data and generated artifacts

See [`data/README.md`](data/README.md) for the provenance contract. Raw
downloads, derived working data, and routine validation figures are ignored by
Git. Task 2 created the compact committed files
`data/data_inventory.json` and `data/lambert_release_ambiguities.md`.
