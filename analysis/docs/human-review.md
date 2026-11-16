# Human review adoption and reviewed-cohort comparison

Run from the repository root in the locked analysis environment. This workflow
uses local reviewed evidence; it does not obtain additional scientific approvals.

## Adoption

`review_adoption.py` reads literal XLSX cells without editing the workbook. It
requires a separate JSON human-adoption declaration with `approval_id`, `reviewer`,
`review_date` (ISO date) and `statement`. The declaration records what the user
asserted; the program does not independently certify reviewer expertise or work.

```bash
uv run --project analysis --locked python analysis/review_adoption.py \
  --workbook <human-reviewed-second-pass.xlsx> \
  --review <frozen-expansion-review-directory> \
  --release <historical-verification-release-directory> \
  --audit <frozen-verification-audit-directory> \
  --legacy-features <frozen-assay-structural_features.parquet> \
  --approval <human-adoption.json> --output <new-directory>
```

The workbook must contain `Reviewed Worksheet` and cover every original
compound/axis/policy exactly once. A known decision requires approved status,
checked source identity, reviewer/date and source references. Specific workbook
revisions supersede earlier automatic proposals. Unreviewed/unknown outcomes
remain unknown even under a general human adoption declaration. All workbook
sheets are exported with source row locators; formulas and Excel errors are
rejected rather than trusting stale cached decisions.

Supported historical assay proposals are adopted under the user's asserted human
review in separate datasets. Original review flags remain in a companion ledger.
Li source-identity conflict, unreadable source assignment and unresolved comparator
stereochemistry remain excluded; missing outcomes and gray bands remain unknown.
Manufacturing provenance does not become a canonical `synthetic` origin label.
The original seven-column label interface remains unchanged, with one activity
policy per dataset and companion evidence/approval history.

The 1998 policy is explicitly the authors' two-species very-active reagent
category at 1 mM (lettuce day six, millet day four). It is not a quantitative
vehicle-controlled efficacy estimate and supplies no inactive threshold. The
second-pass workbook withdraws the earlier field low-response proposals:
non-significance is not equivalence, and formulated-product results do not
establish isolated-ingredient activity. The sarmentine dose conflict persists.
Retracted Walker 2003 origin evidence is excluded in favor of the workbook's
independent Farag 2022 citation for trans-cinnamic acid.

Products include policy-specific labels, origin labels, original and adopted
decision ledgers, 119 second-pass treatment observations, policy definitions,
activity model/support reports, any supported activity out-of-fold predictions,
and a separate provenance-cohort feature table. Existing five-fold class/scaffold
guards are applied without lowering their thresholds. Unsupported models retain
null metrics, no predictions and explicit support statuses. Unknown is never zero.

Publication uses a staging sibling directory and a final rename; existing outputs
are refused and inputs are hashed before/after execution. Frozen bundles, original
workbook and identity holds are preserved. Use a fresh run directory after changes.

## Reviewed provenance-cohort models

The contrast feature table contains approved natural-occurrence examples
(target 0) and documented commercial-herbicide manufacturing comparators (target 1).
This is **purposive cohort classification**, not an origin or herbicidal-activity
classifier. Natural occurrence and commercial manufacture are not mutually
exclusive biological properties. No activity-unknown natural compound becomes
an inactive example. The contrast groups require distinct canonical structures.

Run the maintained matched diagnostic workflow on that explicit target:

```bash
uv run --project analysis --locked python analysis/professor_followup.py \
  --features <adoption-directory>/contrast_features.parquet \
  --target provenance_comparator_target --output <new-model-directory>
```

The eight fixed profiles use the same cohort and five scaffold folds. Formula
coefficients, held-out AUROC permutation and forest tree-specific OOB F1
permutation retain their existing contracts. Target 1 now means the commercial
comparator group. Model scores cannot be compared as improvements over the
historical 171-compound task because the cohort and group definitions changed.
OOB repeat SD is not statistical significance or scaffold validation.

The local `notes/notebooks/presentation_essentials.py` learning notebook remains
ignored and uncommitted. New dated findings belong in `analysis/FINDINGS.md` and
the [result inventory](../../docs/results.md); historical findings remain intact.

## Biological descriptors and fixed-cutoff EPA comparison

```bash
uv run --project analysis --locked python analysis/reviewed_progress.py \
  --adoption <adoption-directory> --models <reviewed-cohort-model-directory> \
  --baseline <frozen-weekly-toxicity-directory> \
  --selection <frozen-selection-structural_features.parquet> --output <new-directory>
```

This offline synthesis verifies the upstream manifests, model target, common
held-out cohort/folds, scaffold separation and recomputed scores. Natural activity
is interpreted under K1998 only; other policies remain separate. It compares
individual descriptor values and per-group medians/IQRs for natural active,
natural activity-unknown, explicit empty natural low-response and selected-herbicide
comparator groups. Exact full-key overlaps are excluded from the comparator and
listed. Unsupported/missing values retain their own descriptor denominators.

