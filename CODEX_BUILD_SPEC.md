# CODEX_BUILD_SPEC.md
## Lambert 2026 Journal-Club Notebook Laboratory

**Project purpose:** Build a small, scientifically disciplined, pedagogical repository that helps an astronomy reader understand the core observational and dynamical logic of Lambert et al. (2026), while also teaching a realistic but not overcomplicated Milky-Way stellar-dynamics workflow.

**Repository philosophy:**  
**Reproduce → understand → experiment.**  
AI-assisted implementation, scientist-verified interpretation.

---

# 1. Scope and non-goals

## Core deliverable

Exactly **three core notebooks**:

1. `01_from_sky_to_galactic_phase_space.ipynb`
2. `02_reading_the_disturbed_anticentre.ipynb`
3. `03_from_spiral_winding_to_a_galactic_clock.ipynb`

Do **not** proliferate notebooks unless a genuinely distinct scientific workflow cannot be taught cleanly inside one of these three.

## What the repository should teach

A reader should finish the repository understanding:

- what an observer actually measures for a star;
- how sky observables become Galactocentric positions and velocities;
- what \(R, Z, V_R, V_\phi, V_Z\), and \(L_Z\) mean physically;
- how survey selections, binning, medians, and phase-space projections are used in Galactic archaeology/dynamics;
- why ACS and Monoceros look dynamically different in Lambert et al.;
- why an overdensity on the sky need not be a dynamically isolated structure;
- how a tidally perturbed disc can develop a winding spiral/radial-velocity wave;
- how Lambert's Fourier timing inference is constructed;
- where direct measurement ends and model-dependent causal interpretation begins.

## Non-goals

The repository must **not**:

- claim to reproduce Lambert's full source-level DESI DR2 analysis;
- imply access to the unpublished three-year DESI stellar catalogue used by Lambert;
- silently reverse-engineer missing source-level selections from figure products;
- present Sagittarius as uniquely demonstrated by the data;
- turn into a general Galactic-dynamics textbook;
- turn into a large simulation project;
- become an AI/Codex showcase at the expense of the astronomy;
- use many decorative widgets or sliders with no scientific purpose;
- copy large blocks of analysis code into notebooks when reusable functions belong in `src/`.

---

# 2. Scientific evidence hierarchy

Every notebook should visibly distinguish, where relevant:

**OBSERVABLE / MEASUREMENT**  
What comes from the survey or released paper product.

**COMPUTATIONAL OPERATION**  
Coordinate transform, quality cut, binning, median, Fourier transform, orbit integration, etc.

**DATA-SUPPORTED INFERENCE**  
What is reasonably inferred from the measured pattern.

**MODEL-DEPENDENT INTERPRETATION**  
What follows only after assuming a particular dynamical framework.

**SPECULATION / PHYSICAL EXPLANATION**  
Plausible but not uniquely established causal story.

Use these distinctions in Markdown callouts throughout the notebooks.

---

# 3. Data provenance strategy

There are two deliberately separate data tracks.

## Track A — public survey workflow data

Used primarily in Notebook 1.

Preferred source:
- DESI DR1 Milky Way Survey stellar value-added catalogue.
- Gaia DR3 crossmatch information already included in DESI DR1 products where practical.
- If a lightweight public sample is needed, create a small cached subset with explicit provenance and a reproducible extraction script.

Purpose:
- teach how an astronomer goes from catalogue measurements to Galactic phase space;
- teach FITS/table inspection, units, quality filtering, sky coordinates, radial velocities, proper motions, distances, and Galactocentric transformations.

Important:
- this is an **educational public-data workflow**;
- it is **not** a reproduction of Lambert's DR2 source catalogue.

Current DESI DR1 MWS documentation states that the DR1 stellar catalogue includes millions of stellar sources, RV/stellar-parameter products, and a Gaia DR3 crossmatch extension. The DR1 MWS VAC documentation and official tutorial should be treated as authoritative implementation references.

## Track B — Lambert author-released figure products

