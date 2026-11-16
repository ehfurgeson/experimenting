# Actual imputation audit — 2026-10-29

Diagnostic reruns only; no tracked model code, labels or source data changed.
The target is curated selection membership, not measured herbicidal activity.
Source: structural_features.parquet from structure-2026-10-28-stress-baseline,
plus analysis/data/compound_traits.parquet for the older notebook group model.
Machine-readable counts, reports, folds, inputs/code hashes: audit.json.
Reproduction script: notes/audit_model_imputation.py (choose a fresh OUT path).

## How the current model imputes

SimpleImputer(strategy='median', keep_empty_features=True) precedes variance
filtering, scaling, PCA and logistic regression. Within each fold, each feature's
replacement median is estimated from that fold's training compounds only and
then applied to missing values in training/held-out rows. Nonfinite numeric
predictors are treated as missing. This is per-feature statistical filling, not
reconstruction of an experimentally known value or a chemically valid formula.
Unknown target labels and invalid structures are excluded, not imputed.

## Distinct missing predictor cells in each eligible selection cohort

| Representation | Compounds | Features | Predictor cells | Missing cells | Affected compounds |
|---|---:|---:|---:|---:|---:|
| Formula | 171 | 27 | 4,617 | 0 | 0 |
| Descriptors | 174 | 11 | 1,914 | 0 | 0 |
| Morgan | 174 | 2,048 | 356,352 | 0 | 0 |
| Combined | 174 | 2,086 | 362,964 | 81 | 3 |

The 81 cells are all 27 formula features for paraquat (PUBCHEM:15939), diquat
(PUBCHEM:6795), and difenzoquat (PUBCHEM:39425). Their charged formulas are outside
the flat neutral formula parser, while descriptors/fingerprints remain valid.
All three are selected herbicides. That is 1.72% of compounds/formula-block cells,
but only 0.0223% of the full combined matrix, which includes 2,048 fingerprint
bits per compound. The full-matrix percentage alone understates the concentration
of missingness in these compounds. Two multicomponent compounds are excluded
from structural models before any imputation.

Counts refer to distinct input cells. Cross-validation reuses the same compounds
in training: 324 training-cell and 81 held-out-cell replacements occur across all
five combined-model folds (405 placements total), plus 81 in the separate
full-sample exploratory refit. These are repeated uses of the same 81 missing
input cells, not 486 independent missing observations. Other representations
have zero replacements in every fold and the full-sample fit.

## Controlled removal of the imputer

The common 171-compound cohort has no missing values for any representation.
Replacing the imputation step with passthrough and refitting every fold with the
same rows, folds, settings and seed produces exactly identical out-of-fold
probabilities and reports for all four representations:

| Representation | With imputer, balanced accuracy | Without imputer, balanced accuracy |
|---|---:|---:|
| Formula | 91.9122% | 91.9122% |
| Descriptors | 72.4216% | 72.4216% |
| Morgan | 76.3636% | 76.3636% |
| Combined | 85.4545% | 85.4545% |

On their larger complete eligible cohorts, descriptors (174) and Morgan (174)
also give identical held-out probabilities when the imputer is removed:
72.8448% and 80.1724% balanced accuracy respectively. Formula remains 91.9122%.

For the 174-compound combined model, removing the imputer without removing
missing inputs causes PCA to reject NaNs. Excluding the three incomplete rows
allows evaluation: 85.4545% balanced accuracy on 171, versus 85.3448% on 174 with
imputation. This is not a causal measure of imputation benefit/harm because
class composition and fold allocation change with the cohort. On the same 171
rows, the imputation step itself has exactly zero numerical effect.

## Older notebook group classifier

The old PubChem-descriptor group model has 2 missing XLogP values out of 1,760
predictor cells (176 compounds x 10 features). The affected compounds are
Glufosinate-ammonium and MSMA, both outside the eligible structural-model cohort.
No other predictors in that older group model are missing.

- Original fold-local median imputation: 76.7045% accuracy on all 176 compounds.
- Removing XLogP entirely (no missing predictors), same 176 compounds and original
  fold algorithm/seed: 77.2727% accuracy. This is a feature ablation, not a pure
  imputation intervention.
- Dropping incomplete rows and rebuilding folds: 78.1609% accuracy on 174; changed
  rows/folds prevent direct attribution of the difference to imputation.
- Keeping original folds and the same 174 complete held-out compounds: original
  imputed training gives 77.0115%, while omitting incomplete training rows gives
  76.4368%. Three held-out class predictions change. This comparison preserves
  test rows/folds but changes training composition; it is not an isolated imputer
  effect either. No statistical performance advantage is established.

These results audit the older group target only; evidence-availability targets
use target-specific labeled subsets. They must not be interpreted as activity
model validation or improvements proven from a difference of one/few cases.
