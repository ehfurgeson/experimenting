# Structural expansion delivery — 2026-10-28

**Document status:** Historical acquisition/stress delivery report, 2026-10-28. Reviewed for organization 2026-11-02.

Bounded ChEMBL snapshots and stress diagnostics exist; acquired measurements are not automatically reviewed activity labels.

Current guidance: [topic note](../../current/structure-and-activity.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Branch: fix/reproducible-structure-folds
Base for this round: b868b04 (fix: stabilize structural evaluation across row order)
Original branch base: e1277ee on feat/structure-classifier.
Initial/final tracked worktrees clean. All commits local. Nothing pushed or merged;
no pre-existing commit rewritten; no pre-existing uncommitted work modified or
discarded. Original compound selection, analysis/data and experiments/data unchanged.
Downloaded snapshots, review products and diagnostics remain ignored.

## Incremental commits

1. 4725d51 feat: retrieve bounded ChEMBL assay snapshots
   Purpose: Preserve complete raw assay evidence with publication context before
   deriving any activity labels. Independent acquisition boundary.
   Files: pipeline/src/agrotox/chembl.py, pipeline/tests/test_chembl.py,
   pipeline/examples/fetch_chembl_assay.py, pipeline/README.md,
   pipeline/docs/decisions.md.
2. e65e1c2 feat: stress test structural selection models
   Purpose: Compare equal-denominator models, fold counts, dominant-scaffold
   sensitivity and shuffled-label controls. Independent diagnostic boundary.
   Files: analysis/stress.py, analysis/tests/test_stress.py,
   analysis/README.md, analysis/docs/decisions.md.
3. af9b84d test: exercise reviewed screening with real structures
   Purpose: Verify existing chemistry-to-candidate exports using RDKit-derived
   features rather than injected feature arrays. Outcomes/references are synthetic
   test fixtures; this commit adds coverage without changing model behavior.
   Files: analysis/tests/test_screen.py.
4. db7866e chore: record structural stress and acquisition results
   Purpose: Record verified live evidence and remaining scientific limitations.
   Files: analysis/FINDINGS.md, analysis/docs/compound_sources.md,
   analysis/docs/structural_validation_check.md.

## Checks run from repository root

pipeline/.venv/bin/python -m pytest pipeline/tests/test_chembl.py -q -> 37 passed
analysis/.venv/bin/python -m pytest analysis/tests/test_stress.py -q -> 10 passed
analysis/.venv/bin/python -m pytest analysis/tests/test_screen.py -q -> 8 passed
analysis/.venv/bin/python -m pytest analysis/tests -q -> 87 passed
pipeline/.venv/bin/python -m pytest pipeline/tests -q -> 1,043 passed
analysis/.venv/bin/ruff check analysis -> clean
pipeline/.venv/bin/ruff check pipeline -> clean
git diff --check -> clean

The two new capabilities were exercised failing before implementation. The
additional test-only slice covered already-supported behavior without claiming
an artificial red test. Each implementation/test slice passed both full suites
and both lint checks before commit. Documentation links and CLI help verified.

## Actual data and model runs

- Current 176-compound structural baseline reproduced.
- 96 stress reports: shared 171-structure cohort, 3/5/10-fold scaffold evaluation,
  largest-scaffold removal, 20 shuffled-label controls per representation.
- Common-cohort five-fold balanced accuracy: 91.9% formula, 72.4% descriptors,
  76.4% Morgan, 85.5% combined. Shuffled means 49.2–50.2%.
- Removing the dominant 49-compound benzene scaffold leaves 122 compounds;
  combined balanced accuracy becomes 77.0%.
- 14 ChEMBL_37 assay snapshots, each from a different publication: 157 activity
  records; 154 unique structures; 28 scaffolds; 149 structures outside the old
  selection. All structures parse. 45 inequalities and three missing numeric
  outcomes retained; no inferred generic active/inactive/origin labels.
- Live 25-record assay retrieved over four pages matches initial raw records.
- CHEMBL3066645 source-reported >80% versus <50% growth-inhibition pilot:
  24 rows, 14 high and ten low; only two low-response scaffolds. Five-/three-fold
  evaluation refuses insufficient scaffold support. Two-fold balanced accuracy:
  formula 50.0%, descriptors 44.3%, Morgan 37.1%, combined 42.9%.
- All 616 production candidate/representation scores remain activity_model_unavailable
  with null probabilities, because reviewed labels are absent.
- Acquisition, structural baseline, stress and candidate manifest hashes verified.

## Local artifacts

analysis/outputs/chembl-2026-10-28/raw/chembl/ — frozen raw bundles
analysis/outputs/chembl-2026-10-28/activity_review.csv — measured outcomes/provenance
analysis/outputs/chembl-2026-10-28/candidates.csv — 154 deduplicated structure IDs
analysis/outputs/chembl-2026-10-28/manifest.json — acquisition hashes and counts
analysis/outputs/chembl-2026-10-28/reported_response_diagnostics.json — single-assay pilot
analysis/outputs/structure-2026-10-28-stress-baseline/ — unchanged cache rerun
analysis/outputs/stress-2026-10-28/ — 96 diagnostics and provenance
analysis/outputs/chembl-screen-2026-10-28/ — final candidate features/status exports
analysis/outputs/chembl-pagination-check-2026-10-28/ — live pagination check

## Remaining work

Review original publications to reconcile species, dose, timing, units, qualifiers
and thresholds before curating comparable labels. Add independent low-response
scaffolds and reserve publication-held-out data. Natural-origin evidence remains
separate. No useful real activity classifier, calibration, external validation or
broad natural-product screen is claimed. Acquisition is a bounded purposive subset,
not a complete database census. Full tracked checkpoint and commands:
analysis/docs/structural_validation_check.md.
