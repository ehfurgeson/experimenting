# Next research steps and dependencies

Reviewed 2026-11-02. This is the maintained roadmap, not an instruction to rerun
old implementation plans. Priorities follow [GOALS.md](../GOALS.md); changing
research scope requires an explicit scientific decision, not a documentation edit.

| Next deliverable | Dependency / acceptance evidence | Current status |
| --- | --- | --- |
| Reviewed activity and origin labels | Agree biological policy, review original assays/publications, retain citations/context/conflicts, validate worksheet schema | Handoff materials exist; inspected 154-row working copy remains all unknown |
| Known natural-product–protein interaction pilot | Declare a compound/target subset, resolve identities, distinguish direct binding from functional activity, retain primary evidence and review state | Reference tables/context exist; reviewed interaction table/workflow remains proposed |
| Broader comparable aquatic evidence | Define species/endpoint/duration policies and select traceable source records; validate identities, units and qualifiers | Sparse current fish/Daphnia evidence; no configured algal comparison; a dedicated aquatic integration remains open |
| Reproducible collaborator input bundle | Version curated selection/classes/crosswalk/labels with raw snapshots and manifests; document authorized transfer and backup ownership | Full bundle is local/ignored; no documented shared distribution or verified backup arrangement |
| Independent model validation | Adequate positive/negative scaffold support, publication/chemical holdouts, calibration and applicability-domain assessment | Selection diagnostics implemented; accepted real activity model still absent |
| Candidate prioritization / final presentation | Reviewed efficacy plus distinct non-target hazard and uncertainty; versioned evidence and clear unsupported states | Notebook/workflows available; safer candidates and final research conclusions remain unestablished |

## Separate A/B release and next source work — 12 November 2026

The [handoff](../handoffs/modeled-evidence-2026-11-12/README.md) now has a first
user-authorized [collection/evaluation checkpoint](../../analysis/docs/modeled-evidence-2026-11-12.md).
Separate A/B releases, fixed models, TEST coverage expansion and training-overlap
comparison are complete for this pass. The comparison bundle's `summary.json`
owns the backlog. Prioritize original-study/tested-form and archive/API-scale
qualification, the two dietary identity reviews, unresolved dietary structures,
additional provider routes and remaining primary aquatic/plant series. The
original TEST cache remains frozen; new union coverage is 173 full structures.
C is deferred because 3,359 of 3,361 paired structures carry teacher-training
tags. These are provisional AI results, not human scientific adoption or resumed
recurring autonomous-goal execution.

## Existing implementation

PubChem acquisition, acute prose normalization, compound identities, EPA integrations, seven-endpoint
structured support, cached analysis, notebook, structural features/scaffold models,
stress/ablations, frozen assay review and researcher handoff materials already
exist. [Project state](project-state.md) separates those implementations from
unmet scientific data/validation needs.

## Deliberately separate engineering follow-ups

The [ECOTOX ingestion plan](ecotox-ingestion-plan.md), prepared 2026-11-05,
specifies an offline-first bulk-snapshot adapter, source-first chemical inventory,
identity review, conservative normalization and staged verification. It is a
proposed pipeline expansion supporting the two research tracks; ECOTOX ingestion
now has a verified source-inventory prototype (10 November 2026): the official
archive/schema were inspected, core relationships validated, and 100 raw samples
exported. Full measurement ingestion remains proposed. See the tracked
[pilot findings](../../analysis/FINDINGS.md#weekly-two-track-pilots--2026-11-10)
and [preflight contract](../../pipeline/docs/epa-chembl.md#ecotox-bulk-inventory-preflight)
before adding normalization or download automation.

Promote preparation tools individually if clean-clone acquisition is needed;
the cached rebuild intentionally does not retrieve missing data. Preserve manual
curation and identity decisions before designing a new bootstrap command.

Package analysis, relocate references/tests or change manifest portability only
when there is a concrete benefit and compatibility plan. Documentation navigation
now supplies the first organization improvement. Do not delete scientific caches,
rename frozen bundles or merge lockfiles merely to reduce directory count.

Bulk natural-product imports and broad candidate scoring depend on source/version
review and supported reviewed activity models. Do not label all imported natural
products inactive or treat source selection as verified origin/activity.

## Recording progress

When a deliverable advances, update its status with the exact input/label policy,
manifest, reviewed source and dated result. Add a checkpoint to tracked findings
when warranted, then update the current summary rather than editing old delivery
figures. See [documentation responsibilities](../AGENTS/DOCUMENTATION.md).


## Evidence expansion — 2026-11-11

The [tracked checkpoint](../../analysis/FINDINGS.md#evidence-and-comparable-toxicity-expansion--2026-11-11)
adds a complete 104-source-chemical ECOTOX cohort, explicit aquatic context policies,
81 source/condition observations for all 15 literature leads, proposal/approval
worksheets, source-name structure checks and LD50 sensitivity/reconciliation views.
No canonical ECOTOX identities or biological labels are approved, and no activity
models were fitted. Review the local
`analysis/outputs/expansion-walkthrough-2026-11-11-verified/walkthrough.html`
and its linked worksheets; resolve chemical form, source analytical evidence and
the sarmentine 10/20 mg/mL conflict before accepting labels.

## Local permissive experiment — 2026-11-12

See [experimental checkpoint](../../analysis/docs/experimental-expansion-2026-11-12.md).
The separate local branch tested deliberately heterogeneous activity pooling;
computational five-fold support succeeded but publication transfer failed.
Generic preflight and publication/scaffold-purge diagnostics now exist, and the
handoff's duplicate-review queue propagation gap is fixed. Sixteen primary leads,
eight cached full texts and304 plant/59 other endpoint provisional observations
are in `experiments/bioherbicide-expansion-2026-11-12/`. Accepted human labels and
frozen results are unchanged. Continue with compatible independent assays,
source-context recovery and unresolved structures; do not promote the pooled
sensitivity model to candidate scoring.

### Aquatic context integration — 2026-11-12

The [source-linked overlay reader](../../analysis/docs/human-review.md#source-linked-aquatic-context-overlays)
now supports separate reviewed/experimental context sensitivities without editing
native records. An abstract-derived eight-row initial-pH experiment leaves all41
original observation fields and the zero-trout/one-Daphnia context subset unchanged.
The reader gap is closed for aquatic context fields; source-specific full methods,
result-cell mappings and rat eligibility overlays remain open. The new local
work root is `experiments/aquatic-context-2026-11-12/`.

### Structural binding pilot — 2026-11-12

The [bounded structural-evidence auditor](../../analysis/docs/binding-evidence.md)
now provides two experimental complexes, three protein constructs and source-linked
author contacts. Tentoxin is an exact parent/bound match; cornexistin binds as the
separate diacidUP0. A default cofactor-link mismatch was detected and rejected.
Continue original occurrence/density review and residue-to-sequence/weed-ortholog
mapping before predictive integration. No binding affinity or safety model exists.

### Primary rat-source progress — 2026-11-12

The [source checkpoint](../../analysis/docs/rat-source-review-2026-11-12.md) maps
two 2,4-D cases to primary single-dose oral result cells, with acid-equivalent
basis separate from material tested and native dietary contradictions retained.
Four priority pairs are experimentally different observations, propagated through
the existing importer;22 remain unreviewed. Elapsed weeks now normalize without
inferring acute exposure. Two other source ester conversions are flagged, not
corrected. No historical rat admissions or toxicity bins change. Next review the
remaining14rat cases, explicit administration technique and historical375mg/kg
lineage/basis; do not substitute sensitivity arithmetic for a harmonized comparison.
