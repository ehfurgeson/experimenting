# Agrochemical toxicity: current research overview

Updated **2026-11-12**. [GOALS.md](GOALS.md) remains the unchanged research compass:
compare synthetic-herbicide and natural-product toxicity profiles, identify
properties that distinguish them, and characterize known natural-product–protein
binding interactions toward safer bioherbicide discovery.

The [new modeled-evidence handoff](handoffs/modeled-evidence-2026-11-12/README.md)
defines broad collection, separate experimental/external-estimate analyses and
modeling, then a later decision on combining them. The current user-authorized
[first A/B release](../analysis/docs/modeled-evidence-2026-11-12.md) now implements
a collection pass and separate fixed evaluations; combined C is deferred. The
[experimental notebook](notebooks/evidence_experiments.py) explores saved
model scores, logistic weights and forest OOB diagnostics in live marimo.
This planning update does not resume the paused research goal.

## Current state

The maintained `pipeline/` package retrieves and processes PubChem, EPA and bounded
ChEMBL evidence with explicit identities, endpoint context and provenance.
Maintained `analysis/` workflows rebuild cached evidence products, support the
marimo presentation, compute structural features, evaluate scaffold-held-out
selection models, run diagnostics and prepare human label review.

The inspected local prepared cohort has **176 compounds** (60 selected herbicides,
116 selected natural products); the input selection has 178 rows. The EPA crosswalk
has 136 approved, 24 review and 16 unresolved identities. The historical 154-row researcher
handoff copy is preserved with unknown labels. A new human-adopted bundle now
records 19 natural-occurrence labels and 80 activity decisions under four separate
policies; within-policy scaffold/class support still prevents activity modeling.
All 104 selected ECOTOX mappings are explicitly human-approved in a separate
versioned source crosswalk; ecological exposure/context documentation remains
limited. A separate 30-compound reviewed-cohort structural comparison is available; see
[human review adoption](../analysis/docs/human-review.md).

Evidence availability, measured toxicity, selection classification, reviewed
herbicidal activity and protein binding answer different questions. The project
has not established an accepted real activity model, safer candidates or a
validated binding-affinity predictor. A two-complex structural-evidence pilot now
exists; broader binding characterization remains an explicit research objective.
A heterogeneous activity experiment fit but failed transfer to new studies.
The local TEST cache already contains2,176 external-estimate records for136
compounds; a full separate predicted-toxicity analysis remains planned. The
reviewed experimental work is integrated into local main, with verified local
preservation and no push. See the linked checkpoint guides for scientific limits.

## Maintain the topic files

| Topic | Where to read / update |
| --- | --- |
| Implemented capabilities, local counts and dated checkpoint map | [Project state](current/project-state.md) |
| Research questions, scope and scientific caveats | [Research context](current/research-questions.md) |
| Compound identity, sources, endpoints and missingness | [Evidence conventions](current/evidence-and-identities.md) |
| Structural selection models and reviewed activity | [Structures and activity](current/structure-and-activity.md) |
| Known natural-product–protein interactions | [Binding and targets](current/binding-and-targets.md) |
| Remaining scientific work and dependencies | [Next steps](current/next-steps.md) |
| Setup, checks and workflow boundaries | [Development](current/development.md) |
| Terminology | [Glossary](current/glossary.md) |

Implementation commands and normative contracts stay in the tracked
[documentation index](../docs/README.md). Local notes should link to those
contracts rather than copy them. Real research inputs/results remain ignored;
a fresh clone alone cannot reproduce the local scientific runs.

## Provenance and working conventions

The [pre-split source](archive/sources/research-notes-2026-11-02.md) is retained for compound
curation's original line citations. The [notes index](README.md) lists current
guidance and provenance. Dated reports and historical sources live in the
[archive](archive/README.md).

Every agent must read [agent orientation](AGENTS/README.md), follow the
[incremental guide](INCREMENTAL_COMMIT_GUIDE.md) and update the
[owning documentation](AGENTS/DOCUMENTATION.md) as part of its work. Keep this
overview short and update the relevant topic when the underlying facts change.