Used primarily in Notebooks 2 and 3.

Source:
- Zenodo DOI: `10.5281/zenodo.18236902`

The Zenodo release explicitly provides:
- data points for every paper figure;
- FITS tables for Figures 9, 10, 13, and 14;
- 2-D FITS arrays for the other figures;
- descriptions in the FITS headers.

Purpose:
- faithfully reconstruct selected Lambert plots;
- simplify them pedagogically;
- run small sensitivity experiments where the released product supports them.

Important:
- treat these as **downstream figure-level scientific products**;
- do not imply access to the full DR2 stellar catalogue;
- provenance must be displayed in notebook metadata/Markdown.

The Lambert paper is not currently present in this local repository. Exact
paper-dependent axis definitions, selections, equations, and figure semantics
therefore remain unresolved until the paper is made available locally or is
accessed from an authoritative source during Task 2. Do not fill those gaps
from memory.

## Machine-readable provenance

Each downloaded release must record, at minimum:
- the exact Zenodo record and version resolved at retrieval time;
- DOI and authoritative source URL;
- original filename and byte size;
- advertised checksum, when available, and a locally verified checksum;
- retrieval timestamp;
- release title, creators, licence, and citation metadata when supplied.

Each derived product must additionally record:
- the producing script or package version and relevant parameters;
- the parent filename(s) and checksum(s);
- enough information to distinguish a regenerated product from an original
  author-released file.

Do not rely on the DOI alone if it can resolve to more than one record version.
Raw downloads and routine generated validation output should normally be
ignored by Git. Compact inventory, ambiguity, and provenance metadata should
be committed.

---

# 4. Preferred software stack

Core:
- Python 3.11+ or 3.12
- `numpy`
- `scipy`
- `matplotlib`
- `astropy`
- `pandas` only where genuinely useful
- `jupyterlab`
- `ipykernel`

Dynamics:
- `galpy` for simple orbit/potential demonstrations if it simplifies the implementation;
- avoid action-angle machinery unless directly useful to the lesson.

Reproducibility/testing:
- `pytest`
- `nbformat` and `nbclient` for clean notebook execution tests
- optional `ruff` for source files
- optional `pre-commit` only if it does not complicate onboarding

Environment:
- prefer `pyproject.toml`;
- avoid an unnecessarily large dependency tree;
- pin minimum versions or a tested lockfile only after the first functioning build.

---

# 5. Repository architecture

```text
lambert-anticentre-lab/
├── README.md
├── AGENTS.md
├── CODEX_BUILD_SPEC.md
├── pyproject.toml
├── .gitignore
├── notebooks/
│   ├── 01_from_sky_to_galactic_phase_space.ipynb
│   ├── 02_reading_the_disturbed_anticentre.ipynb
│   └── 03_from_spiral_winding_to_a_galactic_clock.ipynb
├── src/
│   └── lambert_lab/
│       ├── __init__.py
│       ├── data.py
│       ├── coordinates.py
│       ├── plotting.py
│       ├── dynamics.py
│       └── validation.py
├── scripts/
│   ├── fetch_lambert_zenodo.py
│   └── build_public_demo_sample.py
├── data/
│   ├── README.md
│   ├── data_inventory.json
│   ├── lambert_release_ambiguities.md
│   ├── raw/
│   └── derived/
├── tests/
│   ├── test_data.py
│   ├── test_coordinates.py
│   ├── test_dynamics.py
│   └── test_notebooks.py
└── figures/
    └── validation/
```

Notebook code should call short, readable functions from `src/` rather than hide 50–100 lines of plumbing in every notebook.

`data/data_inventory.json` and `data/lambert_release_ambiguities.md` are Task 2
outputs, not Task 1 placeholders. Runtime code may create ignored raw, derived,
and validation directories when needed.

---

# 6. Notebook 1 contract
## `01_from_sky_to_galactic_phase_space.ipynb`

### Scientific question

**We observe a star on the sky. How do those measurements become a statement such as "this star is moving outward, rotating with the disc, and moving above the Galactic plane"?**