The EPA baseline is reannotated by exact structural identity. Its observations,
compound medians, censored-only coverage and frozen 1,080/3,400 mg/kg bins are
unchanged. Original groups remain in companion columns. No ECOTOX candidate
identity or duplicate-study decision is inferred from blanket review approval.
The output provides group tables, descriptor and LD50 figures, verified model
metrics and a standalone `walkthrough.html`; publication uses a fresh staged
output directory and preserves all scientific inputs.

The current local bundles are `human-review-adopted-2026-11-11-final`,
`reviewed-cohort-models-2026-11-11-final` and
`human-reviewed-progress-2026-11-11-complete` under `analysis/outputs/`.
The source workbook hash is recorded independently of historical manifests.
All 19 occurrence decisions and 80 policy-specific activity decisions are adopted
under the user's human-review declaration; specific unresolved outcomes prevail.
The new 30-compound cohort task is explicitly supported by the matched model
workflow, which rejects disagreement between its target and declared contrast
group. Historical targets and their existing safeguards are unchanged.

## Explicit ECOTOX identity approval

A separate source-identity declaration is required; biological-label approval does
not automatically approve ECOTOX mappings. The user explicitly approved all 104
frozen ECOTOX mappings on 11 November 2026. `ecotox_approved.py adopt` records that
assertion, binds it to the source snapshot hash and exact selected mapping pairs,
and writes a fresh crosswalk and companion ledger without changing old candidates.

```bash
uv run --project analysis --locked python analysis/ecotox_approved.py adopt \
  --cohort <frozen-cohort-directory> --selected-bundle <frozen-selected-results> \
  --selection <selection-structural_features.parquet> --review <frozen-literature-review> \
  --approval <explicit-ecotox-approval.json> --output <new-identity-directory>
```

The declaration requires `approval_id`, `reviewer`, ISO `review_date`, `statement`,
`snapshot_sha256` and scope `all_selected_ecotox_identity_mappings`. Every selected
source needs exactly one known canonical candidate. Ambiguous/missing candidates,
explicit conflicts, canonical SMILES/key disagreement, duplicate source IDs and
snapshot disagreement fail. Canonical consistency is checked computationally;
source equivalence is recorded as the user's human-review assertion. A salt's
multicomponent status can prevent structural modeling without preventing an
explicitly approved whole-form identity mapping; no salt-parent conversion occurs.

Use the new `approved_crosswalk.csv` and preserved `chemical_ids.csv` with the
maintained `agrotox.ecotox_selected` command. Approval attaches canonical identities
but does not relax species, endpoint, effect, duration, medium, formulation,
concentration-basis, analysis-method or unit requirements. Source result/slot IDs
remain unchanged. Duplicate-study decisions and activity labels are independent.
All new products remain local; historical candidates and frozen bundles persist.

## Identity-approved ecological comparisons

```bash
uv run --project analysis --locked python analysis/ecotox_comparison.py \
  --ecotox <approved-selected-results> --previous <original-candidate-selected-results> \
  --identities <approved-identity-bundle> --adoption <human-biological-adoption-bundle> \
  --selection <selection-structural_features.parquet> \
  --reconciliation <approved-expansion-toxicity-bundle> --output <new-directory>
```

Rerun `expansion_toxicity.py` with the approved selected bundle/crosswalk before
this synthesis to refresh overlap-link status and canonical admission summaries.
Identity approval does not approve any same-observation duplicate decisions.

The comparison requires identical native results and identical scientific
measurement fields before/after approval; only `compound_id` and `identity_status`
may change. Result and slot identifiers must remain unique. Every attached
canonical ID must match the approved source crosswalk. It exports individual
admitted observations with result/test/reference IDs, source locators, qualifiers,
exposure data, control fields and documentation gaps.

**Duration distinction:** the existing core policies use 96-/48-hour *observation*
duration. Exposure duration is separate and often missing. The additional reported-
context subset requires reported exposure type/control type and exposure duration
matching observation duration. It is a documentation check, not proof of study
quality. Empty strata remain empty. pH, temperature, age and other study conditions
are not fully harmonized by these strata.

Record-level exact medians stay within compound, policy, measured/unmeasured
analysis, concentration basis, formulation, exposure type, medium and exposure
duration. Bounds/ranges never become point values and are excluded from exact
medians; repeated source result IDs are not created by joins and different IDs
remain distinct. `all_core_policy_admitted`, the observation export, coverage table
and chart preserve original admissions. `reviewed_duplicate_decisions` applies
signed `same_observation` exclusions from the reconciliation queue. All other
sensitivities apply those exclusions too, and may additionally exclude unresolved
overlap candidates and/or retain only the reported-context subset. A signed
`different_observation` removes a pair from the pending set without dropping either
observation. The comparison revalidates queue decisions and fails on unsigned
same/different decisions, unapproved identity collapses or contradictory retention.
The manifest lists aquatic excluded measurement IDs and their count; it does not
claim records were removed from frozen source data. Rebuild reconciliation with
`expansion_toxicity.py --decisions` to adopt review fields before this analysis;
old queues do not contain decisions that were previously lost during export.
No endpoint pooling or new activity labels/model
fitting occurs. The 16 rat LD50 records are exported as a separate context-review
queue; identity approval does not admit them to the frozen rat oral baseline.

