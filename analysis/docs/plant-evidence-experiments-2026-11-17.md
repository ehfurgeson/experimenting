# Plant evidence feasibility and experiments — 17 November 2026

**Complete-study recovery is the strongest immediate direction.** This pass adds
87 numerical ChEMBL responses, recovers 90 responses from a complete primary
coumarin series and five exact numerical Cuscuta responses, and tests context,
continuous-response and candidate-selection approaches. Model improvements remain
uncertain; none is promoted as a general plant-inhibition model.

Work was performed locally on `research/data-first-sprint-2026-11-17`, preserving
the existing uncommitted changes and prior adopted/frozen bundles. These are new
AI experimental evidence products, not new human-adopted labels or laboratory data.

## Brief feasibility assessment

| Direction | Actual probe | Decision |
| --- | --- | --- |
| Complete publication/assay recovery | Eight full ChEMBL publication series; 871 native records | **Pursued.** Adds 87 interpretable numerical responses / 15 structures absent from the old quantitative pool. |
| Primary-paper recovery | Kava, coumarin and Cuscuta PDFs; open coumarin XML | **Pursued.** Tables and methods support value checks, 90 new coumarin responses and five exact Cuscuta measurements. |
| PubChem screening inventory | 31 search matches, 30 descriptions downloaded | Useful discovery route; the returned descriptions link to ChEMBL and include enzymes/cytotoxicity. No independent new study or inactive label inferred from those links. |
| Narrow assay-specific modeling | Four continuous species/endpoint panels, two chemical holdout protocols | **Pursued.** Small and inconsistent improvements; more coherent data are still needed. |
| Shared context/study-offset models | Four fixed logistic profiles under publication and chemical holdouts | **Pursued.** Context helps within familiar studies but does not improve new-publication transfer. |
| Dose-response reconstruction | 126 complete compound/species/endpoint curves; interior-dose holdouts | **Pursued.** Useful descriptive curves; monotone fits do not outperform a median interpolation baseline here. |
| Model-guided experimental selection | 24-entry algorithm from a 224-compound evidence-filtered pool | **Diagnostic only.** Natural-origin and model applicability problems persist. This is an evidence-review queue, not a purchase or assay list. |
| New physical assays | Prepared an assay-design document | No laboratory session or materials were available through the workspace. No compounds purchased, outside contacts messaged or physical assays performed. |
| Large pretrained/protein models | Assessed against observed transfer and evidence support | Deferred. They do not supply missing measured plant outcomes; simple representation pilots already exist, and this pass prioritizes evidence and protected validation. |

## 1. New evidence and source yield

Full publication downloads preserve all source activities, including missing values
and nonplant endpoints. A record enters the experimental response table only with
an eligible plant organism, explicit numerical percent inhibition, exact qualifier,
single scalar exposure, usable structure and no provider validity hold. Generic
“Activity”, absent outcomes, dose ranges and uncontrolled response bases remain in
the audit. Source status/version, URLs, timestamps and hashes are retained.

| Publication | Native records | Numerical responses used |
| --- | ---: | ---: |
| Withanolides, DOI 10.1021/np070030g | 40 | 0; elongation response basis needs reconciliation |
| Brevicompanine, DOI 10.1021/np040178p | 16 | 1; other scales/missing values held |
| Rhodanines, DOI 10.1271/bbb.60.1368 | 306 | 0; 302 nonplant records, four plant lengths without compatible controls |
| Quinones/resorcinolic derivatives, DOI 10.1021/jf100108c | 34 | 0; numerical plant responses absent |
| Kaurane amides, DOI 10.1021/jf0729309 | 87 | 0; numerical responses absent |
| Kava lactones, DOI 10.1021/jf0519461 | 120 | 65 |
| Pyrazinecarboxylic derivatives, DOI 10.1584/jpestics.17.4_261 | 140 | 21 |
| Bismuthines, DOI 10.1021/jf025927s | 128 | 0; ambiguous scales, controls or unsupported structures |

The 87 responses cover **15 new structures relative to the previous quantitative
pool**. They contain 77 high responses, one low response and nine intermediates
under the existing ≥40%/≤20% bands. Acquisition therefore adds positive examples
more readily than comparable negative examples. The expanded quantitative working
table has 740 rows; the binary experiment uses 731 rows / 146 structures.
This differs from the older 733-row v3 pool, which also contains categorical policies.

