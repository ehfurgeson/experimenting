# Structural ablation delivery — 2026-10-29

**Document status:** Historical diagnostic delivery report, 2026-10-29. Reviewed for organization 2026-11-02.

Common-cohort fixed/nested comparisons are implemented; no production-model replacement or verified activity claim follows.

Current guidance: [topic note](../../current/structure-and-activity.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Branch: fix/reproducible-structure-folds
Base for this round: 586b04f (chore: document compound label research workflow)
Initial/final tracked worktrees clean. All commits local; nothing pushed or
merged, no pre-existing commits rewritten, no pre-existing uncommitted work
modified/discarded. Production models and all source/label data unchanged.

## Incremental commits

1. 7ecf24f feat: compare structural feature combinations
   Purpose: Establish equal-cohort, identical-fold comparisons of the original
   four baselines and five feature-block/PCA variants. No imputation or full-data fit.
   Files: analysis/ablations.py, analysis/tests/test_ablations.py,
   analysis/README.md, analysis/docs/decisions.md.
2. 01949a7 feat: tune structural regularization within scaffold folds
   Purpose: Select C inside three inner scaffold folds, preserving all five
   outer folds for assessment, and export every candidate score and selected C.
   Files: analysis/ablations.py, analysis/tests/test_ablations.py,
   analysis/README.md, analysis/docs/decisions.md.
3. 806af00 chore: record structural ablation experiment results
   Purpose: Record actual cached results, interpretation, limits and commands.
   Files: analysis/docs/feature_combination_check.md, analysis/FINDINGS.md.

## Verification

New behavior tests failed before each implementation. Checks ran at each code
commit boundary; final commands/outcomes from repository root:

analysis/.venv/bin/python -m pytest analysis/tests/test_ablations.py -q -> 26 passed
analysis/.venv/bin/python -m pytest analysis/tests -q -> 143 passed
pipeline/.venv/bin/python -m pytest pipeline/tests -q -> 1,043 passed
analysis/.venv/bin/ruff check analysis -> clean
pipeline/.venv/bin/ruff check pipeline -> clean
git diff --check -> clean

The first code slice separately passed 16 focused/133 analysis/1,043 pipeline tests.
Tests reproduce baseline probabilities/metrics, trace all inner/outer preprocessing
fits to training rows only, test tie handling and support failures, and verify exports.
CLI help and local checkpoint links verified. Independent output checks confirm:
- All 18 comparisons use 171 identical structures (55 positive, 116 negative).
- Original five formula scaffold assignments match every profile/mode.
- Each profile has one held-out prediction per compound; no scaffold crosses folds.
- All 675 inner candidate scores are retained; selected C/means recompute exactly.
- Zero predictor values imputed; all input/code/lock/output hashes verify.
- Fixed-C metrics reproduce the original four common-cohort baselines.

## Results and artifacts

Full scientific results: analysis/docs/feature_combination_check.md.
Fixed and nested final products:
analysis/outputs/ablations-fixed-2026-10-29-final/
analysis/outputs/ablations-nested-2026-10-29-final/
Each has metric, OOF, fold, cohort, inner-score CSVs and a provenance manifest.
All generated products remain ignored. Reproduction commands are in the tracked report.

Formula + descriptors: 92.82% balanced accuracy at C=1 (net one extra detected
selected herbicide compared with formula's 91.91%). Preserving formula outside
PCA alone does not restore formula-only performance at C=1. Nested C selection
raises original combined performance from 85.45% to 91.48%, versus formula's
92.77%. All fingerprint profiles choose C=100 in every outer fold; formula
chooses C=0.1 or 0.01. Combined ROC-AUC was already 0.9773 and becomes 0.9793;
fixed-threshold misses/false positives change from 16/0 to 7/5. This supports
regularization and operating-point sensitivity as a substantial part of the gap,
rather than treating formula loss in PCA as its sole explanation.

## Unresolved / follow-up

No independent profile confirmation, significance interval, calibration or
herbicidal-activity validation is claimed. Grid-boundary selection does not
establish optimal C beyond 100; grid and thresholds were not adapted after outer
results. Profile comparisons remain exploratory even though C is nested. Reviewed
activity labels and independent chemistry/publications are still necessary for
the ultimate activity-classification goal. No model default was replaced.
