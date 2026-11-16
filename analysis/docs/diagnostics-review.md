# Stress, ablations and frozen assay review

[Component quickstart](../README.md) · [Repository documentation](../../docs/README.md)

Commands below run from the repository root. Real-data examples require the local inputs described in the [data guide](../../docs/data.md).

## Structural stress diagnostics

### Publication transfer

Use `publication_transfer.py` to test source transfer on prepared features and an
explicit compound/publication crosswalk, in a fresh output directory:

```bash
uv run --project analysis --locked python analysis/publication_transfer.py \
  --features YOUR_RUN/structural_features.parquet \
  --lineage YOUR_WORK/lineage.csv --target activity_target \
  --output analysis/outputs/NEW_PUBLICATION_TRANSFER
```

The lineage CSV needs `compound_id,publication`; extra provenance columns are
ignored. A compound can belong to several publications, but repeated identical
pairs, unknown IDs, mixed known activity policies and missing lineage for any
labeled row fail. Canonical aliases
share the union of their publications before splitting, so an alias cannot leak
the held publication into training. Formula eligibility and deterministic
canonical representatives match the existing diagnostics.

Every publication is held out in two predefined scenarios: `publication_only`
and `publication_and_scaffold`, which also removes every training structure
whose Murcko scaffold appears in that test set. `membership.csv` exposes actual
partitions; `reports.csv` includes shared-scaffold and purge counts, class counts,
F1/precision/recall, balanced accuracy, AUROC, confusion counts and a training-
majority baseline. `predictions.csv` contains held-out probabilities. A split
missing either class in training or testing returns an explicit status, null
metrics and no fit. The three fixed profiles are standardized raw-formula
logistic, unscaled raw Morgan logistic and raw Morgan forest, with the settings
from `professor_followup.py`; threshold is 0.5 and no tuning occurs.

This diagnostic does not replace the five-fold support gate or certify assay
compatibility, identities or scientific approval. Very small publication tests
remain very small. When structures have multiple sources, publication test sets
can overlap: do not combine their predictions as independent out-of-fold rows.
Heterogeneous assay labels require a separate explicitly experimental policy;
the command does not authorize pooling existing reviewed policies. The manifest
hashes inputs, code, locks and products and records dependency versions.

Focused checks: `uv run --project analysis --locked pytest
analysis/tests/test_publication_transfer.py -q`.

### Scaffold and shuffled-label checks

`stress.stress(rows, target = "selection_target", permutations = 20)` compares
all four representations on the same formula-eligible, labeled, deduplicated
cohort. It retains five-fold reports, three-/ten-fold sensitivity reports,
reports after omitting the largest scaffold group, and fixed-seed shuffled-label
controls. The largest group uses a lexicographic tie break. Permutations preserve
class counts, use identical shuffled labels across representations and refit the
complete preprocessing/model pipeline. Each diagnostic retains support failures
and null metrics; failed controls are never silently discarded.

These are exploratory checks, not a hyperparameter search, independent external
validation or a significance test. Selection targets describe curation, not
herbicidal activity. Omitting a scaffold changes the evaluated population; it
does not measure performance on that omitted group. Shuffled-label variability
is descriptive, and twenty permutations are a small control set.

Use an existing `screen.py` feature export to run the offline command:

```bash
uv run --project analysis python analysis/stress.py --features analysis/outputs/structure-review/structural_features.parquet --output analysis/outputs/structure-stress --permutations 20
```

The fresh output directory contains `stress_models.csv` and `manifest.json`
with exact input/code/lock/output hashes, package versions and control seeds.
Unknown targets and permutation counts outside integer 0–1000 raise `ValueError`;
nonempty output directories and outputs containing the input are rejected.
Run the focused checks with
`uv run --project analysis pytest analysis/tests/test_stress.py -q`.


## Frozen assay review exports

`review_assays.run(snapshots, output)` rebuilds review material from the frozen
`raw/chembl/*.json` bundles written by `agrotox.chembl.fetch_assay`. It operates
entirely offline and validates all inputs before writing products. No scratch
script or generated intermediate table is required.

```bash
uv run --project analysis python analysis/review_assays.py --snapshots analysis/outputs/chembl-2026-10-28 --output analysis/outputs/chembl-review-new
```

