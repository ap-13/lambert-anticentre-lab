# Notebook 3 methodological/reproducibility audit

Audit date: 2026-09-20.

## Executive verdict

**Exact-reproduction classification: NO.**

The released Figure 9 table permits a scientifically meaningful independent Fourier analysis and reproduces several numerical fingerprints of Figure 10, but it does not contain enough information to regenerate the released Figure 10 power and uncertainty arrays exactly. The missing information includes the final Monte Carlo sampling rule and seed, aggregation definition, uncertainty-band convention, and Gaussian fitting intervals.

There is, however, unusually strong evidence for how the released spectrum’s frequency axis and basic power were constructed:

- The 70 released `L_Z` values are uniformly spaced in `L_Z`, from `1500` to `4457.1429\ {\rm kpc\,km\,s^{-1}}`, but are nonuniform in `1/L_Z`.
- Every released Figure 10 frequency is reproduced exactly by applying a 70-point FFT frequency formula with
  ```math
  d=(1/L_{Z,2})-(1/L_{Z,1}),
  ```
  i.e. the spacing of only the first two transformed samples, and then retaining the 35 positive frequencies. This gives `771.4286,\ldots,27000` in the released order.
- The released power has correlation `r=0.99986` with the unnormalized `|{\rm FFT}(V_R)|^2` from the Figure 9 central values. The difference is an approximately constant positive noise floor, consistent with averaging noisy periodograms, although its precise magnitude is not explained by the published procedure.
- A public Mika Lambert notebook contains an earlier implementation with exactly this nonuniform-coordinate/first-spacing FFT pattern, but it uses 60 bins, a modal ridge estimator, `V_R/L_Z`, exploratory smoothing, and manually chosen peak indices—not the final Figure 9 statistic or complete Figure 10 pipeline. ([GitHub](https://github.com/mikalambert/UCSC_DESI_MW?utm_source=chatgpt.com "GitHub - mikalambert/UCSC_DESI_MW: My first year project code repository"))

Thus, the spectrum’s likely computational lineage is partially recoverable; the final published stochastic calculation is not.

## 1. Public code and supplementary-material search

Zenodo record 18236902 remains version `v1`. It supplies one checksum-identified ZIP described as figure data; no scripts, notebooks, configuration, random seed, or provenance metadata accompany it, and no newer version is listed. ([Zenodo](https://zenodo.org/records/18236902?utm_source=chatgpt.com "Data for Signatures of a Tidally Induced Spiral Arm at the Anticenter of the Milky Way and a Kinematically Extended Anticenter Stream Using DESI DR2"))

Mika Lambert’s public GitHub account lists four repositories. The relevant repository is `UCSC_DESI_MW`, described as her first-year project on Milky Way disk disequilibrium. It has eight commits, no releases, and contains `desi_Y3_loa_ridges_spirals_arches_refining_cut.ipynb`. ([GitHub](https://github.com/mikalambert?utm_source=chatgpt.com "mikalambert (Mika Lambert)")) Her public research page links the Lambert paper and describes the same DESI/Sagittarius project. ([mikalambert.github.io](https://mikalambert.github.io/?utm_source=chatgpt.com "Mika Lambert's website"))

Direct inspection of that notebook found an earlier FFT prototype:

- 60 uniform `L_Z` bins over `1500`–`4500`;
- a modal `V_R` ridge extracted from a two-dimensional count histogram, despite the variable name `col_median`;
- `V_R/L_Z` as the transformed signal;
- direct FFT of samples that are nonuniform in `1/L_Z`;
- the first `1/L_Z` spacing passed to the FFT frequency routine;
- unnormalized `|{\rm FFT}|^2`;
- exploratory Gaussian smoothing;
- threshold-based peak selection and hard-coded four-bin Gaussian fitting windows.

This notebook is an important historical precursor, not executable provenance for the published result: it does not contain the final 70-row statistic, the published peaks, or the documented 1000-realization Figure 10 calculation.

No author-provided Antoja analysis code or data, and no additional Lambert final-analysis repository, release, notebook, or supplementary method statement, was located in the official arXiv records, author webpages, Zenodo record, or credibly connected public repositories.

## 2. Lambert method reconstruction

### Figure 9 and sample

Lambert restricts the timing analysis to the MRi MSTO anticentre sample with `8<R<23` kpc, `Z<5` kpc, and `175^\circ<l<185^\circ`. The adopted Fourier coordinate is

```math
x=L_Z^{(n-1)/(n+1)},
```

with `n=0`, hence `x=1/L_Z`. ([arxiv.org](https://arxiv.org/html/2601.14562v1?utm_source=chatgpt.com "Signatures of a Tidally Induced Spiral Arm at the Anticenter of the Milky Way and a Kinematically Extended Anticenter Stream Using DESI DR2"))

The paper is internally inconsistent:

| SourceFigure 9 statisticBins/rangeUncertainty |                                   |                                                        |                         |
| --------------------------------------------- | --------------------------------- | ------------------------------------------------------ | ----------------------- |
| Published caption                             | mean `V_R`                        | 70 bins, `1400`–`4500`                                 | standard error on mean  |
| Published body                                | median `V_R`                      | 75 bins, `2000`–`4500`                                 | standard error on mean  |
| arXiv v1 caption                              | mean `V_R`                        | 70 bins, `1400`–`45000`, evidently a range typo        | error on mean           |
| arXiv v1 body                                 | median `V_R`                      | 75 bins, `2000`–`4500`                                 | bootstrap uncertainty   |
| Released FITS                                 | unlabeled central `V_R` statistic | 70 rows, actual `1500`–`4457.1429` left-edge-like grid | one uncertainty per row |

The arXiv source displays these caption/body discrepancies directly. ([arxiv.org](https://arxiv.org/html/2601.14562v1?utm_source=chatgpt.com "Signatures of a Tidally Induced Spiral Arm at the Anticenter of the Milky Way and a Kinematically Extended Anticenter Stream Using DESI DR2")) The arXiv version also incorrectly defines `L_Z=R\,V_Z`; the published AJ version corrects this to `L_Z=R\,V_\phi`.

Consequently, Figure 9 can be replotted exactly from the release, but its per-star estimator and uncertainty construction cannot be reconstructed uniquely.

### FFT, Monte Carlo, and peaks

Lambert states that:

- an FFT is performed on `V_R` versus `L_Z^{(n-1)/(n+1)}`;
- the `V_R` uncertainties are Monte Carlo sampled;
- 1000 FFT realizations are run;
- Figure 10 shows a “power spectrum” with a `1\sigma` band;
- two peaks are fitted with Gaussians;
- the Gaussian widths are used as uncertainties in peak location. ([arxiv.org](https://arxiv.org/html/2601.14562v1?utm_source=chatgpt.com "Signatures of a Tidally Induced Spiral Arm at the Anticenter of the Milky Way and a Kinematically Extended Anticenter Stream Using DESI DR2"))

But “power” is not defined mathematically. The caption says the central spectrum is the **median**, while the body says **mean/average**. Neither the draw distribution nor the definition of “`1\sigma`” is given. Gaussian fitting windows, weighting, baseline, initial conditions, and whether fits were performed per realization or on the aggregate spectrum are absent.

The reported frequencies are

```math
f_1=1313.0\pm477.2,\qquad f_2=5878.6\pm1471.9,
```

in reciprocal-`x` units. ([arxiv.org](https://arxiv.org/html/2601.14562v1?utm_source=chatgpt.com "Signatures of a Tidally Induced Spiral Arm at the Anticenter of the Milky Way and a Kinematically Extended Anticenter Stream Using DESI DR2")) These fitted centers do not need to coincide with the released FFT bins.

### Time conversion and sensitivities

Lambert uses Antoja’s wavelength relation

```math
\Delta x= \left(\frac{V_0}{R_0^n}\right)^{-2/(1+n)} \frac{\pi/t}{1-\tfrac12\sqrt{2(n+1)}}, \quad x=L_Z^{(n-1)/(n+1)},
```

with Fourier frequency `f=1/\Delta x`, `n=0`, `V_0=239.26\ {\rm km\,s^{-1}}`, and `R_0=8.277` kpc. ([arxiv.org](https://arxiv.org/html/2601.14562v1?utm_source=chatgpt.com "Signatures of a Tidally Induced Spiral Arm at the Anticenter of the Milky Way and a Kinematically Extended Anticenter Stream Using DESI DR2")) The terminology is slightly loose: the equation contains a wavelength `\Delta x`, while Figure 10 reports its reciprocal Fourier frequency.

The conversion gives `0.25\pm0.09` and `1.10\pm0.28` Gyr by direct propagation of the quoted frequency widths. The second uncertainty is inconsistent with the abstract and Table 1, which give `1.10\pm0.23` Gyr. ([air.unimi.it](https://air.unimi.it/handle/2434/1272840?utm_source=chatgpt.com "Signatures of a Tidally Induced Spiral Arm at the Anticenter of the Milky Way and a Kinematically Extended Anticenter Stream Using DESI Data Release 2")) Numerically, `1.10(1471.9/5878.6)=0.275` Gyr, supporting `0.28` rather than `0.23`.

The printed sensitivity slopes are `n=-0.01,-0.5,-0.1`. Two peaks reportedly persist; steeper slopes give more recent times, with all results within `1\sigma` of the flat-curve result except the high-frequency `n=-0.1` result at `1.10\sigma`. No numerical table is supplied. ([arxiv.org](https://arxiv.org/html/2601.14562v1?utm_source=chatgpt.com "Signatures of a Tidally Induced Spiral Arm at the Anticenter of the Milky Way and a Kinematically Extended Anticenter Stream Using DESI DR2")) The value `-0.5` should not silently be changed to `-0.05`, even though it is conspicuous.

## 3. Antoja et al. (2022) reconstruction

Antoja transforms `L_Z` because, at fixed time, the oscillation frequency varies with `L_Z`. For a power-law circular-velocity curve `V_c=V_0(R/R_0)^n`, the transformation `L_Z^{(n-1)/(n+1)}` makes the model’s minimum-`V_R` bands straight and equally spaced in transformed-coordinate–azimuth space. For `n=0`, this becomes `L_Z^{-1}`. ([arxiv.org](https://arxiv.org/html/2206.03495v3?utm_source=chatgpt.com "Tidally induced spiral arm wraps encoded in phase space"))

The actual signal is the mean `V_R` wave. In the ideal-model example and Milky Way application, Antoja divides by `L_Z` to flatten its amplitude, stating that this does not affect the Fourier result. Figures and prose alternately call the plotted signal `V_R` or `V_R/L_Z`. The plotted Fourier statistic is explicitly **Fourier amplitude**, not a defined power normalization. ([arxiv.org](https://arxiv.org/html/2206.03495v3?utm_source=chatgpt.com "Tidally induced spiral arm wraps encoded in phase space"))

Antoja does **not** specify:

- resampling or interpolation onto a uniform transformed-coordinate grid;
- how many transformed-coordinate samples are used;
- treatment of reversed `1/L_Z` order;
- mean removal or detrending;
- a window function;
- zero-padding;
- FT normalization;
- a general algorithm for peak finding.

In the ideal model, the clear maximum is compared with the analytical expectation. In the Milky Way application, sampling is described as sparse. The low-frequency feature lies at the first available Fourier frequency and is therefore only an upper limit. For the other peak, the uncertainty range is half the separation between the peak and neighboring frequency points—not a Gaussian fit. ([arxiv.org](https://arxiv.org/html/2206.03495v3?utm_source=chatgpt.com "Tidally induced spiral arm wraps encoded in phase space"))

Antoja tests `n=0,-0.03,-0.06,-0.1`, uses `V_c=239.26\ {\rm km\,s^{-1}}` and `R_0=8.277` kpc, and obtains approximate times `<0.6` and `0.8`–`2.1` Gyr. The authors explicitly call the Milky Way application “back-of-the-envelope.” ([arxiv.org](https://arxiv.org/html/2206.03495v3?utm_source=chatgpt.com "Tidally induced spiral arm wraps encoded in phase space"))

The limits demonstrated are scientifically important:

- Ideal phase-mixing models recover known impact times and separate two imposed perturbations. ([arxiv.org](https://arxiv.org/html/2206.03495v3?utm_source=chatgpt.com "Tidally induced spiral arm wraps encoded in phase space"))
- In the realistic N-body model, the transformed-coordinate FT can be weaker than the FT in `L_Z`; possible causes include a non-power-law potential, imperfect transformation, binning, particle resolution, overlapping impacts, and bar formation. ([arxiv.org](https://arxiv.org/html/2206.03495v3?utm_source=chatgpt.com "Tidally induced spiral arm wraps encoded in phase space"))
- In real Milky Way data, `L_Z` can give more defined peaks than `L_Z^{-1}`, and bar/self-gravity/other perturbations prevent unique attribution. ([arxiv.org](https://arxiv.org/html/2206.03495v3?utm_source=chatgpt.com "Tidally induced spiral arm wraps encoded in phase space"))

## 4. Reproducibility matrix

| OperationDocumented by LambertDocumented by AntojaPresent in releaseIndependently reproducible |                                                         |                            |                               |                                                        |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------- | -------------------------- | ----------------------------- | ------------------------------------------------------ |
| Stellar selection                                                                              | Yes                                                     | Different Gaia selection   | No source stars               | No                                                     |
| Figure 9 statistic                                                                             | Contradictory mean/median and 70/75 bins                | Mean `V_R` wave            | Central values only           | Plot: yes; estimator: no                               |
| Figure 9 uncertainty                                                                           | Standard error in AJ; bootstrap in arXiv v1             | Not the Lambert procedure  | One uncertainty column        | Values: yes; construction: no                          |
| `x=L_Z^{(n-1)/(n+1)}`                                                                          | Yes                                                     | Derived explicitly         | `L_Z` supplied                | Yes                                                    |
| `n=0\Rightarrow x=1/L_Z`                                                                       | Yes                                                     | Yes                        | Derivable                     | Yes                                                    |
| `V_R` versus `V_R/L_Z`                                                                         | Says `V_R`                                              | Uses `V_R/L_Z` in examples | `V_R` supplied                | Both testable; author choice not fully secure          |
| Uniform-`x` sampling                                                                           | Not stated                                              | Not stated                 | No resampled signal           | No exact method                                        |
| Detrending/window/padding                                                                      | Not stated                                              | Not stated                 | No                            | No                                                     |
| Fourier statistic                                                                              | “Power spectrum,” undefined                             | FT amplitude               | Power array supplied          | Shape approximately; definition not documented         |
| Frequency grid                                                                                 | Not stated                                              | Not stated                 | 35 frequencies                | Exactly fingerprinted, not methodologically documented |
| Monte Carlo                                                                                    | 1000 uncertainty draws                                  | Not used for Lambert data  | Aggregate spectrum and spread | No exact draws/aggregation                             |
| Peak location                                                                                  | “Two clear peaks”                                       | Visual/discrete maxima     | Spectrum supplied             | Discrete peaks yes                                     |
| Gaussian fitting                                                                               | Gaussian width used as location uncertainty; no windows | Not used in MW analysis    | Fits not supplied             | No                                                     |
| Frequency-to-time mapping                                                                      | Equation and constants given                            | Equation derived           | Frequencies supplied          | Yes                                                    |
| Rotation-curve sensitivity                                                                     | Printed slopes, no results table                        | `0,-0.03,-0.06,-0.1`       | No                            | Conceptually yes; Lambert results no                   |

## 5. Exact-reproduction verdict

**NO — exact numerical regeneration is not possible from Figure 9 alone.**

What is recoverable:

- the apparent 70-point FFT frequency-grid convention;
- the nearly exact deterministic spectral shape from unnormalized `|{\rm FFT}(V_R)|^2`;
- the published timing conversion;
- a reasonable uncertainty-propagation experiment.

What remains underdetermined:

- why nonuniform `1/L_Z` samples apparently received an ordinary FFT;
- the Monte Carlo draw distribution and effective scale;
- mean versus median aggregation;
- definition of the released `1\sigma` spread;
- seed and realization handling;
- peak windows and fit weighting;
- whether any smoothing entered the final fits.

The public precursor helps explain the frequency grid but cannot elevate an inferred historical implementation into a documented or scientifically preferred method.

## 6. Recommended Notebook 3 architecture

1. **Short physical motivation.** Introduce the impulse-to-wave chain without fitting the data.
2. **Released-data layer.** Load only the released Figure 9 and Figure 10 tables. State that Figure 9 central values are labeled `V_R`, but mean/median provenance is unresolved.
3. **Forensic reproduction layer.** Demonstrate that the released frequency grid follows the first-spacing/nonuniform-`1/L_Z` FFT convention and that raw `|{\rm FFT}(V_R)|^2` nearly reproduces the released shape. Label this a diagnostic of provenance, not the preferred estimator.
4. **Independent primary analysis.**
   - transform to `x=1/L_Z`;
   - sort `x` ascending;
   - resample onto 70 uniformly spaced `x` points spanning only the observed support;
   - use linear interpolation as the baseline;
   - propagate each released `V_R` uncertainty with Gaussian draws, explicitly as an assumption;
   - subtract the realization mean;
   - apply a declared window—preferably Hann—with the rectangular window shown as a sensitivity;
   - compute a one-sided FFT and define the normalization explicitly;
   - show the central-value periodogram alongside the Monte Carlo median and central 68% interval.
5. **Peak reporting.** Report discrete resolution, local maxima, and Monte Carlo peak distributions. Any Gaussian fits should be descriptive and use declared windows. Do not call a fitted Gaussian width a posterior uncertainty.
6. **Comparison layer.** Compare the independent spectrum with the released Figure 10 spectrum after a clearly declared shape normalization. Do not tune interpolation, windows, or fitting ranges to improve agreement.
7. **Timing layer.** Use the published `1313.0` and `5878.6` frequencies separately for the exact documented conversion. Report `0.25\pm0.09` and `1.10\pm0.28` Gyr, while noting the published `0.23/0.28` conflict.
8. **Model-dependence layer.** Recompute both transformed spectra and times when varying `n`; changing only the conversion equation is insufficient because `x` itself depends on `n`.

## 7. Five high-value sensitivity experiments

1. **Sampling and interpolation:** direct legacy-style FFT of nonuniform `1/L_Z` samples versus uniform-`x` linear and PCHIP interpolation. This exposes the central reproducibility issue.
2. **Signal definition:** `V_R` versus `V_R/L_Z`. This connects Lambert’s wording with Antoja’s amplitude-flattened implementation.
3. **Leakage control:** mean-removed rectangular versus Hann-windowed signals, keeping support and sample count fixed.
4. **Peak estimator:** discrete maximum/Monte Carlo peak distribution versus Gaussian fits over predeclared intervals. Show dependence on the fitting interval and Fourier-bin resolution.
5. **Circular-velocity slope:** `n=0,-0.03,-0.06,-0.1`, rebuilding the transformed coordinate and spectrum each time. Treat Lambert’s printed `-0.5` separately pending author confirmation.

## 8. Claims the notebook must not make

- That it exactly reproduces Figure 10.
- That the public precursor notebook is the final author pipeline.
- That interpolation creates new independent information or improves intrinsic spectral resolution.
- That two spectral maxima prove two Sagittarius pericentric passages.
- That Sagittarius is the unique possible perturber or that the MRi interpretation is uniquely tidal.
- That the Monte Carlo band incorporates selection effects, binning choices, potential-model uncertainty, covariance, or preprocessing systematics.
- That Gaussian width is automatically a statistically calibrated `1\sigma` uncertainty on frequency.
- That agreement obtained after trying many preprocessing combinations is an independent validation.
- That the published `1.10\pm0.23` and `1.10\pm0.28` values are mutually consistent.
- That the printed `n=-0.5` can be silently replaced with `-0.05`.

## 9. Questions worth emailing Mika Lambert

1. Was the FFT block in `UCSC_DESI_MW` ancestral to Figure 10? If so, did the final analysis still treat the nonuniform `1/L_Z` samples as uniformly spaced using the first spacing?
2. What is the definitive Figure 9 construction: mean or median, 70 or 75 bins, exact range/bin coordinate, and standard error or bootstrap uncertainty?
3. Was the final transformed signal `V_R` or `V_R/L_Z`? Were mean removal, detrending, windowing, zero-padding, or smoothing applied?
4. What distribution and scale were used for the 1000 Monte Carlo draws; was the central spectrum a mean or median; how was “`1\sigma`” defined; and was a seed retained?
5. What were the two Gaussian fit intervals and fit model, and do the reported widths represent Gaussian `\sigma`, covariance errors on the centers, or another quantity? Also, should the sensitivity slope be `-0.5` or `-0.05`, and should the second timing uncertainty be `0.28` or `0.23` Gyr?

## 10. Codex-ready implementation brief

- **Inputs:** checksum-pinned Figure 9 and Figure 10 FITS files only.
- **Primary product:** an explicitly independent, uniformly sampled `1/L_Z` Fourier analysis with fixed seed, documented interpolation, window, normalization, and uncertainty summary.
- **Secondary product:** a visually separated forensic panel reproducing the released frequency-grid fingerprint and near-match to raw unnormalized `|{\rm FFT}(V_R)|^2`.
- **Timing:** calculate times from the published fitted frequencies, not from tuned notebook peaks.
- **Sensitivities:** the five experiments above, changing one scientific choice at a time.
- **Provenance labels:** “released data,” “forensic inference,” “independent analysis,” and “published timing conversion.”
- **Acceptance criteria:** no hidden preprocessing; no parameter tuning against Figure 10; all frequency axes derived from declared grid spacing; spectral resolution displayed; published inconsistencies visible in the narrative.
- **Toy model:** include only an impulsive quadrupolar velocity kick, differential winding at approximately `\Omega-\kappa/2`, correspondence of arm loci with negative mean `V_R` and near-zero residual `V_\phi`, ridges in `R`–`V_\phi`, and the resulting `L_Z`–`V_R` wave. Antoja establishes this qualitative chain while also warning that bars, self-gravity, overlapping perturbations, and non-power-law potentials complicate it. ([arxiv.org](https://arxiv.org/html/2206.03495v3?utm_source=chatgpt.com "Tidally induced spiral arm wraps encoded in phase space"))

A short toy model is therefore justified pedagogically, provided it is presented as a mechanism demonstrator—not a simulation or fit to the Lambert data.