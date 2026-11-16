# Analysis marimo presentation commit report

**Document status:** Historical delivery report, 2026-10-22. Reviewed for organization 2026-11-02.

Notebook, tracked analysis and cached rebuild exist; original test counts/branch claims describe that delivery.

Current guidance: [topic note](../../current/project-state.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Contents of the historical record:

- [Commits](#commits)
- [Verification](#verification)
- [Presentation order](#presentation-order)
- [Reproduction](#reproduction)
- [Remaining limits](#remaining-limits)

Branch: `feat/seven-endpoint-experiments`
Base: `aa8e45b` — docs: record seven endpoint experiment checkpoint
Status: four new local commits; nothing pushed or merged. The final commit is the marimo presentation.

## Commits

1. `aba2ce2` — refactor: retain presentation analysis outside experiments
   Purpose: Keep experimental working files ignored while maintaining the tested seven-endpoint analysis under a tracked analysis directory.
   - `.gitignore`
   - `analysis/FINDINGS.md`
   - `analysis/README.md`
   - `analysis/build_traits.py`
   - `analysis/classifiers.py`
   - `analysis/compare.py`
   - `analysis/distributions.py`
   - `analysis/endpoint_analysis.py`
   - `analysis/endpoint_coverage.py`
   - `analysis/stats.py`
   - `experiments/04_traits.py`
   - `experiments/05_distributions.py`
   - `experiments/06_compare.py`
   - `experiments/07_classifiers.py`
   - `experiments/08_epa_coverage.py`
   - `experiments/notes/current/project-state.md`
   - `experiments/README.md`
   - `experiments/endpoint_analysis.py`
   - `experiments/stats.py`
   - `pipeline/docs/decisions.md`
   - `pipeline/tests/test_experiment_distributions.py`
   - `pipeline/tests/test_experiment_endpoints.py`
   - `pipeline/tests/test_experiment_models.py`

2. `2dc6708` — feat: rebuild presentation analysis from read-only caches
   Purpose: Create locked analysis products in a separate directory while preserving source caches and recording provenance for the professor presentation.
   - `analysis/README.md`
   - `analysis/build_traits.py`
   - `analysis/classifiers.py`
   - `analysis/compare.py`
   - `analysis/distributions.py`
   - `analysis/endpoint_analysis.py`
   - `analysis/endpoint_coverage.py`
   - `analysis/pyproject.toml`
   - `analysis/rebuild.py`
   - `analysis/uv.lock`
   - `pipeline/docs/decisions.md`
   - `pipeline/tests/test_analysis_rebuild.py`

3. `576336e` — feat: prepare evidence-aware professor presentation views
   Purpose: Present seven endpoint availability distributions and chemical traits with selected denominators, explicit missingness, and classifier baselines.
   - `analysis/README.md`
   - `analysis/presentation.py`
   - `pipeline/docs/decisions.md`
   - `pipeline/tests/test_analysis_presentation.py`

4. `552e02e` — feat: present professor findings in a marimo notebook
   Purpose: Lead with seven endpoint availability distributions before chemical traits and classifier baselines in an executed interactive professor presentation.
   - `.gitignore`
   - `analysis/FINDINGS.md`
   - `analysis/README.md`
   - `analysis/professor_notebook.py`
   - `analysis/pyproject.toml`

## Verification

- Full suite in the new analysis environment: 1,006 passed.
- Ruff: all checks passed for analysis and pipeline.
- `marimo check analysis/professor_notebook.py`: passed.
- Executed HTML export: passed; output at `analysis/outputs/professor_presentation.html` (ignored).
- Rebuilt real cached source data into `analysis/data/` without network queries or writes to source caches.
- Endpoint, descriptor, and classifier plots rendered to PNG and visually inspected.
- Live notebook previewed in Dia; source selector changed to EPA hazard and verified.
- `git ls-files experiments` returns no paths; the original local files remain present and ignored.
- Generated inputs/results, exports, and marimo sessions are ignored.

## Presentation order

1. Seven primary endpoint availability distributions (LD50, LC50, EC50, NOAEL, LOAEL, BMD, BMDL).
2. Molecular weight, XLogP, polarity, and complexity distribution comparisons.
3. Study-coverage and measured/calculated-property comparisons.
4. Classifier accuracy against majority baselines, including sparse-target limits.
5. Additional trait exploration and study-level toxicity observations with context.

## Reproduction

```bash
uv sync --project analysis --locked
uv run --project analysis python analysis/rebuild.py --source experiments/data
uv run --project analysis marimo run analysis/professor_notebook.py
```

The selected source root can be any equivalent cache; no analysis code imports experiment Python files. The prepared environment can also run directly with `analysis/.venv/bin/marimo`.

## Remaining limits

- The endpoint plots describe extracted evidence availability. Heterogeneous chronic potency values are not pooled.
- BMD is absent and BMDL too sparse for five-fold modeling in the current cached selection.
- Natural-product selection is purposive, with differences in source and assay coverage.
- Data and reports are local. A clean checkout needs access to the input selection and caches to rebuild.
- Concurrent edits adding marimo to `pipeline/pyproject.toml` and `pipeline/uv.lock` were left untouched and excluded from commits; the committed analysis environment has a separate dependency lock.
- The static HTML captures the default view; Python-backed selectors require the live marimo app.
