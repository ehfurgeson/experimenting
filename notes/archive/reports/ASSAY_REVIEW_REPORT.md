# Frozen assay review export delivery — 2026-10-29

**Document status:** Historical delivery report, 2026-10-29. Reviewed for organization 2026-11-02.

Validated frozen-assay export is implemented; biological label review remains separate.

Current guidance: [topic note](../../current/structure-and-activity.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Branch: fix/reproducible-structure-folds
Base for this round: db7866e (chore: record structural stress and acquisition results)
Initial and final tracked worktrees clean. All changes committed locally.
Nothing pushed or merged; no pre-existing commits rewritten; no pre-existing
uncommitted work modified or discarded. Original data, raw snapshots and prior
review products unchanged. New generated products remain ignored.

## Commit

1. 9fbc272 feat: rebuild assay review files from frozen snapshots
   Purpose: Replace the ignored scratch-script dependency with an offline,
   validated, deterministic source-to-review command. Unknown labels remain
   unknown; no model is trained automatically on unreviewed assay outcomes.
   Files:
   - analysis/review_assays.py
   - analysis/tests/test_review_assays.py
   - analysis/README.md
   - analysis/docs/decisions.md
   - analysis/docs/structural_validation_check.md

The command rejects incomplete/corrupt snapshots, invalid identifiers/counts/
offsets, mixed releases, duplicate activities, conflicting source SMILES,
non-UTC timestamps, nonstandard/nonfinite JSON numbers, and unsafe output roots.
Missing structures remain review rows. Complete raw activity JSON, source hashes,
publications, qualifiers and unknown fields are preserved. Separate compound IDs
remain separate even when their structures match. All semantic validation occurs
before writing outputs; filesystem errors may still leave partial product files.

## Verification

The initial tests failed against the unimplemented behavior, then passed after
implementation. Final checks from the repository root:

analysis/.venv/bin/python -m pytest analysis/tests/test_review_assays.py -q -> 30 passed
analysis/.venv/bin/python -m pytest analysis/tests -q -> 117 passed
pipeline/.venv/bin/python -m pytest pipeline/tests -q -> 1,043 passed
analysis/.venv/bin/ruff check analysis -> clean
pipeline/.venv/bin/ruff check pipeline -> clean
git diff --check -> clean

Actual offline rebuild: all 14 frozen assays, 157 activity records and all
154 candidates match the earlier products by source ID and every previously
exported evidence field. Original acquisition manifest hashes still verify.
New review and screening manifests verify every input/code/lock/output hash.
Worksheet ingestion through screen.py retains all 154 valid structures with
null activity/origin targets and explicit unsupported-model reports.

## Ready local products

analysis/outputs/chembl-review-2026-10-29-final/activity_review.csv
analysis/outputs/chembl-review-2026-10-29-final/candidates.csv
analysis/outputs/chembl-review-2026-10-29-final/label_review_template.csv
analysis/outputs/chembl-review-2026-10-29-final/manifest.json
analysis/outputs/chembl-review-screen-2026-10-29-final/

The tracked analysis/docs/structural_validation_check.md records reproduction
commands and observed results. Use a new output directory for any rerun.

## Remaining work

Publication-level biological review and comparable activity-label curation remain.
No useful validated herbicidal-activity model, natural-origin labels, calibration,
or independent external validation is claimed. These exports remove a reproducibility
gap; they do not manufacture evidence or remove the earlier scaffold limitations.
