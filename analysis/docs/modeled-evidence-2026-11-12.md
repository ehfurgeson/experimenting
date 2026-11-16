# Separate modeled-evidence checkpoint — 12 November 2026

**AI experimental, provisional scientific interpretation.** This first collection
pass expands source coverage and evaluates A/B separately under the
[predeclared protocol](modeled-evidence.md). It does not adopt human labels,
change historical rat admissions, validate a plant-activity model or establish
safer candidates. Combined pathway C is **deferred**.

## Collection and separate releases

Public source snapshots are local under
`experiments/external-evidence-2026-11-12-run1/sources/`. The source registry and
HTTP log distinguish downloads, documentation and unresolved routes. No credentials
are included. Scientific files remain ignored and local.

| Product | Actual result and qualification |
|---|---|
| NIH ICE lowercase `acute_oral.xlsx` | 16,721 In Vivo rows; workbook metadata ICE 4.1, created 2024-07-29. Retains all mixtures, classifications, missing references and inequalities. Not the same export as the older uppercase workbook. |
| A exact cohort | 5,921 eligible exact observations summarized into 4,234 full structures; 47 eligible censored observations remain separate; 10,753 excluded rows retained. 4,188 cohort structures lie beyond the original selection. |
| OPERA `OPERA_Data.zip` | Pinned repository commit `01b07c769dd86eadb71843e057783a64a364c885`; 36 archived members, including 50,660 CATMoS source records. Source package version is not inferred from the current executable release. |
| B CATMoS primary cohort | 50,330 source rows pass value/domain/structure checks; 330 excluded. Collapse duplicate structures; exclude 2,985 conflicting full-key groups. Final primary cohort: 43,128 structures, 43,064 beyond the original selection. |
| CATMoS domains | 50,581 source Inside / 79 unknown; no source Outside records in this file. Finite output and Inside remain separate checks. |
| Original CTX cache | 2,176 TEST5.1.3 rows / 136 compounds; also retain 3,752 OPERA2.8 and 2,078 Percepta calculated-property records as distinct model/version inventories. Cached acquisition: 21 October 2026. |
| Dietary TEST batch | All 40 locally resolved dietary structures attempted; 38 returned stored TEST5.1.3 output / 608 rows, including 36 finite rat outputs. Xylitol and erythritol remain identity-review cases. No other identity or Li hold is overridden. |
| Union TEST coverage | 173 unique full structures, adding 37; 2,784 retrieved/cache rows collapse to 2,768 structure/model/endpoint rows. Repeat retrieval is not a new model vote. No new-structure TEST inference was run. |
| Author dataset DOI 10.5281/zenodo.3300664 | 13,680 aggregation rows retained for review. Its pLD50 scale and TESTEPA/NICEATM/Toolbox lineage require qualification before normalization or experimental admission. |
| VEGA / GenRA / OECD Toolbox | Official documentation/download routes archived. No batch inference or read-across result was acquired from these platforms. Their catalog pages add zero prediction records. |