### Audience outcome

By the end, the reader should understand physically and computationally:

\[
(\alpha,\delta,d,\mu_{\alpha*},\mu_\delta,v_{\rm los})
\rightarrow
(l,b,d)
\rightarrow
(X,Y,Z)
\rightarrow
(R,\phi,Z)
\]

and

\[
(v_{\rm los},\mu_l,\mu_b)
\rightarrow
(V_R,V_\phi,V_Z)
\rightarrow
L_Z=R\,V_\phi.
\]

### Required sections

1. **What the telescope/survey gives us**
   - inspect a small public DESI DR1/Gaia-backed sample;
   - show actual column names and units;
   - explain position, proper motion, line-of-sight velocity, and distance.

2. **Coordinate geometry before code**
   - short schematic/intuitive explanation;
   - Sun versus Galactic Centre;
   - cylindrical directions;
   - sign conventions reconciled against the chosen Astropy frame and
     Lambert's documented definitions after source inspection.

3. **Astropy transformation**
   - construct `SkyCoord`;
   - define Galactocentric frame parameters explicitly;
   - transform positions and velocities;
   - show units throughout.

4. **One-star sanity test**
   - choose or construct an intentionally easy geometry;
   - predict the sign of \(V_R\) and \(V_Z\) before calculating;
   - confirm that code agrees with physical reasoning.

5. **Small real-sample diagnostic**
   - plot a compact \(R-V_\phi\) or \(R-V_R\) view;
   - calculate \(L_Z\);
   - connect the quantity to later Lambert notebooks.

6. **Try it yourself**
   - modify one velocity or one sky position;
   - predict and then inspect how the Galactocentric result changes.

### Pedagogical constraint

Do not bury the coordinate transformation inside unexplained helper code. The notebook may call a helper function for the full sample, but at least one star must be transformed transparently so the reader sees what is happening.

### Validation

- explicit unit checks;
- sign-convention tests;
- verify transformation round-trip or compare against direct Astropy output;
- document adopted solar position/velocity;
- do not assume axis, rotation, or velocity signs from memory: record how the
  adopted Astropy conventions map onto Lambert's definitions;
- no hand-written transformation formula should replace a validated Astropy transformation unless shown strictly for intuition.

### Out of scope

- actions;
- complex orbit fitting;
- uncertainty propagation beyond a short note or one compact Monte Carlo demonstration;
- full survey selection-function modelling.

---

# 7. Notebook 2 contract
## `02_reading_the_disturbed_anticentre.ipynb`

### Scientific question

**Before invoking Sagittarius or a tidal model, what do the released Lambert products actually tell us about Monoceros and the Anticenter Stream?**

### This is the flagship notebook

Give this notebook the highest polishing priority.

### Required flow

## Part A — inspect the author-released products

- load the cached Zenodo release and the committed Task 2 inventory;
- summarize the relevant FITS files, HDUs, shapes, units, and descriptions;
- distinguish FITS tables from 2-D arrays and explain what operations each
  representation supports.

Keep this short and practical.

## Part B — ACS versus Monoceros kinematics

Reconstruct or simplify the most useful Figure 5/6-style products.

Teach:
- sky-space versus Galactocentric projections;
- density versus median velocity;
- binning and minimum-count masking when the released representation permits
  them, or otherwise how those operations are already embedded in the product;
- median \(V_R\), \(V_Z\), and optionally \(V_\phi\);
- why velocity structure can reveal a population more clearly than density alone.

Target scientific point, if supported by the inspected products:
- in Lambert's sampled region, ACS- and Monoceros-associated stars show opposite-sign radial and vertical motions.

If this cannot be independently reconstructed, present it as Lambert's reported
result and state which public information is insufficient.

Do not overstate:
- "opposite-sign motions" is observational;
- "different dynamical manifestations of a disturbed disc" is an inference;
- a specific formation mechanism is further downstream.

## Part C — phase-space projection

