# Structural feature-combination experiments — 2026-10-29

These experiments test why adding structural features lowered the original
formula-only selection classifier's balanced accuracy. The target remains
**curated selection membership**, not measured herbicidal activity or natural
origin. Implementation commits: `7ecf24f` (fixed comparisons), `01949a7` (nested C).
Production models, reviewed labels and source data were not changed.

## Design fixed before evaluation

All runs use the same **171 complete compounds: 55 selected herbicides and
116 selected natural products**, deduplicated by canonical structure. The five
outer scaffold assignments exactly match the earlier formula-model evaluation.
Invalid structures, unsupported formulas and unknown targets are excluded before
comparison. Every included predictor is finite; **zero values are imputed**.

The four original profiles are controls. Two ablations add descriptors or Morgan
fingerprints to formula. Three further profiles preserve formula outside PCA,
with different treatment of descriptors/fingerprints. All projected branches
remove training constants, standardize and retain 95% training variance with PCA.
Preserved features are standardized without PCA. Raw training constants can
remain as zero-valued columns. Logistic regression uses L2 regularization,
balanced class weights, a fixed 0.5 classification cutoff and the existing seed.

Fixed runs use C=1. Nested runs choose C separately for each outer training set
from **0.01, 0.1, 1, 10, 100** using three inner scaffold folds. Smaller C means
stronger regularization. Every inner transform is fitted on inner training data
only. Selection maximizes the unweighted mean inner-fold balanced accuracy;
ties within 1e-12 choose the smaller C. The selected model is refitted on the
outer training set before evaluating that fold's held-out compounds. There is
no global C selection from outer results, threshold tuning, seed search or
full-data exploratory refit in this experiment.

## Held-out results

The table reports **pooled outer out-of-fold balanced accuracy**. Inner-fold
scores determine C only and are not substituted for these evaluation scores.

| Feature/preprocessing profile | Fixed C=1 | Nested C selection |
|---|---:|---:|
| Formula, PCA | 91.91% | 92.77% |
| Descriptors, PCA | 72.42% | 73.33% |
| Morgan, PCA | 76.36% | 86.50% |
| Formula + descriptors, joint PCA | 92.82% | 91.91% |
| Formula + Morgan, joint PCA | 83.64% | 91.91% |
| Formula + descriptors + Morgan, joint PCA | 85.45% | 91.48% |
| Combined, formula preserved; descriptors + Morgan PCA | 84.11% | 92.39% |
| Combined, formula + descriptors preserved; Morgan PCA | 84.55% | 91.48% |
| Formula + Morgan, formula preserved; Morgan PCA | 83.64% | 91.48% |

The fixed formula + descriptor model gains 0.91 percentage points over fixed
formula alone: a net one additional selected herbicide detected, with the same
number of false positives. That small descriptive gain does not establish a
reliable ranking between the profiles. Inner tuning does not improve every
outer score; formula + descriptors decreases under the nested procedure.

## What the experiments say about the earlier gap

**Keeping formula outside PCA is not sufficient to recover formula-only
performance at C=1.** The preserved-formula profiles remain near 84% at that C,
compared with 91.91% for formula alone. Thus loss of formula information during
PCA is not an adequate sole explanation of the original performance difference.
Block preprocessing also changes effective weighting and dimensionality, so this
is not a direct measurement of how much biological signal PCA discarded.

**Regularization choice accounts for a substantial recovery in this dataset.**
The original combined pipeline improves from 85.45% to 91.48% when C is selected
inside training folds, with the feature blocks and PCA procedure otherwise
unchanged. Formula + Morgan improves from 83.64% to 91.91%. Every profile using
fingerprints selects C=100 in all five outer folds. This favors a weaker penalty
within the tested grid; it does not establish a globally optimal C beyond 100.
The grid was not expanded after viewing these results.

Formula-only nested performance is 92.77%, so a smaller gap remains. Both formula
and formula + descriptors remain competitive with the much larger fingerprint
representations. No profile is automatically installed as the new default.

## Ranking versus classification cutoff

The combined model already ranks the selected groups well at C=1, despite its
lower balanced accuracy. Its ROC-AUC changes only modestly with C selection.
The confusion counts make the change at the fixed 0.5 cutoff concrete:

| Model | ROC-AUC | Selected herbicides detected / 55 | Missed / 55 | Natural products called herbicide / 116 | Correctly called natural product / 116 |
|---|---:|---:|---:|---:|---:|
| Formula, C=1 | 0.9516 | 48 | 7 | 4 | 112 |
| Combined, C=1 | 0.9773 | 39 | 16 | 0 | 116 |
| Formula, nested C | 0.9585 | 48 | 7 | 2 | 114 |
| Combined, nested C | 0.9793 | 48 | 7 | 5 | 111 |

At C=1, combined predictions are conservative about calling the positive
selection class. Nested C changes the sensitivity/false-positive tradeoff at the
unchanged cutoff. No threshold was chosen from held-out outcomes and no
calibration claim is made. These errors are relative to the selection categories;
a natural product called herbicide could still be biologically herbicidal.

All fingerprint profiles already achieve 100% balanced accuracy on their outer
training partitions at both fixed and selected C. The improvement cannot be
explained simply as correcting training classification errors. Regularization
changes coefficients, margins and held-out decisions even when training labels
are already separated. Fingerprint PCA retains up to 104 components here,
versus at most nine for formula alone; preserved-block models have up to 131 or
142 classifier inputs. The small-sample dimensionality concern therefore remains.

## C selected inside each outer training partition

Columns are outer fold IDs 0–4; these are training-selected values, not selections
made by comparing the held-out metrics above.

| Profile | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 |
|---|---:|---:|---:|---:|---:|
| Formula | 0.1 | 0.1 | 0.1 | 0.1 | 0.01 |
| Descriptors | 0.1 | 0.1 | 10 | 1 | 100 |
| Formula + descriptors | 0.1 | 1 | 0.1 | 0.01 | 0.1 |
| All six fingerprint-containing profiles | 100 | 100 | 100 | 100 | 100 |

`inner_scores.csv` retains all 675 C/inner-fold candidate scores, not only the
winning scores. `folds.csv` also records training/test sizes, selected C, inner
mean score, PCA dimensions and outer training/test balanced accuracy.

## Reproduce and inspect

From the repository root, using fresh output directories:

```bash
analysis/.venv/bin/python analysis/ablations.py --features analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet --output analysis/outputs/ablations-fixed-2026-10-29-final
analysis/.venv/bin/python analysis/ablations.py --features analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet --output analysis/outputs/ablations-nested-2026-10-29-final --tune
```

Each directory contains:

- `ablation_models.csv`: nine held-out metric reports, including confusion counts.
- `out_of_fold.csv`: 1,539 per-compound/profile predictions with original fold IDs.
- `folds.csv`: 45 outer fold records and dimension/training diagnostics.
- `cohort.csv`: the same 171 exact compound identities, scaffolds and labels.
- `inner_scores.csv`: 675 nested search rows, or a header only for fixed-C runs.
- `manifest.json`: exact inputs, code, locks, versions, profile columns, settings
  and output hashes. Generated results stay ignored/local.

Source implementation: [ablations.py](../ablations.py). Focused tests:
[test_ablations.py](../tests/test_ablations.py). Public contract and policy:
[README](../README.md), [decisions](decisions.md).

## Verification and limits

- The four original fixed-C baseline metrics reproduce the earlier common-cohort
  checkpoint; unit tests also compare their held-out probabilities/fold IDs.
- All 18 profile/mode comparisons have 171 unique out-of-fold predictions each;
  cohort identities, class counts and outer assignments match across runs and
  match the original formula evaluation. Scaffolds never cross outer folds.
- Every selected C/mean score was independently recomputed from the saved inner
  history and matches `folds.csv`. All input/code/lock/output hashes verify.
- Focused checks: 26 passed. Analysis suite: 143 passed. Pipeline suite: 1,043
  passed. Both Ruff checks and `git diff --check` are clean. Tests trace actual
  preprocessing fits to verify inner/outer training-only behavior and retain
  explicit failures rather than switching split policies.

These are exploratory comparisons on one purposive selection and one outer
partitioning seed. Nested C selection does not protect a subsequent choice of
profile based on the same outer results. No significance interval, independent
external confirmation, prospective performance or herbicidal-activity validation
is established. The results narrow the explanation of the selection-model gap;
they do not replace the need for reviewed activity labels and broader independent
chemistry. Production models, raw source data and label worksheets remain unchanged.