Use a fresh output directory on subsequent runs. Snapshot and output roots must
be separate, with neither containing the other. Existing nonempty outputs,
missing snapshot files, invalid source/assay/document identities, non-UTC retrieval
times, inconsistent page offsets/counts, duplicate activity IDs, mixed database
versions and conflicting source SMILES raise `ValueError` before any products
are written. Malformed JSON and nonfinite numbers are rejected. File access
errors propagate; concurrent source/output writers are not supported.

| Product | Contents |
|---|---|
| `activity_review.csv` | Every activity, source value/qualifier, assay/publication context, database version, retrieval time, raw snapshot path/hash and complete `raw_activity_json` |
| `candidates.csv` | One row per source molecule ID, with its supplied canonical SMILES |
| `label_review_template.csv` | Full label schema with activity and natural origin set to unknown and reference/context/policy fields blank |
| `manifest.json` | Exact consumed input, code, dependency-lock and product hashes, database version and row/missing-structure counts |

Review rows sort by activity ID; candidates sort by molecule ID. Repeated
measurements are retained. For a given molecule ID, a missing SMILES can be
filled from a consistent nonempty source record; conflicting nonempty strings
require explicit reconciliation. Separate molecule IDs are not merged on the
basis of identical structures. Missing or invalid SMILES remain review
candidates; chemistry validation occurs in `screen.py`. Empty assays retain
header-only exports and explicit zero counts.

CSV blanks represent missing selected fields; `raw_activity_json` preserves the
original record's nulls, types and unknown fields. The saved raw bundle and hash
retain the complete source assay/document metadata. No endpoint/unit conversion,
qualifier interpretation or active/inactive label assignment is performed.
The candidate list can be passed to `screen.py --candidates`; the worksheet is
usable with `--labels` only for the matching compound IDs and remains all unknown
until reviewed. These exports do not establish biological comparability.

Run the focused checks with
`uv run --project analysis pytest analysis/tests/test_review_assays.py -q`.


## Structural feature-block ablations

`ablations.ablate(rows, target = "selection_target")` compares nine predeclared
feature/preprocessing profiles on one formula-eligible, deduplicated cohort with
complete finite chemistry. The four original PCA baselines are accompanied by
formula + descriptors, formula + Morgan, combined with formula outside PCA,
combined with formula/descriptors outside fingerprint-only PCA, and formula +
Morgan with formula outside fingerprint PCA. Preserved features are standardized
individually; each projected block removes training constants, standardizes and
retains 95% training variance using PCA. Logistic regression remains L2,
class-balanced, C=1. No imputation or production-model replacement occurs.

All profiles share the same five scaffold folds, seed and compound order.
Missing targets, unsupported formulas and unusable structures are excluded from
the common cohort. Duplicate identities count once; conflicting targets and
invalid/duplicate IDs raise `ValueError`. Missing predictor values raise
`ValueError` rather than being filled. Class/scaffold support failures retain
null metric rows; a projected block lacking training variation retains
`no_training_variation`, without partial predictions. Raw preserved features
can include training constants, which scale to zero. There is no full-data fit.

```bash
uv run --project analysis python analysis/ablations.py --features analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet --output analysis/outputs/ablations-fixed-new
```

Use a fresh output directory. `ablation_models.csv` contains pooled held-out
metrics; `folds.csv` records fold sample sizes, dimensions and training/test
balanced accuracy; `out_of_fold.csv` preserves per-compound predictions and
assignments; `cohort.csv` identifies the exact compounds. `manifest.json` hashes
inputs, code, locks and products and records profile columns, versions and seed.
Nonempty outputs and output ancestors of the input are rejected. These are
exploratory selection comparisons, not evidence of herbicidal activity.
Run the focused checks with
`uv run --project analysis pytest analysis/tests/test_ablations.py -q`.


## Nested structural regularization experiments

`ablations.ablate(rows, target = "selection_target", tune = True)` selects
logistic-regression C independently within each outer training partition using
three inner scaffold folds. The predeclared grid is 0.01, 0.1, 1, 10 and 100;
smaller C means stronger L2 regularization. Selection maximizes mean inner-fold
balanced accuracy; ties within 1e-12 choose the smaller C. The selected estimator
is then refitted on all outer training compounds before predicting outer held-out
compounds. No outer test score is used to choose C.

```bash
uv run --project analysis python analysis/ablations.py --features analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet --output analysis/outputs/ablations-nested-new --tune
```