Show how the same disturbance appears in a different projection such as \(R-V_\phi\).

Teach:
- why Galactic dynamicists change projections;
- relation of approximately constant \(L_Z\) to diagonal features/ridges;
- difference between a density ridge and a causal interpretation of that ridge.

## Part D — ACS boundary experiment

Use the released Figure 13 table if Task 2 confirms that it contains the
row-level quantities and selection state required for the comparison.

When supported, build the sequence:

**all stars → \(V_R>0\) → \(V_R<0\)**

and examine \(b-V_Z\) or the released equivalent. If the table contains only
preselected or aggregated values, show only the comparisons directly supported
by those values and document the unavailable operation.

When supported by the released representation, the reader should see that:
- the high-latitude ACS overdensity is associated with a characteristic velocity-sign regime;
- the associated kinematic population extends below the photometric ACS boundary;
- therefore the named density feature is not synonymous with a kinematically isolated object.

Otherwise, the notebook should identify which of these steps is reported by
Lambert and which cannot be tested independently from the release.

### Required "reader prediction" moments

Before revealing a filtered or otherwise contrasted panel, ask the reader what
they expect to happen. This requirement applies only to a comparison supported
by the released representation.

### Try-it-yourself experiments

Limit to two or three scientifically meaningful experiments selected only after
Task 2 establishes which operations the released representation supports. They
may include rebinning, changing a minimum-count mask, switching a \(V_R\) sign
selection, or toggling a photometric boundary overlay. Do not present rebinning,
remasking, or source-level filtering as available for a fixed two-dimensional
array or an already selected table.

### Validation

For every recreated paper panel:
- identify the exact source file/HDU;
- record axis definitions;
- compare axis range and qualitative morphology with the published figure;
- save a compact validation image;
- do not judge success solely from aesthetics.

If a result cannot be independently reconstructed from the public product,
record that limitation in the validation table and reproduce only the supported
intermediate or author-released panel. Accurate limitation reporting is an
acceptable outcome; it must prevent claims of independent reproduction.

Create a small validation table in the notebook:

| Item | Published reference | Reproduction status | Difference |
|---|---|---|---|

### Critical interpretation box

End with:

**Directly supported, if established by Task 2 and the reconstruction**
- ACS and MRi have different kinematics in the sampled region.
- ACS-associated kinematics extend beyond the narrow photometric overdensity.

If either statement is only encoded in an author-produced aggregate and cannot
be independently reconstructed, label it as a reported result and state the
public-data limitation.

**Supported inference**
- ACS is not a fully isolated kinematic island.

**Model-dependent**
- ACS as a particular fold/vertical-wave manifestation.
- MRi as a specific tidal spiral.

**Not demonstrated by this notebook**
- Sagittarius as the unique perturber.

---

# 8. Notebook 3 contract
## `03_from_spiral_winding_to_a_galactic_clock.ipynb`

### Scientific question

**How can a perturbation become a winding phase-space wave, and what assumptions are required before the wave becomes a clock for a satellite encounter?**

### Part A — intuitive toy dynamics

Start with nearly circular planar orbits.

Use the simplest defensible framework:
- analytic epicyclic/precession intuition, or
- lightweight `galpy` orbit integration.

Show:
- an impulsive coherent perturbation;
- differential orbital/precession rates;
- progressive winding with time.

Reader should visually connect:

\[
\text{impulse}
\rightarrow
\text{winding configuration-space structure}
\rightarrow
R-V_\phi\ \text{ridges}
\rightarrow
L_Z-\langle V_R\rangle\ \text{wave}.
\]

The toy model must be explicitly labelled **educational**, not a full Milky Way simulation.

### Part B — link to Antoja-style tidal spiral picture

Explain only the minimum theory required:
- guiding radius / angular momentum intuition;
- \(\Omega\) and \(\kappa\);
- why differential winding changes the spatial frequency of the wave with time;
- why the relevant tidal-arm pattern speed is model-dependent.

Do not recreate all of Antoja et al. (2022).