The [Kava primary study](https://doi.org/10.1021/jf0519461) was recovered as a PDF.
Table 3 and methods were checked visually: six pure lactones, lettuce/barnyardgrass,
1/10 ppm and germination/shoot/root endpoints. All 65 ChEMBL numerical values
were independently checked against that table. Its dashes mean untested; mixtures,
crude extracts and fungal responses are separate. These checks corroborate the same
study and add **zero extra independent observations** beyond the 65 already counted.
The paper's plant activity does not establish human safety.

The [eugenol-derived coumarin study](https://doi.org/10.3390/plants9040533) yields
**90 dose-specific responses**: six source compounds × five nonzero doses × three
table endpoints. Source control values, raw cells, mean ratios, vehicle and methods
are preserved. Under the retrospective bands these are 63 low, nine high and 18
intermediate responses. The six compounds are synthesized derivatives; they are
**not adopted as natural-occurrence examples**, and their A1–A6 structure mappings
remain unresolved. Tables 1–3 on PDF pages 3/5 were visually checked against XML.
Root/shoot figure values were not reconstructed as exact data.

The previously inaccessible [Cuscuta study](https://doi.org/10.3390/agriculture12101746)
was recovered from the author institution. Page 5 gives exact numerical text for
2-benzoxazolinone, hydrocinnamic acid, pisatin, umbelliferone and 1,4-benzoquinone:
89.2, 88.5, 81.6, 48.7 and 47.3% growth inhibition at 1 mM after five days.
Reported SEM, three replicate dishes and source locators are retained in
`analysis/resources/cuscuta_primary_review_2026-11-17.csv`. No values were guessed
from bar heights; the other compounds' qualitative descriptions do not become
numeric inactive labels. Exact sample mappings remain pending.

These five Cuscuta observations and the 90 coumarin observations remain separate
primary evidence; they are not silently pooled into the classifiers. In particular,
the source-named plant-active compounds should not be assumed to have favorable
acute toxicity merely because they inhibit plant growth.

## 2. Context-aware classification

Four fixed logistic profiles use fold-local imputation, scaling and category
encoding. Numeric exposure features keep molar concentration, mass/area, soil dose
and reported ppm in separate axes; unknown months and ambiguous units are not
given invented precise conversions. Molecular weight converts explicit aqueous
mass concentrations to molarity. Study indicators are regularized offsets, **not
a fitted Bayesian hierarchical model**. Unknown test species/studies are handled
without fitting their encodings on test data.

| Profile | Publication holdout macro-F1 | Chemical-group holdout macro-F1 |
| --- | ---: | ---: |
| Chemistry only | **0.5865** | 0.6117 |
| Context only | 0.5263 | **0.7279** |
| Chemistry + context | 0.5193 | 0.6573 |
| Chemistry + context + study offsets | 0.5523 | 0.7059 |

Chemical holdout permits study overlap; publication holdout permits chemical
overlap. The context-only chemical result is a warning that assay selection and
conditions explain substantial label variation. It is not evidence that a model
can discover new active chemistry. All six conditional paired intervals against
the chemistry baseline include zero. For example, the context-only chemical gain
is +0.1161, interval −0.0493 to +0.3212; its publication difference is −0.0603,
interval −0.2519 to +0.1898. Intervals use 2,000 fixed-prediction cluster bootstrap
draws, without retraining or multiplicity correction.

These metrics are `experiments-v3`, rebuilt on `plant-v5` quantitative labels.
`experiments-v2` used `plant-v3`, which still scored CL-20 `ECOTOX:2063905` as
high. That comment documents a significant increase, so `plant-v5` keeps it low.
The row count is unchanged: one label moved. Do not interpret the difference
from the previous 0.6706/0.6553 logistic scores, or from the `experiments-v2`
table, as a matched feature change. The run exports per-class diagnostics, all
predictions, holdout support,
paired intervals and feature weights for every fit. Numeric transformed columns
map to `NUMERIC` in the source; one-hot coefficients retain category names.

## 3. Continuous and assay-specific models

All 324 flavonoid study measurements, including intermediate effects, were used
in four independent species/endpoint panels: radish/cress × germination/root length.
Each has 27 structures, three doses and a 120-hour endpoint. Fixed median, dose-only
ridge, chemistry-plus-dose ridge and forest profiles were evaluated with every
dose of a held-out structure together, followed by stricter scaffold/connectivity
holdouts. There is no row-random train/test leakage across doses of a compound.

| Root-length panel | Full-structure holdout median / forest MAE | Scaffold/connectivity holdout median / forest MAE |
| --- | ---: | ---: |
| Radish | 18.95 / 19.59 percentage points | 19.36 / 19.18 |
| Cress | 25.07 / 21.86 | 25.34 / 24.36 |

The cress forest has a modest point improvement, but the conditional difference
interval includes zero: −3.21 points (−8.63 to +2.31) under full-structure holdout,
and −0.98 (−3.25 to +5.45) under chemical groups. No new-study transfer is tested.
Germination has **zero high-response examples** under these bands; a high/low
classifier is unsupported there even though continuous response prediction can be
evaluated. Root panels have only eight/five high-response observations, not eight/
five independent active compounds. MAE is primary; thresholded F1 and support are
secondary diagnostics. No predictions are clipped to hide implausible extrapolation.

The dose-curve experiment separately reconstructs **126 curves**: 108 flavonoid
compound/species/endpoint series and 18 coumarin series. It uses monotone isotonic
fits and log-dose interpolation, without forcing a four-parameter curve through
three observations. Held-out interior-dose MAE is 11.71 points for all three
flavonoid interpolation profiles. For coumarins it is 9.95 for median, 12.21 for
linear log-dose and 11.58 for isotonic interpolation. Monotonicity therefore adds
no demonstrated predictive benefit here. Forty-seven series have downward steps
over ten points; hormesis, noise and assay context cannot be distinguished from
reported means alone. Eight series cross 50% in the monotone fit; the others do
not reach it in range. These are descriptive crossings/conditional range bounds,
**not newly measured EC50s**, uncertainty intervals or validated potency estimates.

## 4. Experimental selection and the origin bottleneck

A prototype selected 24 entries from 224 candidates with accepted exact high-class
toxicity, no explicit toxicity-context assumptions, a LOTUS link and no current
plant label, excluding the original herbicide selection. Eight entries probe
higher model scores, eight model disagreements and eight chemical-space diversity.
All scores are exploratory full fits for a proposed lettuce/root/100µM/120h context.

**The resulting queue is not ready for laboratory use.** It includes entries such
as ofloxacin and dipyridamole that cannot be treated as natural bioherbicide
candidates from these joins. Extreme scores also occur outside well-supported
plant-training chemistry. This stress test shows that occurrence-link filters,
acute LD50 and model disagreement alone are insufficient selection criteria.
`validation-queue-v1/validation_queue.csv` is retained as an evidence-review
diagnostic, with exact structures, toxicity provenance, occurrence DOIs, similarity
and explicit pre-assay holds. Disagreement is not calibrated uncertainty, and no
prospective active-learning gain was measured.

The accompanying assay-design document proposes a smaller 8–12-compound first
round **after** origin, exact-form, chronic/non-target hazard, solubility and
availability review. It calls for range-finding, dose-response follow-up,
solvent controls, randomized positions and independent dishes/runs. It is a planning
artifact rather than an approved protocol or claim of OECD compliance.

## What should be pursued next

1. Extend complete primary-table recovery, prioritizing comparable low-response
   natural compounds. The synthetic coumarins supply useful response contrasts but
   do not fill the natural-origin negative class.
2. Resolve exact structures and sample forms for the recovered primary sources;
   audit the strongest Cuscuta leads against measured toxicity and occurrence.
3. Build a coherent root-growth benchmark before more general modeling. Keep
   species, dose, duration, vehicle and control basis explicit; retain intermediates
   and stimulation. Request replicate data only through user-authorized outreach.
4. Gate experimental selection on primary biosynthetic-occurrence evidence and
   broader hazard review. Re-run diversity/disagreement selection only on that
   reviewed pool. Keep a separate assay-control set and prospectively test whether
   model guidance improves hit discovery.

## Artifacts, reproduction and checks

Run root: `experiments/plant-evidence-2026-11-17/`. Canonical bundles are
`sources-v1/`, `extra-sources-v1/`, `experiments-v3/`, `assay-regression-v1/`,
`validation-queue-v2/` and `report-v4/`. `experiments-v2/` and `report-v3/`
remain the plant-v3 label fit. Assay regression reads the flavonoid series only
and was not refit.
Large raw sources and generated products stay ignored/local; tracked scripts and
this report preserve workflow and findings. Rhodanine primary HTML returned 500;
its failed body/status is retained, and no missing primary table was manufactured.

Run from the repository root, choosing fresh output paths:

```bash
analysis/.venv/bin/python analysis/plant_evidence_acquire.py --output NEW_RUN/sources-v1
analysis/.venv/bin/python analysis/plant_evidence_extra_sources.py \
  --sources NEW_RUN/sources-v1 --output NEW_RUN/extra-sources-v1
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 uv run --project analysis --locked python analysis/plant_evidence_experiments.py \
  --sources NEW_RUN/sources-v1 \
  --accepted experiments/data_acquisition/2026-11-17-accepted-experiments \
  --flavonoids experiments/compatible-assays-2026-11-12 --output NEW_RUN/experiments-v3
uv run --project analysis --locked python analysis/plant_assay_regression.py \
  --flavonoids experiments/compatible-assays-2026-11-12 --output NEW_RUN/assay-regression-v1
uv run --project analysis --locked python analysis/plant_validation_queue.py \
  --experiments NEW_RUN/experiments-v3 \
  --prior experiments/data_acquisition/2026-11-17-review-followup/pilot-v2 \
  --output NEW_RUN/validation-queue-v2
```

The first two commands require network access. Acquisition records the current
ChEMBL version rather than silently claiming it equals an older release. The
dated report verifier expects canonical directory names above; its CLI is
`analysis/plant_evidence_report.py --root RUN_ROOT --output FRESH_REPORT_PATH`.
Primary PDF text extraction used bundled Poppler; selected pages were rendered
and visually inspected. XML/table cells and printed source methods remain authoritative.

Independent verification preserves all 653 prior quantitative rows field-for-field,
checks 65 Kava source cells and 90 coumarin cells/ratios, recomputes eight context
F1 scores and 32 assay MAEs, checks 40 assay fold partitions and validates 29
experiment/regression/queue product hashes. It also hashes the recovered PDFs,
checks queue uniqueness and preserves the five source-located Cuscuta observations.
All **390 analysis tests** pass. Tests cover scalar/ranged exposures, unit conversion, unknown response scales,
incomplete series, unseen contexts and held-out dose interpolation. Full test and
lint results are recorded with the final delivery. These checks do not replace
independent biological or sample-identity validation.
