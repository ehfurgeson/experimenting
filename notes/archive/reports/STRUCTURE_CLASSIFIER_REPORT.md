# Local structural classifier implementation report

**Document status:** Historical structural delivery report, 2026-10-27. Reviewed for organization 2026-11-02.

Formula/descriptor/scaffold machinery is implemented; reviewed real activity models remain unsupported by the inspected labels.

Current guidance: [topic note](../../current/structure-and-activity.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Branch: feat/structure-classifier
Base: 552e02e (feat: present professor findings in a marimo notebook)
Status: local only; no upstream, push, merge or pre-existing history rewrite.

Initial and final Git worktrees are clean; no pre-existing uncommitted changes were modified or discarded.

## Commits

1. bcb76f2 chore: provision structure modeling dependencies
   Purpose: Lock the chemistry and machine-learning libraries used by structural analysis.
   Files: analysis/README.md, analysis/docs/decisions.md, analysis/pyproject.toml, analysis/tests/test_structure_environment.py, analysis/uv.lock

2. 2d58c13 feat: extract formula composition features
   Purpose: Preserve missing and unsupported formulas while counting validated elemental composition.
   Files: analysis/README.md, analysis/docs/decisions.md, analysis/formula.py, analysis/tests/test_formula.py

3. 906a8f4 feat: compute structural screening descriptors
   Purpose: Derive molecular descriptors and explicitly named screening proxies from validated SMILES.
   Files: analysis/README.md, analysis/docs/decisions.md, analysis/structure.py, analysis/tests/test_structure.py

4. c63cb87 feat: validate independent compound activity labels
   Purpose: Require cited activity and natural-origin labels independently of selection membership.
   Files: analysis/README.md, analysis/docs/decisions.md, analysis/labels.py, analysis/tests/test_labels.py

5. e3c9891 feat: evaluate scaffold-held-out structure models
   Purpose: Evaluate structural predictions with training-only reduction and explicit support limits.
   Files: analysis/README.md, analysis/docs/decisions.md, analysis/pyproject.toml, analysis/structure_models.py, analysis/tests/test_structure_models.py, analysis/uv.lock

6. 8355820 feat: expose offline structural screening workflow
   Purpose: Export auditable structural features and model results from cached compound traits.
   Files: analysis/README.md, analysis/docs/decisions.md, analysis/screen.py, analysis/tests/test_screen.py

7. 5e5b500 feat: compare complete elemental identities
   Purpose: Detect formula conflicts involving elements outside the common predictor list.
   Files: analysis/README.md, analysis/docs/decisions.md, analysis/formula.py, analysis/screen.py, analysis/tests/test_formula.py, analysis/tests/test_screen.py

8. e1277ee chore: document compound expansion evidence
   Purpose: Record source-specific acquisition paths and the remaining activity-label requirements.
   Files: analysis/FINDINGS.md, analysis/README.md, analysis/docs/compound_sources.md

## Verification

Focused test files were exercised red before implementation and then green.
- analysis/.venv/bin/python -m pytest analysis/tests -q: 68 passed.
- pipeline/.venv/bin/python -m pytest pipeline/tests -q: 1,006 passed.
- analysis/.venv/bin/ruff check analysis: clean.
- pipeline/.venv/bin/ruff check pipeline: clean.
- Both environments synchronized with uv sync --locked --offline.
- CLI help, cached 176-compound run, local documentation links and manifest hashes verified.
- git diff --check: clean.

## Results and limits

All structural work runs without toxicity. Formula-only selection modeling achieves 91.9% balanced accuracy on 171 eligible cached compounds; this is selection discrimination, not an activity claim.
Reviewed activity/origin labels are absent; no validated real activity classifier or broad natural-product screen is claimed.
Two multicomponent structures and three charged formulas retain explicit review states.
Tice is an explicitly documented RDKit proxy; exact original descriptor calculators were not reproduced.
Broad database acquisition, label curation and independent activity validation remain data-dependent follow-ups, with planned slices in notes/current/next-steps.md.
Full source assessment: analysis/docs/compound_sources.md. Dated metrics: analysis/FINDINGS.md.
Local generated outputs: analysis/outputs/structure-2026-10-27-verified/; source caches unchanged.