### Part C — Lambert released timing products

Use the released Figure 9/10 tables only for the stages that Task 2 confirms
their columns and the paper's documented equations support.

Candidate workflow:

\[
\langle V_R\rangle(L_Z)
\rightarrow
\langle V_R\rangle(1/L_Z)
\rightarrow
\text{Fourier representation}
\rightarrow
\text{frequency peak(s)}
\rightarrow
\Delta L_Z
\rightarrow
t.
\]

This chain is not an advance guarantee that every intermediate can be derived
from the public release. Task 2 must determine whether the tables contain the
input wave, transformed samples, Fourier products, timing intermediates, or
some combination. Omit or label as unavailable any unsupported transformation.

At each arrow explicitly label whether it is:
- a data re-expression;
- a numerical operation;
- a dynamical-model mapping.

### Part D — reproduce the reported timing result

Attempt to reproduce Lambert's reported timing calculation from the released products and documented equations.

Important:
- reproduce the calculation only to the extent supported by the public release and paper;
- report any ambiguity or missing information rather than silently guessing;
- treat Lambert's quoted approximately 0.25 Gyr and 1.10 Gyr values as
  comparison targets, not fixtures that the implementation must be forced to
  reproduce;
- if an independent computation is not supported, show the available released
  intermediate and document the missing link instead of tuning choices to the
  published values.

### Part E — robustness / sensitivity

Run a small set of sensitivity experiments only where the released data and
documented equations expose the relevant choice, such as:
- smoothing strength;
- fitting interval;
- Fourier windowing choice if applicable;
- plausible rotation-curve/potential parameter perturbation where the documented equations allow it.

The goal is not parameter fishing. The goal is to demonstrate:

> a Fourier feature can be measured more directly than its mapping to a unique physical encounter time.

### Final causal-inference ladder

End with a diagram or table:

1. **Measured:** velocity wave / released kinematic pattern.
2. **Derived:** Fourier peak(s).
3. **Model-dependent:** convert peak frequency to perturbation time under the tidal-winding framework.
4. **Further interpretation:** associate a perturbation time with Sagittarius.
5. **Not established:** Sagittarius as unique cause.

### Out of scope

- full self-gravitating N-body simulation;
- live Sagittarius model;
- fitting the Milky Way potential;
- claiming Bayesian constraints on Sgr;
- reproducing the original unbinned DR2 analysis.

---

# 9. Notebook visual/pedagogical grammar

Use the same visual structure across all notebooks.

Each major section should contain:

### Question
One sentence.

### Physical intuition
Short prose before equations.

### Data / observable
What quantity is available and from where.

### Code
Short and readable.

### What to notice
One to three concrete visual cues.

### Interpretation ladder
Observation → inference → model dependence.

### 🧪 Try it yourself
A small parameter experiment only when scientifically meaningful.

Avoid:
- walls of text;
- unexplained equations;
- giant code cells;
- decorative plotting;
- excessive interactivity.

---

# 10. `AGENTS.md` scientific guardrails

Create a concise, operational `AGENTS.md` at repository root during Task 1. It
should act as a map to this specification rather than copy it wholesale. Link
to the relevant sections of `CODEX_BUILD_SPEC.md` and include only the
highest-value prohibitions, commands, and validation expectations below.

## Scientific claims

- Never describe a model-dependent interpretation as a direct measurement.
- Preserve wording distinctions such as "consistent with", "can reproduce", "suggests", and "plausibly".
- Sagittarius must not be described as uniquely demonstrated by Lambert.
- Do not claim the public Lambert Zenodo release is the full DESI DR2 stellar catalogue.
- Do not silently invent unavailable columns, source-level cuts, uncertainties, or sample metadata.
- If a public product is insufficient to reproduce a result, state the limitation explicitly.

## Coordinates and units

- Use `astropy.units` wherever practical.
- Adopt Galactocentric frame parameters explicitly and centrally.
- Reconcile the chosen Astropy frame with Lambert's documented definitions
  after source inspection; do not infer conventions from memory.
