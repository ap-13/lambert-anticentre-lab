# Lambert release forensic findings and ambiguities

Scope: Zenodo record **18236902**, DOI
`10.5281/zenodo.18236902`, cached as
`Lambert_DESI_DR2_MW_outer_disk_figures_data.zip`. The archive is a release of
downstream figure products, not the unpublished DESI DR2 stellar catalogue.
The canonical per-member, per-HDU statistics and semantics are in
`data/data_inventory.json`.

Authoritative cross-check: Lambert et al. (2026), *The Astronomical Journal*
171:292, DOI `10.3847/1538-3881/ae5100`, with arXiv `2601.14562` as an
accessible fallback. Paper locations below refer to the published article.

## Release integrity and contents

- The one cached ZIP is 389,969 bytes and matches Zenodo's advertised
  `md5:20eda5915d328a9584cc4a6213bc8834`; its independently recorded SHA-256 is
  in the JSON inventory. Every ZIP member passes CRC verification.
- The ZIP has 40 members: 26 genuine FITS files (23 two-dimensional primary
  image arrays and three binary-table files) plus 14 `__MACOSX/._*.fits`
  AppleDouble resource-fork members. The latter have `.fits` suffixes but are
  not FITS files (`SIMPLE` is absent).
- The 26 FITS files contain 29 HDUs: 23 image primary HDUs, three empty table
  primary HDUs, and three binary-table extensions. No `EXTNAME` is set on any
  extension.
- The release supplies products for published Figures 3--6 and 8--14, except
  the Figure 3 top-left R--Z count panel. No product is present for Figures 1,
  2, or 7. The three files named `*fig2.fits` map to published Figure 3, not
  Figure 2.

## What the focal products contain

### Figure 9 — `Lz_Vr_fig9.fits`, HDU 1

This is a 70-row, three-column binned summary, not a star table. It contains
`angular momentum [kpc km/s]`, `radial velocity [km/s]`, and
`radial velocity uncertainty [km/s]`. The first column is **L_Z**, not
`1/L_Z`; its 70 values run from 1500 to 4457.142857 kpc km/s at a constant
42.857143 kpc km/s spacing. All values are finite. The table therefore supports
plotting the released wave and deterministically re-expressing its coordinates
as `1/L_Z`.

The published Section 3.5 states that the selected input is the MSTO
anticenter/MRi-region sample with 8 < R < 23 kpc, Z < 5 kpc, and
175° < l < 185°. It identifies the errors as standard errors on the mean. The
source stars, bin membership/counts, weights, and upstream selection columns
are not released.

### Figure 10 — `FFT_fig10.fits`, HDU 1

This is a 35-row, three-column author-derived Fourier product containing
frequency, power, and a 1-sigma power spread. It is a spectrum, not a set of
Fourier inputs. Its frequency grid is finite, descending, and uniformly spaced
from 27000 to 771.428571 in steps of -771.428571 in the paper's reciprocal
`L_Z^-1` coordinate units. Power normalization and units are not documented.

The Figure 9 table is described by the paper as the input to Figure 10, but an
exact independent FFT is not specified: no method is given for resampling or
interpolating a series uniform in L_Z onto the nonuniform `1/L_Z` coordinates;
detrending, windowing, padding, FFT normalization, and random seed are also
absent. The released 35-point spectrum supports grid-level peak localization,
but the samples/windows/covariance from the two Gaussian peak fits are not
released. Published Section 3.5 and Figure 10 give the fitted frequencies as
1313.0 ± 477.2 and 5878.6 ± 1471.9 in the reciprocal transformed-coordinate
units.

### Figures 13 and 14 — `fig13_and_fig14_table.fits`, HDU 1

This is a 7,708-row table with four per-row values: Galactic latitude,
Galactic longitude, V_Z, and V_R. Published Sections 3.6--3.7 and the Figure
13/14 captions establish that these are individual rows from the authors'
already-selected MSTO anticenter sample with heliocentric distance >10 kpc;
they are not binned values and are not the full DESI DR2 source catalogue.

V_R is present per row, so Figure 13's `all -> V_R>0 -> V_R<0` experiment can
be independently recomputed after applying the published 10-degree longitude
subsets from 150° to 200°. The release does not merely provide author-made
sign subsets. Likewise, V_Z is present per row, so Figure 14's all/positive/
negative V_Z subsets can be recomputed in its two published longitude ranges.
All four columns are finite and neither velocity contains an exact zero.

The table also contains longitudes from 200° to 220° that are outside the
Figure 13/14 plotted subsets. It does not contain a source identifier,
distance, uncertainties, weights, photometry, metallicity, selection flags, or
the photometric ACS boundary/width values.

## Two-dimensional array handling

All 23 image products are already-binned author products. In NumPy, their
shape is `(vertical_axis, horizontal_axis)`. Direct display with
`origin="lower"` and the header-stated extent reproduces the published
orientation; no transpose is required. This orientation was checked against
the author panels, while the physical axis identities and ranges come from
FITS `COMMENT` cards and paper captions, not from numerical appearance.