All nine profiles still share the same outer folds and complete cohort. Each
inner transformation fits exclusively on its own training partition; transformed
arrays may be reused across C values within that split because preprocessing
is independent of C. `inner_scores.csv` preserves every C/inner-fold score,
with profile, outer fold and sample sizes. It has only a header for fixed-C runs.
`folds.csv` records the chosen C and its mean inner score; the manifest records
nested mode, inner-fold count and the entire grid. The `tune` API flag must be a
boolean. Unsupported inner splits retain `insufficient_inner_scaffold_support`;
a projected block lacking variation in any required training split retains
`no_training_variation`. Neither case emits partial held-out predictions.

These experiments tune C only; PCA variance, class weights, threshold and profiles
remain fixed. Choosing a profile after inspecting outer scores remains exploratory
and requires independent confirmation. No full-sample estimator is fitted or
installed into the production screening workflow.
Run the focused checks with
`uv run --project analysis pytest analysis/tests/test_ablations.py -q`.

## Professor follow-up: halogens and raw fingerprints

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis python analysis/professor_followup.py --features analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet --output analysis/outputs/professor-followup-new
```

`professor_followup.diagnose` uses the existing formula-eligible canonical-structure
cohort and deterministic five scaffold folds. Eight fixed profiles share exactly
the same compounds/folds: the original formula PCA/logistic pipeline, standardized
raw formula logistic, halogen counts/fractions only, halogen presence only, formula
with direct halogen columns dropped, composition recalculated without halogens,
unscaled raw Morgan logistic and raw Morgan random forest. Logistic C=1,
class-balanced, cutoff 0.5; forest has 500 trees, minimum leaf size 2, square-root
feature sampling, class-balanced weights, fixed seed and one worker. These are
exploratory fixed comparisons, with no tuning or production replacement.

The stricter composition ablation removes F/Cl/Br/I and recalculates atom count,
element count and remaining fractions using complete `formula_composition`.
Dropping only direct columns retains halogen information in totals and denominators.
Neither ablation makes the remaining chemistry statistically independent of
halogenation, nor simulates chemically valid dehalogenated molecules. All profiles
require finite predictors; fingerprints must be valid binary vectors. Unknown labels,
identity conflicts and insufficient class/scaffold support follow existing ablation
contracts. Raw models can fit constant features; PCA retains an explicit
`no_training_variation` state. No partial predictions are exported on support failure.

The raw formula logistic model also exports five training-fold standardized
coefficient vectors and test-fold permutation ROC-AUC drops for each feature plus
a joint halogen block (10 fixed-seed shuffles per fold by default, configurable
0–100). Each joint shuffle preserves within-block relationships. Coefficient signs
refer to target 1. Means across folds/repeats are descriptive: correlated formula
counts/fractions redistribute coefficients and mask permutation importance, and
permutations can create impossible compositions. These are predictive associations,
not causal effects, significance tests or explanations of actual plant toxicity.
The coefficients explain the raw formula comparator, not the older PCA model.

Fresh outputs contain `reports.csv`, `oof.csv`, `cohort.csv`, `coefficients.csv`,
`permutations.csv` and a hash/version/parameter manifest. The cohort identifies
halogen presence and the evaluated target; OOF rows retain scaffold assignments.
The command is offline and never changes source features/labels. Run
`pytest analysis/tests/test_professor_followup.py -q` in the analysis environment.

## Weekly pilot diagnostics

`professor_followup.py` now adds precision, recall and F1 at threshold 0.5 to
scaffold-held-out reports. The existing structural evaluator also exports F1.
Formula coefficients describe the change in log odds of target=1 per training-fold
standard deviation. Compare signs and magnitude across folds; correlated formula
features prevent causal or independent-effect interpretations. PCA coefficients
are not original-feature weights. Morgan bits require substructure inspection
before receiving chemical names.

New runs additionally export `oob_importance.csv` for the matched-cohort raw
Morgan forest. `--oob-repeats 10` uses the existing 500-tree bootstrap settings,
shuffling each bit only within each tree's unsampled rows and combining the same
OOB vote denominators. Positive importance means an F1 decrease after permutation;
negative decreases are retained. Mean and SD describe repeat variation, not a
p-value or confidence interval. This exploratory full-cohort diagnostic does not
replace scaffold-held-out validation; related chemistry may share bootstrap
training and OOB samples. `--oob-repeats 0` disables this additional diagnostic.
Unavailable class/scaffold support yields empty importance exports. Existing
frozen runs remain unchanged. Selection targets still describe source curation,
not verified biological activity.