- Define \(V_R\), \(V_\phi\), \(V_Z\), \(\phi\), and \(L_Z\) sign conventions in Markdown and tests.
- Add at least one sign sanity test.
- Prefer Astropy coordinate transformations to handwritten transformation code.

## Code quality

- reusable code belongs in `src/lambert_lab/`;
- notebooks should read as scientific narratives;
- functions require docstrings when nontrivial;
- no hidden state;
- notebooks must execute top-to-bottom in a clean kernel;
- random processes require a seed;
- downloads must be cached and checksummed where feasible;
- compact inventory, ambiguity, and provenance metadata must be machine-readable
  where applicable and committed; raw downloads and routine generated outputs
  should normally be ignored.

## Validation

- every figure reproduction needs a paper/figure reference;
- compare scientific morphology/numbers, not just appearance;
- tests should catch missing files, wrong units, wrong signs, and broken notebooks;
- do not declare a reproduction successful if a key published feature is missing.
- default tests must run offline; network integration tests must be explicitly invoked.

## Pedagogy

- explain physical intuition before formalism where possible;
- assume an astronomer who is not a Milky Way dynamics specialist;
- avoid unexplained specialist shorthand;
- keep the main path readable without requiring the reader to inspect all helper code.

---

# 11. Acceptance criteria

The project is "journal-club ready" when all of the following are true.

## Repository

- fresh environment installs successfully;
- all three notebooks execute top-to-bottom;
- no notebook requires manual hidden setup;
- data provenance follows the machine-readable schema in Section 3;
- default unit and notebook tests run offline; network integration tests are
  opt-in and explicitly invoked;
- README explains what is and is not reproduced.

## Notebook 1

- reader can explain the physical meaning/sign of \(V_R,V_\phi,V_Z\);
- public data example works;
- one-star sanity check passes;
- coordinate choices are explicit and reconciled against both the chosen
  Astropy frame and Lambert's documented definitions.

## Notebook 2

- central Lambert observational results are reconstructed or simplified only
  to the extent supported by the released representation;
- the ACS/MRi velocity-sign difference and extended ACS-associated kinematics
  are shown when independently supported by the public products;
- any result that cannot be independently reconstructed is explicitly marked
  as reported rather than reproduced, with the blocking data limitation stated;
- data/inference/model distinction is explicit.

## Notebook 3

- toy model clearly demonstrates differential winding;
- reader can understand why wave frequency contains timing information in the adopted model;
- each supported stage of the Fourier workflow is reproducible, while missing
  public inputs or paper-dependent semantics are identified explicitly;
- the published approximately 0.25 Gyr and 1.10 Gyr values are comparison
  targets rather than required test values;
- a supported sensitivity experiment demonstrates model dependence, or the
  notebook explains why the released representation does not permit one;
- Sagittarius is presented as an interpretation, not a direct detection.

## Presentation usefulness

At least one clean educational figure from Notebook 2 and one from Notebook 3 should be exportable directly for journal-club use if desired.

---

# 12. Codex task sequence

Do not ask Codex to build the finished repository in one giant prompt.

## Task 0 — repository reconnaissance and plan

**Model:** GPT-5.6 Sol  
**Goal:** inspect the supplied Lambert paper/project files and this specification; produce a short implementation plan and identify unknowns.  
**No coding beyond trivial inspection.**

Deliver:
- dependency proposal;
- likely data-file mapping;
- risks/unknowns;
- exact files to create.

Stop if Codex invents unavailable data.

## Task 1 — scaffold and reproducibility infrastructure

**Model:** GPT-5.6 Sol

Create:
- repo structure;
- `pyproject.toml`;
- concise operational `AGENTS.md` pointing to this specification;
- download/cache utilities;
- Zenodo fetcher;
- basic tests;
- empty notebook shells with section headings;
- notebook execution test harness.

Do not implement scientific notebook content yet.
Do not perform full FITS/HDU inspection, figure mapping, semantic
interpretation, or create the canonical data inventory; those belong to Task 2.

