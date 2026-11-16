# Experiment endpoint integration report

**Document status:** Historical delivery report, 2026-10-22. Reviewed for organization 2026-11-02.

Endpoint integration is implemented; maintained analysis now lives under analysis/, not the earlier experiment script layout.

Current guidance: [topic note](../../current/evidence-and-identities.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Branch: `feat/seven-endpoint-experiments`
Base: `c182291` — test: verify seven endpoint offline analysis
Status: seven local commits; nothing pushed or merged.

## Behavior

All seven endpoint types flow through source-specific cached coverage, trait flags, distributions, comparisons, and classifier targets. Chronic example policies remain availability-only. EPA source observations retain experimental admission and model-derived BMD/BMDL classifications; TEST predictions remain separate.

## Commits

1. `ac81e81` — feat: rebuild experiment endpoint coverage from raw evidence
   Purpose: Compare all seven endpoints on the full selected compound universe while retaining current EPA study context and review products.
   - `experiments/08_epa_coverage.py`
   - `experiments/README.md`
   - `experiments/endpoint_analysis.py`
   - `pipeline/docs/decisions.md`
   - `pipeline/tests/test_experiment_endpoints.py`

2. `929203f` — feat: expose source-specific endpoint traits in experiments
   Purpose: Preserve assessed and unavailable endpoint states across PubChem and EPA evidence without introducing unsupported potency summaries.
   - `experiments/04_traits.py`
   - `experiments/README.md`
   - `experiments/endpoint_analysis.py`
   - `pipeline/docs/decisions.md`
   - `pipeline/tests/test_experiment_endpoints.py`

3. `9dade83` — feat: describe sparse endpoint availability distributions
   Purpose: Retain every endpoint availability flag with explicit missing-data counts instead of interpreting coverage as a molecular property or potency.
   - `experiments/05_distributions.py`
   - `experiments/06_compare.py`
   - `experiments/README.md`
   - `experiments/endpoint_analysis.py`
   - `experiments/stats.py`
   - `pipeline/docs/decisions.md`
   - `pipeline/tests/test_experiment_distributions.py`

4. `a331504` — fix: validate classifiers with training-fold preprocessing
   Purpose: Apply training-fold scaling to held-out compounds while withholding accuracy when either target class cannot support five folds.
   - `experiments/README.md`
   - `experiments/stats.py`
   - `pipeline/docs/decisions.md`
   - `pipeline/tests/test_experiment_models.py`

5. `3a11bfb` — feat: model availability across seven toxicity endpoints
   Purpose: Explore every source-specific endpoint target using assessed labels while reporting unsupported sparse targets without fitted accuracy.
   - `experiments/07_classifiers.py`
   - `experiments/README.md`
   - `pipeline/docs/decisions.md`
   - `pipeline/tests/test_experiment_models.py`

6. `3703db9` — fix: preserve molecular count trait categories
   Purpose: Keep atom and bond descriptors classified as molecular properties so evidence coverage summaries describe only study-related counts.
   - `experiments/endpoint_analysis.py`
   - `pipeline/tests/test_experiment_distributions.py`

7. `aa8e45b` — docs: record seven endpoint experiment checkpoint
   Purpose: Document refreshed cached coverage and model support while explaining source availability, chronic potency limits, and reproducible analysis commands.
   - `experiments/notes/current/project-state.md`
   - `experiments/README.md`

## Verification

- Focused experiment endpoint tests: 4 passed.
- Focused distribution tests: 3 passed.
- Focused model tests: 4 passed.
- Full suite: `pipeline/.venv/bin/python -m pytest pipeline/tests -q` — 1,000 passed.
- Ruff: all checks passed for pipeline plus the retained experiment analysis scripts.
- Each behavior regression was observed failing before its implementation.
- Real cached run of scripts 08, 04, 05, 06, and 07 completed successfully.
- All eleven EPA dependency sidecars match current inputs and implementation hashes.
- Generated CSV/Parquet products, raw data, logs, and credentials are excluded from commits.

## Current results

- 176 compounds: 60 herbicides, 116 natural products; 136 approved EPA identities.
- EPA daily-dose coverage: NOAEL 50 compounds; LOAEL 40; BMD 0; BMDL 2.
- Current EPA mammal oral LD50 coverage: 50, replacing the stale 76.
- 78 trait columns; 24 source-specific/combined endpoint flags.
- 118 distribution rows; 59 comparison rows; 27 classifier target rows.
- 12 classifier targets evaluated; 15 have insufficient class support.
- All 92 chronic compound-summary medians remain null under availability policies.

## Limits and follow-up

- Chronic potency comparisons require stronger study/benchmark context or explicitly constrained policies.
- PubChem chronic prose extraction remains unsupported; its chronic flags describe extraction coverage.
- BMD is absent and BMDL too sparse for five-fold validation in the current caches.
- Existing preparation scripts 01–03, curated input files, and provenance notes remain local; this task tracks analysis integration rather than promoting the entire experiments directory.
- Optional ToxCast/property coverage retains existing processed source products; EPA endpoint analysis always rebuilds raw hazard evidence.
- Raw normalized endpoint observations remain separate from pooled trait flags; no toxicity ranking or safety score is introduced.
- The existing long-form trait value column remains text for compatibility.
