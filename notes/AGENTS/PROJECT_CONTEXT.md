# Project context for agents

Read the unchanged [goals](../GOALS.md) and [current overview](../notes.md).
The project compares synthetic-herbicide and natural-product toxicity profiles,
identifies differentiating properties and seeks known natural-product–protein
binding interactions toward discovery of safer bioherbicides. Deliverables include
analyzed datasets, computational workflows and a semester presentation.

## Ownership

| Location | Responsibility |
| --- | --- |
| `pipeline/` | Maintained `agrotox` package: acquisition, identity, normalization, endpoint policy, comparisons, audits and provenance |
| `analysis/` | Maintained cached analyses, structural models/diagnostics, assay-review exports and presentation |
| `docs/` | Cross-component architecture, data requirements, reference and result catalogs |
| `notes/current/` | Local current research state, scientific questions, interpretation and next steps |
| `notes/provenance/` | Still-used source curation and ambiguity decisions; not current activity labels |
| `notes/archive/` | Outdated reports, superseded notes and historical citation sources; not current instructions |
| `experiments/` | Ignored local preparation, raw caches and earlier scripts; the cached rebuild does not reconstruct all acquisition/manual curation |

Pipeline and analysis keep separate locked environments. Analysis depends on the
sibling pipeline and currently uses flat script imports. Real-data bundles are
ignored and absent from a clone. See [architecture](../../docs/architecture.md),
[data](../../docs/data.md) and [current project state](../current/project-state.md)
for exact workflows, inventory and checkpoint sources.

## Preserve scientific meaning

Evidence availability, measured toxicity, model-derived BMD/BMDL, stored TEST
predictions, selection membership, reviewed herbicidal activity, natural origin
and protein binding are distinct. Natural origin or missing evidence does not
establish safety. A plant-assay response or strong selection classifier does not
establish direct binding or validated candidate efficacy.

Retain identity, species/route/duration, units, qualifiers, evidence class and source
provenance. Unknown assessment/labels remain unknown; they are not zero toxicity
or tested inactivity. Preserve source exports, raw snapshots, reviewed labels and
frozen manifests. Use fresh result directories and explicit inputs for new runs.
Known binding characterization and independent activity validation remain research
workstreams; use [next steps](../current/next-steps.md) for current dependencies.