Acceptance:
- a fresh editable install works with a minimal base dependency set;
- importing the package never triggers a download;
- the Zenodo fetcher supports an explicit destination, caching, exact record
  metadata, and checksum verification;
- an explicitly invoked live integration smoke test can fetch and verify the
  release when network access is authorized;
- default unit tests use local synthetic fixtures, run offline, and cover cache
  and checksum behavior, actionable missing-data errors, coordinate sign sanity,
  and clean execution of the notebook shells;
- raw downloads and routine validation output are ignored, while the locations
  for committed compact provenance products are documented;
- all default offline tests pass.

## Task 2 — Lambert data inventory

**Model:** GPT-5.6 Sol

Inspect every released FITS product and create:
- canonical `data/data_inventory.json`;
- figure ↔ filename ↔ HDU ↔ shape ↔ columns ↔ header description mapping;
- `data/lambert_release_ambiguities.md`.

This task should execute code and inspect outputs.

Do not infer scientific meaning beyond headers/paper without citation.

Task 2 owns full FITS/HDU inspection, figure mapping, semantic interpretation,
and the canonical inventory. Record the exact release metadata and provenance
schema from Section 3. For every FITS file, include every HDU; record HDU class,
extension name, shape, dtype, row/column counts, table column names/formats/units,
header descriptions, finite/invalid counts, axis metadata, panel/slice mapping,
and unresolved questions where applicable.

Acceptance:
- every asset in the resolved Zenodo release is present with verified size and
  checksum, and every FITS HDU appears in the canonical inventory;
- every figure mapping states whether its evidence comes from a filename,
  header, release description, or the paper rather than numerical appearance;
- orientation and axis semantics are checked for two-dimensional arrays;
- Figures 9, 10, 13, and 14 receive explicit table-level inspection;
- the inventory states which Notebook 2 operations are supported and precisely
  which stages of Notebook 3's Fourier/timing chain are publicly reproducible;
- absent, ambiguous, and paper-dependent information is distinguished in the
  ambiguity report, with no invented columns, cuts, uncertainties, or source-level
  interpretation;
- inventory generation is deterministic and does not modify raw files.

## Task 3 — Notebook 1 implementation

**Model:** GPT-5.6 Sol

Build the public DESI DR1/Gaia educational workflow.

Prefer a small cached sample to a massive required download.

Execute notebook end-to-end and validate coordinate/sign tests.

Then stop.

### Human/ChatGPT science review gate

Review:
- adopted solar parameters;
- sign conventions;
- whether the public-data workflow is accurately distinguished from Lambert DR2;
- whether the astronomy is understandable.

Only after review, issue corrections.

## Task 4 — Notebook 2 observational core

**Model:** GPT-5.6 Sol

Implement only:
- figure-product loading;
- selected Lambert observational reconstructions;
- ACS/MRi velocity comparison to the extent supported by Task 2;
- Figure-13-style sign split only if Task 2 establishes that the released table
  supports it;
- validation outputs.

No tidal-model discussion beyond minimal context.

Execute and test.

### Human/ChatGPT science review gate

Check:
- figure mapping;
- axis definitions;
- selection logic;
- direct observation versus inference;
- whether the reconstructed features genuinely match Lambert.

This is the highest-priority review gate.

## Task 5 — Notebook 2 pedagogy/polish

**Model:** Sol or a cheaper capable model if available.

Refine:
- Markdown;
- figure labels;
- prediction prompts;
- compact "try it yourself" controls;
- exported clean figures.

No new scientific claims.

## Task 6 — Notebook 3 toy dynamics

**Model:** GPT-5.6 Sol

Build the pedagogical winding model first.

Acceptance:
- simple initial conditions;
- physically interpretable output;
- relationship among spiral/ridge/radial-wave projections demonstrated;
- toy nature clearly labelled;
- no attempt yet to reproduce Lambert timing.

### Human/ChatGPT science review gate

Check physical interpretation before proceeding.

