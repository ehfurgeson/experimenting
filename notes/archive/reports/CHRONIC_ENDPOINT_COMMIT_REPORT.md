# Chronic endpoint implementation report

**Document status:** Historical delivery report, 2026-10-22. Reviewed for organization 2026-11-02.

Structured seven-endpoint support exists; cached counts and test counts belong to this checkpoint.

Current guidance: [topic note](../../current/evidence-and-identities.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Contents of the historical record:

- [Commits](#commits)
- [Verification](#verification)
- [Current cached coverage and limits](#current-cached-coverage-and-limits)
- [Outputs](#outputs)

Branch: `feat/chronic-endpoints`
Base: `b1f8fd4` — restrict hazard comparisons to experimental records
Status: seven local commits; nothing pushed or merged.

NOAEL, LOAEL, BMD, and BMDL now have structured EPA normalization, unit-specific matching, availability counts, preserved study context, review reasons, and explicit context requirements for potency summaries.

## Commits

1. `7fafb40` — refactor: centralize normalized endpoint policy
   Preserve existing endpoint eligibility and unit conversions through one shared policy.

   - `pipeline/README.md`
   - `pipeline/docs/decisions.md`
   - `pipeline/src/agrotox/_context.py`
   - `pipeline/src/agrotox/coverage.py`
   - `pipeline/src/agrotox/endpoints.py`
   - `pipeline/src/agrotox/epa_hazard.py`
   - `pipeline/src/agrotox/units.py`

2. `bc593ab` — feat: normalize point of departure dose units
   Convert reported point of departure doses while preserving the distinction between total dose and daily dose.

   - `pipeline/README.md`
   - `pipeline/docs/decisions.md`
   - `pipeline/src/agrotox/endpoints.py`
   - `pipeline/src/agrotox/units.py`
   - `pipeline/tests/test_units.py`

3. `cc5f559` — feat: retain study context in comparison records
   Preserve explicit study and benchmark context when matching or consolidating toxicity observations.

   - `pipeline/README.md`
   - `pipeline/docs/decisions.md`
   - `pipeline/src/agrotox/analysis.py`
   - `pipeline/src/agrotox/contracts.py`
   - `pipeline/src/agrotox/coverage.py`
   - `pipeline/src/agrotox/normalize.py`
   - `pipeline/src/agrotox/tables.py`
   - `pipeline/tests/test_comparisons.py`

4. `84d29f4` — feat: constrain point of departure summaries
   Count point of departure availability while requiring explicit comparable context before summarizing potency.

   - `pipeline/README.md`
   - `pipeline/docs/decisions.md`
   - `pipeline/src/agrotox/analysis.py`
   - `pipeline/src/agrotox/coverage.py`
   - `pipeline/src/agrotox/tables.py`
   - `pipeline/tests/test_pod_comparisons.py`

5. `ee3f80b` — feat: normalize EPA point of departure evidence
   Normalize supported EPA hazard observations with source provenance and explicit review reasons for excluded records.

   - `pipeline/README.md`
   - `pipeline/docs/decisions.md`
   - `pipeline/src/agrotox/epa_hazard.py`
   - `pipeline/src/agrotox/tables.py`
   - `pipeline/tests/test_epa_hazard.py`

6. `612be20` — feat: analyze cached EPA hazard evidence offline
   Build source-specific coverage and review tables from selected approved EPA hazard caches without network requests.

   - `pipeline/README.md`
   - `pipeline/docs/decisions.md`
   - `pipeline/examples/analyze_epa_hazards.py`
   - `pipeline/examples/endpoints.yaml`
   - `pipeline/src/agrotox/epa_workflow.py`
   - `pipeline/src/agrotox/tables.py`
   - `pipeline/tests/test_epa_workflow.py`

7. `c182291` — test: verify seven endpoint offline analysis
   Verify all seven endpoint types through cached analysis while documenting current coverage and stale processed results.

   - `pipeline/README.md`
   - `pipeline/docs/point_of_departure_check.md`
   - `pipeline/tests/test_epa_workflow.py`

## Verification

- Full suite: 989 passed using `.venv/bin/pytest -q` from `pipeline/`.
- Focused endpoint-unit, study-context, point-of-departure comparison, EPA normalization, and offline-workflow checks passed before their respective commits.
- Ruff: all checks passed using `.venv/bin/ruff check .` from `pipeline/`.
- Diff whitespace checks passed.
- Real cached run: eleven deterministic analysis tables, unchanged selected input hashes, and verified export dependency sidecars.
- Acute EPA coverage matched the adapter at base commit b1f8fd4 on the same raw evidence.

## Current cached coverage and limits

- Oral daily-dose NOAEL: 50 compounds (34 herbicides, 16 natural products).
- Oral daily-dose LOAEL: 40 compounds (32 herbicides, 8 natural products).
- Oral daily-dose BMDL: 2 compounds, both herbicides; three source records.
- BMD: implemented and tested, but no records in current caches.
- Chronic policies default to availability: all 92 chronic compound summary medians are null.
- PubChem prose extraction remains acute-only; adding chronic prose extraction is separate work.
- Existing experiment comparison products are stale under the earlier experimental-only admission rule; rebuilt EPA oral LD50 coverage is 50 rather than 76.
- No remaining implementation work for the authorized EPA-first extension; fuller metadata or additional sources are needed for broader potency comparisons.

## Outputs

- `pipeline/.live-smoke/chronic-endpoints/`: rebuilt Parquet analysis products and dependency metadata, gitignored.
- `pipeline/docs/point_of_departure_check.md`: committed coverage checkpoint and reproduction command.
- `notes/archive/reports/ENDPOINT_DEFINITIONS.md`: corrected local endpoint note, gitignored as required by the commit guide.
