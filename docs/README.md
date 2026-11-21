# Documentation index

Use this index for maintained guidance. Dated records explain a particular run;
their test counts and results are historical observations.

| Audience / task | Current guide |
| --- | --- |
| New collaborator | [Project overview](../README.md), [component architecture](architecture.md) |
| Pipeline developer | [Setup and minimal example](../pipeline/README.md), [inputs/identity](../pipeline/docs/inputs-identity.md), [retrieval/cache](../pipeline/docs/retrieval-cache.md) |
| Evidence analyst | [Normalization](../pipeline/docs/normalization.md), [endpoint comparisons](../pipeline/docs/endpoints-comparisons.md), [EPA/ChEMBL](../pipeline/docs/epa-chembl.md) |
| Research analyst / presenter | [Analysis quickstart](../analysis/README.md), [cached analysis](../analysis/docs/cached-analysis.md) |
| Catalog screening and model review | [Joint screen](../analysis/docs/joint-catalog-screen.md), [notebook and full rebuild](../analysis/docs/joint-catalog-notebook.md) |
| Separate measured / modeled toxicity | [A/B protocol and release workflow](../analysis/docs/modeled-evidence.md) |
| New source evidence and natural-product overlap | [Data-first sprint](../analysis/docs/data-sprint.md) |
| Accepted-data experimental continuation | [Accepted sprint cohorts and experiments](../analysis/docs/accepted-sprint.md) |
| Structure analyst | [Screening and labels](../analysis/docs/structural-screening.md), [stress/ablations/review](../analysis/docs/diagnostics-review.md) |
| Protein-interaction analyst | [Experimental structural-evidence pilot](../analysis/docs/binding-evidence.md): exact ligand/form and deposited protein checks; no affinity inference |
| Toxicity source reviewer | [Experimental rat-source checkpoint](../analysis/docs/rat-source-review-2026-11-12.md): primary result mapping, dose basis, overlap decisions and unresolved source contradictions |
| Human label reviewer | [Researcher label guide](../analysis/docs/label_review_guide.md) |
| Data custodian | [Data conventions and bootstrap](data.md), [source catalog](references.md), [frozen results](results.md) |

## Scientific contracts and rationale

- [Pipeline decisions](../pipeline/docs/decisions.md): identity, missingness, evidence classes, context matching, provenance and analysis boundaries.
- [Analysis decisions](../analysis/docs/decisions.md): chemistry, independent origin/activity labels, scaffold validation and diagnostic controls.
- [Table/provenance contract](../pipeline/docs/tables-provenance.md): typed products and dependency hashes.
- [Shared endpoint configuration](../pipeline/examples/endpoints.yaml): executable research policies; its location under examples does not make it disposable.

## Dated findings and checks

- [Findings by checkpoint](../analysis/FINDINGS.md): start at the pointer for the question being asked.
- [Structural validation, 2026-10-28](../analysis/docs/structural_validation_check.md).
- [Feature combinations, 2026-10-29](../analysis/docs/feature_combination_check.md).
- [Compound expansion evidence](../analysis/docs/compound_sources.md): checked sources supporting the selection.
- [Separate A/B modeled evidence, 2026-11-12](../analysis/docs/modeled-evidence-2026-11-12.md): broad source-first release, separate evaluations and teacher-overlap limits.
- [Experimental expansion, 2026-11-12](../analysis/docs/experimental-expansion-2026-11-12.md): permissive assay-pooling experiment, source transcription and failed publication transfer; separate from accepted labels.
- [Live retrieval checkpoint](../pipeline/docs/live_retrieval_check.md) and [point-of-departure checkpoint](../pipeline/docs/point_of_departure_check.md): dated evidence checks, not clean-clone fixtures.

## Historical and local material

The [prototype status](../prototype/README.md) describes the earlier retrieval
implementation. The [data guide](data.md) lists inputs for current and
historical workflows.