There are no FITS WCS keywords, coordinate arrays, or explicit bin edges.
Therefore the stated extents are metadata-derived plotting extents rather than
recoverable exact edges. Figure 4 arrays cover b=15°--45°, whereas the paper
panels display b=20°--40°; reproducing those panels requires a display crop.
NaNs encode unavailable or author-masked bins, but no separate mask HDU exists.
For Figure 6 the paper reports removal of bins with five or fewer stars, and
for Figure 8 it reports removal below 20 stars. The threshold cannot be changed
because the needed per-bin counts are absent from the median-velocity arrays.

The arrays contain the following kinds of values:

- Figure 3: star counts and median V_phi; the R--Z count panel is absent.
- Figure 4: uncorrected counts, completeness-weighted counts, and a
  completeness ratio.
- Figure 5: median V_R, median V_Z, and median [Fe/H] in l--b and R--Z.
- Figure 6: an author-produced density residual, median V_R, median
  `V_phi-<V_phi(R)>`, and median V_Z.
- Figure 8: completeness-weighted density, median V_R, and median V_Z.
- Figure 11: Pan-STARRS binned star counts, without the fitted ACS parabolas.
- Figure 12: median V_R, median V_Z, and median [Fe/H].

Because these are fixed aggregates, rebinning, changing source selections,
recomputing medians/residual models, or remasking at a new count threshold is
not scientifically legitimate from the arrays alone. Cropping a display or
changing a color scale is legitimate; treating such display operations as a
new measurement is not.

## NOT PRESENT IN PUBLIC RELEASE

- **Source-level DESI DR2 catalogue:** absent. Exact blocker: all 23 image
  products contain only one primary 2-D array, and the Figure 9 table contains
  only binned summaries.
- **Upstream rows/counts for Figures 3--6, 8, 9, and 12:** absent, preventing
  new source cuts, binning, medians, residual fits, or thresholds.
- **Image uncertainties:** absent for all 2-D arrays; there are no companion
  error HDUs. Figure 9 alone has one uncertainty column and Figure 10 has a
  power-spread column.
- **Exact image bin edges/WCS:** absent from every image HDU (`CTYPE*`,
  `CUNIT*`, `CRPIX*`, `CRVAL*`, and `CDELT*` are absent).
- **Figure 10 preprocessing and Monte-Carlo realization details:** no
  interpolation/resampling rule, detrending/windowing/padding choice, FFT
  normalization, random seed, individual spectra, or peak-fit data/covariance.
- **ACS photometric boundary parameters:** the coefficients, fit points,
  fitting procedure, and evaluated boundary/width vectors are absent from
  `lb_panstarrs_fig11.fits`, `fig13_and_fig14_table.fits`, and all headers.
- **Figures/panels:** no products for published Figures 1, 2, or 7, and no
  Figure 3 top-left R--Z count array.

## PRESENT BUT AMBIGUOUS

- **Figure 9 statistic/range/bin count:** `Lz_Vr_fig9.fits`, HDU 1 has 70
  rows. Published Figure 9's caption says *mean*, 70 bins, and 1400--4500;
  published Section 3.5 says *median*, 75 bins, and 2000--4500. The actual
  released centers are 1500--4457.142857. This conflict cannot be resolved
  from the release.
- **Figure 10 Monte-Carlo statistic:** `FFT_fig10.fits`, HDU 1. The published
  caption calls the black spectrum the median; Section 3.5 calls it the
  average. The FITS column is only `Power`.
- **Figure 10 power semantics:** `Power` and `1-sigma on the Power` have no
  `TUNIT`, and neither the header nor paper defines the normalization.
- **Figure 5 angular binning:** the six Figure 5 headers/shapes imply 42 by 12
  bins over 70° by 20° (0.6 bin/degree), while the published caption states one
  bin/degree.
- **Figure 6 X bins:** each `XY_*fig6.fits` header states 28 X bins over
  8--23 kpc, while the paper states two bins/kpc (which would require 30 bins
  across that range). No edges resolve the mismatch.
- **Figure 8 V_phi bins:** the three `RVphi_*fig8.fits` products have 32 rows
  across the stated 140--270 km/s range, while the paper states 0.25 bins per
  km/s (32.5 bins across the range). No edges are released.
- **Figure 8 V_phi wording/sign:** each `RVphi_*fig8.fits` `COMMENT` calls the
  vertical coordinate “negative azimuthal velocity,” while the published
  Figure 8 and the paper's sample cut display/use positive V_phi from roughly
  140 to 270 km/s. The paper resolves how to label the published panels, but
  the contradictory header wording remains unexplained and must not be used to
  infer a sign flip.
- **NaN cause outside explicit thresholds:** Figure 5 and 12 headers do not
  distinguish empty bins from other author masking; only the NaN state itself
  is present.
- **Timing uncertainty:** Section 3.5 reports 1.10 ± 0.28 Gyr, while the
  abstract, Table 1, and summary report 1.10 ± 0.23 Gyr. Equation (1) with the
  quoted 5878.6 ± 1471.9 peak yields approximately 1.08 ± 0.27 Gyr, supporting
  the 0.28 rounding but not resolving editorial intent.

## REQUIRES PAPER INTERPRETATION