## Task 7 — Notebook 3 Lambert Fourier/timing analysis

**Model:** GPT-5.6 Sol

Use released Figure 9/10 tables and paper equations.

Implement:
- exact data transformations supported by the paper/release;
- Fourier calculation where the released inputs and documented method permit it;
- timing mapping where the required equations and assumptions are documented;
- comparison to published values;
- supported sensitivity tests.

If required information is missing, document the gap rather than guess or tune
the analysis to recover the published values.

## Task 8 — final engineering audit

**Model:** GPT-5.6 Sol first; escalate only if necessary.

Fresh-clone simulation:
- install;
- download/cache;
- run tests;
- execute notebooks in order;
- compare validation outputs;
- check README/provenance;
- flag stale or misleading scientific claims.

Do not use Astra merely for polish.

---

# 13. Model/usage strategy

The default implementation model should be **GPT-5.6 Sol**.

Use a cheaper model for:
- formatting;
- minor README edits;
- simple refactors;
- lint fixes;
- mechanical notebook cleanup.

Reserve **Astra** only for a well-defined hard problem, for example:
- a persistent numerical discrepancy in the Fourier reproduction;
- a difficult coordinate/kinematic bug after independent checks;
- a complex architectural failure;
- one final adversarial audit if Sol repeatedly fails.

Do not spend Astra on:
- roadmap writing;
- repository scaffolding;
- prose cleanup;
- routine tests;
- simple plotting.

---

# 14. Optional ChatGPT Work audit

Do this **only after** the local specification exists and before expensive implementation if unresolved external-data questions remain.

Suggested Work prompt:

> Audit the attached `CODEX_BUILD_SPEC.md` for a three-notebook educational/reproducibility repository centred on Lambert et al. (2026). Do not build the repository.
>
> Research only what is necessary to challenge feasibility and scientific correctness. Prioritize primary/authoritative sources: Lambert et al. (2026), the Lambert Zenodo figure-data release, DESI DR1 MWS documentation/tutorials, Astropy coordinate documentation, galpy documentation, and directly relevant methodological papers.
>
> For each proposed notebook:
> 1. verify that the required public data actually exist;
> 2. identify which outputs can be reproduced exactly versus only pedagogically approximated;
> 3. identify scientifically dangerous shortcuts, coordinate/sign pitfalls, hidden assumptions, and selection-function issues;
> 4. verify that the proposed software stack is appropriate;
> 5. recommend the minimum validation tests;
> 6. flag anything that would overstate what Lambert's public data support.
>
> Return:
> - a short go/no-go verdict for each notebook;
> - a corrected data-source map;
> - a list of blocking uncertainties;
> - recommended changes to the build spec;
> - acceptance criteria that would falsify a bad implementation.
>
> Do not spend time on general Milky Way background or a broad literature review. Do not rewrite the notebooks. Do not generate slides.

Use Work as an **adversarial feasibility audit**, not as a substitute for the scientific design already established.

---

# 15. Recommended immediate next move

1. Keep this file at repository root as `CODEX_BUILD_SPEC.md`.
2. Complete **Task 0** reconnaissance and review its plan.
3. Apply any approved Task 0 corrections to this specification as **Task 0.5**.
4. Run Task 1, including creation of the concise operational `AGENTS.md` and an
   explicitly invoked live-fetch smoke test when network access is authorized.
5. Run Task 2 to inspect the release and commit the canonical inventory,
   ambiguity report, and compact provenance metadata.
6. Only then decide whether a ChatGPT Work audit is still worth the shared allowance.
7. Build Notebook 1.
8. Build Notebook 2 and review it most carefully.
9. Build Notebook 3 last.

The first milestone is **not** "three notebooks exist."

The first milestone is:

> **The data/provenance layer is correct, the figure-release inventory is understood, and Codex cannot silently confuse figure products with the unpublished DR2 stellar catalogue.**

Once that foundation is secure, the notebooks can be built efficiently without spending high-tier model usage correcting avoidable scientific mistakes.
