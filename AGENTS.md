# Repository instructions

`CODEX_BUILD_SPEC.md` is the source of truth. Read the relevant notebook
contract and task boundary there before changing code or scientific prose.

## Guardrails

- Never present a model-dependent interpretation as a measurement or describe
  Sagittarius as uniquely demonstrated.
- Never describe Lambert's Zenodo figure products as the unpublished DESI DR2
  source catalogue. Do not invent missing columns, cuts, uncertainties, or
  metadata; state public-data limitations.
- Use explicit Astropy units and centrally defined Galactocentric parameters.
  Reconcile velocity and coordinate signs with both Astropy and Lambert's
  documented definitions; do not rely on memory.
- Keep reusable code in `src/lambert_lab/`. Notebooks must execute from top to
  bottom in clean kernels, and random work must use explicit seeds.
- Cache downloads, verify checksums, and preserve provenance. Keep raw and
  routine generated outputs untracked; commit compact provenance and inventory
  metadata where the build specification requires it.
- Default tests must remain offline. Network integration checks require an
  explicit invocation and authorization.

## Validation commands

```bash
uv sync
uv run pytest
git diff --check
```

For reproduced figures, cite the exact paper figure and released file/HDU, and
validate scientific morphology or values rather than appearance alone.

