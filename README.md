# Lambert Anticentre Lab

**A reproducible, pedagogical exploration of the disturbed outer Milky Way using Lambert et al. (2026), DESI, Gaia, and the authors' released figure data.**

This repository grew out of an astronomy journal-club project, but the notebooks are designed to stand on their own as a compact introduction to several ideas in Galactic dynamics:

- turning sky observables into six-dimensional Galactic phase space;
- reading density and velocity structure in the Galactic anticentre;
- understanding the Anticenter Stream (ACS) and Monoceros Ring (MRi);
- interpreting ridges in $R-V_\phi$ and waves in $L_Z-\langle V_R\rangle$;
- seeing how differential winding can turn phase-space structure into a model-dependent Galactic clock;
- learning how to **read** complicated Galactic-dynamics plots rather than merely reproduce them.

The main scientific reference is:

> **Lambert et al. (2026)**, *Signatures of a Tidally Induced Spiral Arm at the Anticenter of the Milky Way and a Kinematically Extended Anticenter Stream Using DESI Data Release 2*  
> *The Astronomical Journal*, **171**, 292  
> DOI: [10.3847/1538-3881/ae5100](https://doi.org/10.3847/1538-3881/ae5100)

Author-released figure data:

> **Zenodo record 18236902**  
> DOI: [10.5281/zenodo.18236902](https://doi.org/10.5281/zenodo.18236902)

---

## Start here

There are four notebooks.

| Notebook | Main question | Best for |
|---|---|---|
| [**01 — From sky to Galactic phase space**](notebooks/01_from_sky_to_galactic_phase_space.ipynb) | How do DESI/Gaia measurements become $R,\phi,Z,V_R,V_\phi,V_Z,L_Z$? | Coordinates, observables, survey workflow |
| [**02 — Reading the disturbed anticentre**](notebooks/02_reading_the_disturbed_anticentre.ipynb) | What do Lambert's released products directly show about Monoceros and the ACS? | Main observational results |
| [**03 — From spiral winding to a Galactic clock**](notebooks/03_from_spiral_winding_to_a_galactic_clock.ipynb) | How can a velocity wave become a perturbation clock? | Dynamics, Fourier analysis, model dependence |
| [**04 — Visual intuition lab**](notebooks/04_visual_intuition_lab.ipynb) | “I still don't see it — show me another way.” | Plot anatomy and visual intuition |

### Suggested learning order

For a first pass:

**01 → 02 → 04 → 03**

Notebook 4 is intentionally a visual workbench. Reading it before Notebook 3 makes several of the later phase-space and Fourier plots easier to interpret.

---

## Just want to explore? No installation needed

The rendered notebooks contain the executed plots, equations, tables, code, and outputs. You can read them directly in a web browser:

- [**Notebook 1 — From sky to Galactic phase space**](https://ap-13.github.io/lambert-anticentre-lab/01_from_sky_to_galactic_phase_space.html)
- [**Notebook 2 — Reading the disturbed anticentre**](https://ap-13.github.io/lambert-anticentre-lab/02_reading_the_disturbed_anticentre.html)
- [**Notebook 4 — Visual intuition lab**](https://ap-13.github.io/lambert-anticentre-lab/04_visual_intuition_lab.html)
- [**Notebook 3 — From spiral winding to a Galactic clock**](https://ap-13.github.io/lambert-anticentre-lab/03_from_spiral_winding_to_a_galactic_clock.html)

Or start from the [**rendered notebook index**](https://ap-13.github.io/lambert-anticentre-lab/).

---

# Run the notebooks on your own computer

**Supported for v0.1: Linux and macOS.**

Windows may work, but it is not currently tested or documented.

You do **not** need to create a Python virtual environment manually, activate it, or install packages one by one.

You need:

- Git
- an internet connection for the first setup
- [`uv`](https://docs.astral.sh/uv/), which manages Python and the required packages for this project

## 1. Install Git if needed

Check whether Git is already installed:

```bash
git --version
```

On macOS, if this command does not work, you can install Apple's command-line tools with:

```bash
xcode-select --install
```

On Linux, install Git with your distribution's package manager if necessary.

---

## 2. Install `uv`

If this already works:

```bash
uv --version
```

skip to the next step.

On Linux or macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then close and reopen your terminal if `uv` is not found immediately.

Check the installation:

```bash
uv --version
```

---

## 3. Download this repository

```bash
git clone https://github.com/ap-13/lambert-anticentre-lab.git
cd lambert-anticentre-lab
```

---

## 4. Install the project

```bash
uv sync --locked
```

That's it.

`uv` creates an isolated project environment and installs the package versions recorded in `uv.lock`.

You do **not** need to activate the environment manually.

---

## 5. Download and prepare the Lambert figure data

```bash
uv run python scripts/prepare_lambert_data.py --download
```

This command:

- downloads the small author-released Zenodo archive;
- verifies the downloaded file;
- extracts the released FITS products used by Notebooks 2–4;
- verifies the prepared products against the committed data inventory;
- safely reuses an already-verified local copy on later runs.

It does **not** download Lambert's original DESI DR2 stellar catalogue.

---

## 6. Start JupyterLab

```bash
uv run jupyter lab
```

Your web browser should open JupyterLab.

In the file browser, open:

```text
notebooks/
```

For a first run, start with:

```text
01_from_sky_to_galactic_phase_space.ipynb
```

Inside JupyterLab, choose:

**Run → Run All Cells**

You should not need to install anything from inside the notebook.

---

## Something went wrong?

First make sure your terminal is inside the repository.

On Linux/macOS:

```bash
pwd
```

Then update the environment:

```bash
uv sync --locked
```

Run the automated checks:

```bash
uv run pytest
```

If the tests pass, the Python environment and repository code are working.

If a notebook reports missing Lambert FITS products, rerun:

```bash
uv run python scripts/prepare_lambert_data.py --download
```

---

# What the notebooks contain

## 01 — From sky to Galactic phase space

A compact real-data workflow using a public DESI DR1 MWS/Gaia DR3 teaching sample.

The notebook starts with quantities that surveys actually measure:

$$
(\alpha,\delta,\varpi,\mu_{\alpha*},\mu_\delta,V_{\rm los})
$$

and progressively builds:

$$
(l,b,d)
\rightarrow
(X,Y,Z)
\rightarrow
(R,\phi,Z,V_R,V_\phi,V_Z)
\rightarrow
L_Z.
$$

The goal is not to reproduce Lambert's sample. It is to make the coordinate and velocity machinery transparent.

The committed teaching sample contains 256 quality-selected stars and has fully recorded provenance.

---

## 02 — Reading the disturbed anticentre

This notebook uses Lambert's released products to ask:

> Before invoking Sagittarius or any tidal model, what do the observations actually show?

It dissects:

- Figure 5 sky-space $V_R$ and $V_Z$ structure;
- Figure 6 density residuals and top-down kinematics;
- the Figure 8 $R-V_\phi$ ridge;
- the Figure 13 $V_R>0$ / $V_R<0$ experiment.

A central lesson is that a named photometric overdensity and a dynamical population are not necessarily the same thing.

---

## 03 — From spiral winding to a Galactic clock

This notebook separates four logically different steps:

1. a simple tidal-winding mechanism;
2. Lambert's released $L_Z-\langle V_R\rangle$ wave;
3. Fourier/spectral analysis;
4. conversion of spectral structure into a perturbation time under a model.

It also contains a reproducibility audit of the Figure 9 → Figure 10 chain.

One of the notebook's main conclusions is deliberately phrased as:

> **The wave is measured; the spectrum is derived; the clock belongs to a model; the identification with Sagittarius is another inference.**

The public Figure 9/10 products do **not** contain enough information to reproduce every step of the authors' final stochastic Fourier pipeline exactly. The notebook preserves those ambiguities rather than silently choosing missing assumptions.

See [`docs/notebook3_reproducibility_audit.md`](docs/notebook3_reproducibility_audit.md).

---

## 04 — Visual intuition lab

This optional companion asks a different question:

> **How do I actually learn to see what an experienced Galactic-dynamics reader sees in these plots?**

For Figures 5, 6, 8, 9, 10, and 13, the notebook repeatedly uses:

**see → remove information → isolate → collapse → rebuild → stop where the evidence stops**

Examples include:

- turning continuous velocity maps into sign maps;
- comparing density morphology with velocity morphology;
- reconstructing an $R-V_\phi$ ridge from one-dimensional slices;
- revealing a $b-V_Z$ sequence by conditioning on the sign of $V_R$;
- showing why $1/L_Z$ is a useful transformed coordinate;
- connecting Fourier frequency to the number of visible wiggles across the available baseline.

This notebook is intentionally more pedagogical than publication-like.

---

# Data: two deliberately separate tracks

The repository keeps two data tracks separate.

## Track A — public DESI/Gaia teaching sample

Notebook 1 uses a compact sample generated from:

**DESI DR1 MWS Iron v1.0 — Survey Validation 2 / bright**, with Gaia DR3 astrometry.

The final committed ECSV contains 256 stars.

It is:

- real survey data;
- useful for learning the transformation pipeline;
- **not** Lambert's sample;
- **not** the DESI DR1 main-survey bright sample;
- **not** intended for population-level inference.

See [`data/derived/public_demo_sample.provenance.json`](data/derived/public_demo_sample.provenance.json).

## Track B — Lambert's author-released figure products

Notebooks 2–4 use the public Zenodo figure-data release associated with Lambert et al. (2026).

The release contains downstream figure products:

- 23 two-dimensional FITS image products;
- 3 FITS table products.

These products support some operations exactly and others only partially.

For example:

- Figure 13 provides individual rows from an already-selected sample, so the $V_R$-sign split can be recomputed.
- Figures 5, 6, and 8 are already-binned author products, so their source-level selections or binning cannot be changed.
- Figure 9 provides the binned $L_Z-V_R$ wave.
- Figure 10 provides an already-computed Fourier spectrum, not the complete analysis pipeline.

See:

- [`data/data_inventory.json`](data/data_inventory.json)
- [`data/lambert_release_ambiguities.md`](data/lambert_release_ambiguities.md)

---

# What this repository does **not** claim

This distinction is central to the project.

The public Lambert Zenodo archive is **not the source-level DESI DR2 stellar catalogue** used in the paper.

Therefore this repository does not claim to independently reconstruct:

- Lambert's complete DESI DR2 source selection;
- the original source-level binning of fixed image products;
- unreleased per-star uncertainties or weights;
- the fitted ACS photometric boundary;
- every undocumented detail of the Figure 9 → Figure 10 Fourier calculation;
- a unique Sagittarius origin for the observed structures.

Throughout the notebooks, important statements are separated into:

1. **released observation / measurement**
2. **our computational transformation**
3. **data-supported inference**
4. **model-dependent interpretation**
5. **proposed physical explanation**

Agreement with a toy model or simulation is not treated as proof of causation.

---

# Reproducibility

The project uses:

- Python
- NumPy
- SciPy
- Matplotlib
- Astropy
- Jupyter
- `uv` with a committed lockfile
- `pytest`

Run the complete offline validation suite with:

```bash
uv run pytest
```

The tests cover, among other things:

- coordinate and velocity sign conventions;
- the public teaching sample;
- Lambert FITS representations and orientations;
- Figure 13 deterministic selections;
- the Figure 9/10 forensic frequency fingerprint;
- timing calculations;
- visual-intuition helper transformations;
- fresh-kernel execution of all four notebooks.

Ordinary notebook execution does not perform implicit network requests.

---

# Scientific provenance and important caveats

Several ambiguities in the public products and paper are intentionally preserved.

Examples include:

- Figure 9 mean versus median wording;
- 70 versus 75 stated $L_Z$ bins;
- differences between stated and released $L_Z$ ranges;
- Figure 10 mean versus median Monte-Carlo spectrum wording;
- undocumented Fourier preprocessing details;
- the published $1.10\pm0.23$ versus approximately $1.10\pm0.28$ Gyr uncertainty discrepancy.

These are documented in:

[`data/lambert_release_ambiguities.md`](data/lambert_release_ambiguities.md)

and the dedicated Figure 9/10 audit:

[`docs/notebook3_reproducibility_audit.md`](docs/notebook3_reproducibility_audit.md)

---

# Repository layout

```text
lambert-anticentre-lab/
├── notebooks/      # the four teaching/science notebooks
├── src/            # reusable loaders, coordinates, dynamics, plotting
├── scripts/        # reproducible data preparation
├── tests/          # scientific + execution tests
├── data/
│   ├── derived/    # small committed teaching products
│   └── ...         # provenance/inventory documentation
├── docs/           # methodological audit
├── pyproject.toml
└── uv.lock
```

Large/raw downloads are intentionally not committed.

---

# Citation and attribution

If this repository is useful for scientific work, please cite the original data and scientific sources rather than citing this repository as a substitute for them.

In particular:

**Lambert et al. (2026)**  
*The Astronomical Journal*, **171**, 292  
DOI: [10.3847/1538-3881/ae5100](https://doi.org/10.3847/1538-3881/ae5100)

**Lambert figure-data release**  
Zenodo record 18236902  
DOI: [10.5281/zenodo.18236902](https://doi.org/10.5281/zenodo.18236902)

Notebook 1 also uses public DESI DR1 and Gaia DR3 material; their appropriate survey citations should be retained in downstream scientific use.

A [`CITATION.cff`](CITATION.cff) file provides citation metadata for this repository itself.

---

# License

Repository source code is released under the **BSD 3-Clause License**. See [`LICENSE`](LICENSE).

Third-party survey data and author-released scientific data remain under their original licences and attribution requirements. The repository's software licence does not relicense DESI, Gaia, or Lambert data products.

---

## Why this repository exists

Galactic-dynamics papers often compress a large amount of physical reasoning into a few dense phase-space figures.

The goal here is not simply to reproduce those figures.

It is to make the chain

$$
\text{measurement}
\rightarrow
\text{coordinate system}
\rightarrow
\text{phase-space structure}
\rightarrow
\text{dynamical inference}
\rightarrow
\text{physical interpretation}
$$

slow enough to inspect.

If, after working through the notebooks, a plot such as an $R-V_\phi$ ridge or an $L_Z-\langle V_R\rangle$ wave feels less like “something an expert somehow sees” and more like a readable physical object, the repository has done its job.