- **Figure mappings where names disagree or omit a number:** the files named
  `XY_hist_fig2.fits`, `XY_vphi_fig2.fits`, and `RZ_vphi_fig2.fits` map to
  published Figure 3; the three `lb_completeness_*` files map to Figure 4.
  Evidence is the FITS axis/quantity comments combined with the published
  captions.
- **Selections and panel roles:** image headers often name the broad sample,
  but the detailed R, Z, Y, distance, and longitude selections and panel order
  come from published Sections 2.3--3.7 and the corresponding captions.
- **Figure 9 uncertainty and timing-input meaning:** the standard-error
  interpretation and sample cuts come from published Section 3.5; no table
  header comments state them.
- **Figure 10 units and workflow:** the frequency's transformed-coordinate
  meaning, 1,000 Monte-Carlo runs, peak-fit interpretation, and timing mapping
  come from published Section 3.5 and Equation (1).
- **Figures 13/14 row and subset meaning:** individual-star status, the
  distance-selected parent sample, longitude slices, sign subsets, and plot
  roles come from published Sections 3.6--3.7 and captions; the FITS table has
  column names only.

## RESOLVED BY PAPER/HEADER

- **L_Z versus inverse:** Figure 9 releases L_Z. Inverse L_Z is a later
  transformation described in published Section 3.5.
- **Raw versus aggregate:** all image products are already-binned arrays;
  Figure 9 is binned; Figure 10 is derived; Figures 13/14 contain individual
  rows from an already selected sample.
- **Figure 12 binning typo:** each Figure 12 header says “1 bin per 2 kpc” for
  angular axes. The shape/range and published caption resolve this as 2° per
  bin.
- **Array orientation:** paper comparison plus FITS/NumPy ordering establishes
  `origin="lower"`, no transpose, horizontal axis in NumPy dimension 1 and
  vertical axis in dimension 0.
- **Figure 13 V_R split:** V_R is a per-row column, so the sign split is not
  pre-baked and is independently reproducible within the released selection.
- **Timing conversion:** published Equation (1), n=0, V0=239.26 km/s, and
  R0=8.277 kpc convert the two quoted Fourier frequencies to approximately
  0.24 and 1.08 Gyr (before the authors' rounding). This is a model-dependent
  conversion, not a direct measurement or unique demonstration of Sagittarius.

## Capability matrix

### Notebook 2

| Question | Classification | Evidence |
|---|---|---|
| Can Figures 5/6-style products be reconstructed? | YES — directly supported by released data | Fixed 2-D arrays for all Figure 5 and 6 panels are present with header/paper semantics. |
| Can binning be changed? | NO — required source information is absent | Figure 5/6 products are already-binned arrays without stellar rows or bin edges. |
| Can minimum-count thresholds be changed? | NO — required source information is absent | Counts underlying the velocity/metallicity bins are not released, so the NaN masks cannot be recalculated. |
| Can source-level selections be changed? | NO — required source information is absent | The image products contain no source rows or upstream selection columns. |
| Can the ACS/MRi velocity-sign result be independently reconstructed? | PARTIAL — only some stages are supported | Author-binned maps encode the opposite-sign regions, but their full selection and aggregation cannot be independently rebuilt. |
| Can the Figure-13 V_R sign split be independently recomputed? | YES — directly supported by released data | The 7,708-row table has per-row l, b, V_Z, and V_R, permitting the paper's longitude and sign filters. |
| Can the photometric ACS boundary be overlaid/changed? | NO — required source information is absent | The count map exists, but fitted parabola coefficients, fit data/procedure, and boundary/width vectors do not. |

### Notebook 3

| Question | Classification | Evidence |
|---|---|---|
| Can the L_Z-<V_R> wave be reconstructed? | YES — directly supported by released data | Figure 9 supplies 70 L_Z-bin coordinates, V_R summaries, and V_R uncertainties. |
| Can the transformation to 1/L_Z be recomputed? | YES — directly supported by released data | Every L_Z coordinate is finite and nonzero, so inversion is an exact re-expression. |
| Can the Fourier transform be independently recomputed? | PARTIAL — only some stages are supported | The wave/errors exist, but resampling from uniform L_Z to nonuniform 1/L_Z and FFT preprocessing/normalization are undocumented. |
| Can the published Fourier peaks be independently measured? | PARTIAL — only some stages are supported | The released spectrum permits grid-level peaks, but Gaussian fit inputs/windows and fitted parameters/covariance are absent. |
| Can the timing conversion be independently recomputed? | YES — directly supported by released data | Published Equation (1), constants, assumptions, and peak frequencies reproduce the rounded timing calculation. |
| Which assumptions/equations must come from the paper? | PARTIAL — only some stages are supported | The circular-curve form and n, epicycle/corotating-arm assumptions, Equation (1), V0, R0, Monte-Carlo count, and winding-time interpretation are paper-supplied. |

A targeted external science audit is recommended before Task 3, limited to the
Figure 9-to-10 resampling/FFT/peak-fit procedure and the published internal
inconsistencies. An author clarification or preserved analysis code would be
more useful than a broad literature review.