Current local bundles are `ecotox-identities-approved-2026-11-11`,
`ecotox-selected-approved-2026-11-11`,
`ecotox-approved-reconciliation-2026-11-11` and
`ecotox-approved-comparison-2026-11-11-verified`. All original source/label/result
bundles remain intact. The new native CSV/Parquet and dictionary files have the
same bytes as the original exports; verified identical immutable copies share
filesystem storage to avoid duplicating roughly 770 MB. All paths and manifest
hashes remain unchanged by that storage deduplication.

All 104 source mappings are approved, but only 103 have result records.
Acacetin (`ECOTOX:chemical:480444` / `PUBCHEM:5280442`) has zero results in the
frozen snapshot and remains an assessed zero in source coverage. The reconciliation
manifest’s `approved_ecotox_identities` counts observed canonical IDs (103), not
the full approved crosswalk (104). Zero coverage supplies no safety/activity label.

## Source-linked aquatic context overlays

`context_overlay.py` creates a separate versioned context sensitivity from an
existing comparison bundle. Native source exports, concentrations, qualifiers,
identities, original core admission and rat LD50 estimates remain unchanged.
Run from the repository root with a fresh output directory:

```bash
uv run --project analysis --locked python analysis/context_overlay.py \
  --comparison analysis/outputs/EXISTING_COMPARISON \
  --overlays YOUR_WORK/context_decisions.json --sources YOUR_WORK/sources \
  --mode reviewed --output analysis/outputs/NEW_CONTEXT_RUN
```

The evidence directory needs `sources.json`, a list of records with unique
`source_id`, `reference_number`, `kind`, relative `file` and lowercase SHA-256
`sha256`. Kinds are `primary_fulltext`, `primary_abstract`, or `secondary`.
Every file must resolve inside that directory and match its hash. Source kind,
authenticity and reviewer identity are caller assertions; hashes verify bytes,
not scientific conclusions. The source reference must match each observation.

The overlay JSON is a list of decisions. Every decision requires
`measurement_id`, `field`, `original`, `proposed`, `status`, `review_level`,
`source_id`, `source_locator`, `rationale`, `reviewer` and ISO `review_date`.
`original` must match the frozen comparison's field value (null for absent
metadata). Allowed fields are `exposure_type`, `exposure_hours`, `medium`,
`control_type_raw`, `initial_ph` and `temperature_c`. Numeric proposals must be
finite; hours positive; pH within 0–14; text proposals nonmissing. Raw values,
units, duration of observation, endpoints and identities cannot be edited.

Statuses are `verified_from_primary_source`, `provisional`, `not_reported`,
`access_gap`, `ambiguous` or `contradiction`. Review levels are
`scientific_review` and `AI_experimental`. In default **reviewed** mode only
verified full-text decisions with scientific review apply. **Experimental** mode
also allows explicitly provisional primary full-text/abstract evidence and AI
review. Secondary evidence never applies. Unresolved/contradictory decisions
remain in the audit and never change context. An abstract cannot be marked as
verified primary full-text evidence. This mode distinction supports authorized
experiments without presenting AI proposals as independent scientific review.

Duplicate measurement/field decisions, stale original values, orphan IDs and
nonmissing native disagreements fail. A contradictory proposed value can instead
be retained with status `contradiction` for further review. Test-level changes
require explicit consistent decisions for every admitted slot sharing that test;
there is no implicit last-write-wins or hidden propagation.

Outputs are a byte-identical `original_aquatic_observations.csv`, separate
`source_adjudicated_observations.csv` with original-context JSON and applied-field
names, `context_decisions.csv` with per-field status/provenance/application flags,
`coverage.csv`, within-context summaries and a hashed manifest. Original and
source-adjudicated all-core/reported-context scenarios remain separately named.

The reported-context calculation still checks presence of exposure type, control
type and exposure duration matching observation duration. In experimental mode
this is conditional on the explicitly provisional overlay assumptions, not new
proof of protocol adequacy or verified exposure. Initial pH/temperature metadata
are retained in observations but do not automatically enter the existing strata;
those summaries still do not harmonize all study conditions. This standalone
comparison does not adopt duplicate exclusions, promote new core records or admit
rat cases; use the separate duplicate-review workflow for that sensitivity.

Focused checks:
`uv run --project analysis --locked pytest analysis/tests/test_context_overlay.py -q`.