Sources: [NIH bulk index](https://ice.ntp.niehs.nih.gov/downloads/DataonICE/),
[OPERA source repository](https://github.com/kmansouri/OPERA),
[author collection](https://zenodo.org/records/3300664),
[EPA TEST](https://www.epa.gov/comptox-tools/toxicity-estimation-software-tool-test).
The raw versions, exact source-cell/native-record locators and SHA256s are in the
local releases. Original experiment identifiers, tested material, exposure context,
purity and study independence remain incompletely audited. Source references are
not counted as independent publications. Diet/inventory membership is not
verified natural origin or tested plant inactivity.

A excludes non-LD50 classifications, mixtures, incompatible/missing context,
nonpositive/nonfinite doses, reference gaps, unresolved structures and multicomponent
forms. Repeated same-chemical/sex/reference/value reports collapse before medians;
this does not resolve every mirrored study. B uses `CATMoS_LD50_pred` on documented
log10(mg/kg), not the separate consortium consensus or experimental-comparator
field. Outside/unknown and rejected rows remain recoverable. Provider full-key
mismatches are excluded. The archive-scale interpretation is provisional and specific to this pinned
SDF. The provider README identifies the CATMoS log(mg/kg) model. A separately
archived `OPERA.m` reads internal predictions at line 8442 and exponentiates them
at lines 8631–8634 for current executable output. **Fresh OPERA CLI exports under
the same column name can therefore be on a different scale.** The local
`model-documentation-v1/normalization_audit.csv` retains this distinction; do not
reuse the archive parser for current executable CSVs without qualification.
No molar/mass conversion is applied to TEST cache values;
API-specific transform and chemical-form semantics still need qualification.

## Separate fixed model evaluation

Five GroupKFold outer folds keep connectivity and scaffold groups together. All
A/B train and test folds support all three fixed LD50 bins. There are 1,097 A and
7,606 B merged groups. Two large scaffold groups each occupy a single test fold;
the remaining groups spread over the other three folds. Actual counts/membership
are retained, so five folds should not be mistaken for five equally diverse tests.

Seven RDKit descriptors are structure-derived, not measured features. The
both-X-and-y experimental subset, original-publication/provider holdouts,
calibration and prediction intervals are unsupported in this release. No tuning
or favorable-profile selection occurred. No experimental-only input claim is made.
The historical 1,080/3,400 mg/kg cutoffs are cohort bins, not regulatory categories.
Lower LD50 means greater acute hazard.

| Pathway | Profile | Pooled held-out MAE, log10 dose | Pooled held-out macro-F1 |
|---|---|---:|---:|
| A measured, n=4,234 | Training-median / majority baselines | 0.650 | 0.226 |
| A measured | Ridge / logistic | 0.648 | 0.382 |
| A measured | Forest | 0.636 | 0.430 |
| B CATMoS estimates, n=43,128 | Training-median / majority baselines | 0.404 | 0.200 |
| B CATMoS estimates | Ridge / logistic | 0.371 | 0.465 |
| B CATMoS estimates | Forest | 0.301 | 0.616 |

B metrics measure teacher reproduction, not agreement with experiments. A forest
MAE improves little over its training-median baseline; these results do not
establish a general toxicity predictor. The complete per-fold metrics, regression
bias/RMSE/rank, per-class precision/recall/F1/AUROC, confusion counts, actual split
membership and held-out predictions remain in the model bundle.

Standardized logistic weights are retained by class/fold and do not identify
causes. The separate binary low-LD50-versus-rest whole-cohort forest has OOB F1
0.677 A / 0.772 B; this is not scaffold-held-out performance. Tree-specific
three-repeat OOB permutation drops and repeat SD are stability diagnostics, not
p-values or statistical significance. OOB importance for A is diffuse; its largest
mean drops are rotatable bonds (0.033), molecular weight (0.031) and fraction sp3
(0.030). B's largest drops are TPSA (0.110) and rotatable bonds (0.101).

## Agreement and decision for C

There are 3,361 exact full-key rat/oral/LD50 pairs. Log-dose MAE is 0.250,
Spearman correlation 0.917 and fixed-bin agreement 76.9%. However, **3,359 pairs
carry the teacher's training-compound tag**; one has a test tag and one is unknown.
The archive's training tags and chemical similarity do not identify an independent
original experimental study or prove exclusion from a later teacher version.
This is agreement dominated by known chemical overlap, not independent validation.

The exact-key paired subset contains only 14 selected herbicides and 10 selected
natural products; the other 3,337 have no inferred biological group. Broader
source-first coverage does not solve the selection/classification problem. For
example, A includes 28 selected herbicides and 18 selected natural products,
while B includes 29 and 35, respectively. Group descriptions retain separate
membership, class counts and log-dose distributions; no activity/safety labels
are inferred from source membership.

**Defer C.** There is no established untouched experimental cohort with qualified
teacher-training and original-study independence. Combining these labels now
would obscure shared lineage. A future design may add a teacher feature to an
A-only comparison on the same untouched experiments, after study/form audits,
without concatenating labels or changing the existing test set to favor C.

## Reproduction and remaining source work

Canonical local bundles:

- `analysis/outputs/separate-evidence-2026-11-12-v2/`: frozen A/B inputs,
  original TEST/property audit, identities, exclusions, lineage, source log and
  code/protocol/lock snapshots.
- `experiments/external-evidence-2026-11-12-run1/dietary-test-v1/`: independent
  exact-identity acquisition, 38 successful stored-output chemicals, two review
  cases, raw cache and executed code snapshots.
- `analysis/outputs/separate-evidence-models-2026-11-12-v3/`: separate model
  evaluation, offline `walkthrough.html`, figures, weights/OOB and C decision.
- `analysis/outputs/separate-evidence-comparison-2026-11-12-v3/`: TEST union,
  duplicate/mirror audit, exact cohort memberships, group descriptions and paired
  teacher-lineage/similarity ledger.

Earlier release v1, model v1/v2 and comparison v1/v2 outputs are retained as preliminary. Their exact code
and the original acquisition-log prefix are preserved locally; the recovered log
prefix matches its historical SHA256. Canonical v2 freezes retain code snapshots
within the bundle. New code must never rewrite the old manifest to match itself.

Commands and fixed settings are in the [workflow contract](modeled-evidence.md).
The comparison's `summary.json` owns the next-source backlog: resolve the remaining
160 dietary names; review the two EPA ambiguities; qualify TEST/VEGA/GenRA/Toolbox
execution and TEST API units; audit ICE/teacher original studies and tested forms;
review the held Zenodo scale; transcribe the recovered Kühn Daphnia series and
preserve the benzoic-acid access failure; expand documented natural-product
inventories. No fit-for-purpose external plant-activity model has been qualified.
This first pass does not claim every accessible source has been exhausted.


## Verification

The prescribed locked, offline suites pass: 1,078 pipeline tests, 324 analysis
tests, and Ruff over both components. Earlier no-sync checks were needed while
pre-existing dependency edits were unresolved; the final standard commands pass.
Dependency edits remain outside this research task's commits. Installed package
versions and frozen lock/code copies are retained for the actual model run.

The independent local verifier checks 233 product hashes and recoverable executed
code snapshots, all 16,721 NIH rows against an independent workbook reader (zero
cell differences), eight SDF records through RDKit, all 4,234 medians, exclusion
of all 2,985 conflicting B structures, ten actual outer folds for both connectivity
and scaffold leakage, and all twelve pooled metric profiles by plain arithmetic.
Credential equality checks found no credential in local text products. It writes
`experiments/external-evidence-2026-11-12-run1/verification.json`; the exact verifier
is preserved beside it. Scientific plots were rendered and visually inspected;
residuals use separate panels/scales so cohort-size differences remain readable.
These checks verify computation and provenance, not human scientific review or
independent biological validity.

## Same-target OOB exploration and local notebook

The follow-up `separate-evidence-multiclass-oob-2026-11-12-v1/` bundle fits two
additional full-cohort diagnostic forests on the same three LD50 classes and fixed
profile as the primary held-out classifiers. It retains ten per-feature OOB
permutation repeats, probabilities/vote counts and exact source/code hashes.
Whole-cohort OOB macro-F1 is **0.484 A / 0.729 B**; the original scaffold-held-out
forest macro-F1 remains **0.430 / 0.616**. These are different evaluation regimes,
not improvements in the held-out models or independent validation of B.

For three-class A, the largest mean OOB macro-F1 drops are TPSA 0.0310
(repeat SD 0.0042), fraction sp3 0.0260 (0.0056), and rotatable bonds 0.0184
(0.0033). For B they are TPSA 0.1600 (0.0008), rotatable bonds 0.1107
(0.0010), and molecular weight 0.0801 (0.0011). The original binary OOB results
above remain preserved. Neither set supplies a p-value: repeat SD measures
permutation stability, and correlated features can share importance.

The gitignored local `notes/notebooks/evidence_experiments.py` explores saved
model results with native Markdown cells, visible calculation cells, A/B and
class controls, F1-first scores, standardized logistic coefficient means/fold SDs,
and same-target forest OOB importance. It also retains assay-policy counts,
pooled-activity coefficients/fingerprint importance, failed new-paper transfer,
and the two binding cases. It does not refit on UI changes or recast unknown
activity as inactivity. `notes/notebooks/evidence_experiments.html` is a static
reading copy; use live marimo for Python-backed controls.

The notebook's full-key biological join gives A: **1 reviewed K1998-active
natural, 0 reviewed K1998-low-response naturals, 5 natural activity-unknown,
28 herbicide comparators and 4,200 other/unclassified**. B has **3, 0, 4, 29
and 43,092**, respectively. These provisional exact-key cohort intersections are
separate from the earlier selection-group counts and do not infer new labels.
