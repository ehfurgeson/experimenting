# Editable manual verification pack

Initialized 2026-11-05. No scientific approval or known labels have been assigned.

Follow `analysis/docs/verification-checklist.md` from the repository root.

- `assays/li2006_source_mapping.csv`: 24 source-row/structure checks to complete.
- `assays/he2011_source_mapping.csv`: 58 source-row/structure checks to complete.
- `assays/reviewed_labels.csv`: exact seven-column working label copy; all 154 rows remain unknown.
- `assays/policy_working.md`: explicitly unapproved source-policy draft to discuss and version.
- `assays/*_reference.csv`: earlier AI-assisted source annotations, not human sign-off.
- `dietary/review.csv`: 40-row editable dietary review copy; no high-dose/plant labels accepted.
- `dietary/triage_reference.csv`: automated prioritization only; not a label file.
- `sources/`: save legally obtained papers/SI and annotated source excerpts here, with source citations.

Human fields in the source-mapping worksheets start blank. Do not mistake the
AI-assisted reviewer names in reference files for scientific acceptance.
Do not combine different activity policies in the seven-column label copy:
use it for one accepted policy at a time and save separately versioned files.

The initialization manifest records starting bytes. Editing these working copies
is expected; preserve dated copies of completed decisions instead of treating the
initial output hashes as ongoing proof that a working file must never change.
The notebook does not read these editable files as accepted evidence. Its frozen
source/result checks are independent of this working pack.

`assays/structure_drawings/` contains seven SVG reference sheets covering all 82
Li/He entries. Open them in a browser/image viewer beside the original paper/SI.
The labels identify frozen ChEMBL and activity IDs, not original paper compound
numbers. These are computed depictions of supplied SMILES, not verified source
structures; a chemistry reviewer still needs to confirm each exact match.
The drawing manifest separately records the initial mapping inputs and SVG hashes.

Run `analysis/.venv/bin/python analysis/outputs/manual-verification-2026-11-05/validate_labels.py`
from the repository root to check the working label schema without fitting.
Use `--labels path/to/versioned_labels.csv` for a saved policy-specific version.
This does not verify scientific sign-off, source truth or comparability.
