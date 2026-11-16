# Natural-product binding and protein targets

Research workstream, updated 2026-11-12. Characterizing known natural-product–protein
binding interactions is an explicit objective in [GOALS.md](../GOALS.md), alongside
toxicity-profile comparison. It remains a substantial scientific workstream.

## What the repository currently provides

The preserved [herbicide target tables](../../herbicide_target_tables/README.md)
contain HRAC target groups, protein names, weed species, protein accessions,
paper DOIs, binding-site/resistance residues and ortholog/Ki fields with incomplete
or placeholder entries. They provide working reference context, not a complete
validated natural-product binding dataset. Source exports retain their original
bytes and known/unknown provenance.

The [literature catalog](../../docs/references.md) supports candidate curation.
ChEMBL plant-assay snapshots preserve molecule structures, measurements and
publication context for activity review. Whole-plant growth inhibition or a
source assay target label alone does not demonstrate direct binding to a specific
protein. A bounded offline [structural-evidence auditor](../../analysis/docs/binding-evidence.md)
now checks declared RCSB complexes, exact parent/bound forms and protein constructs.
Its local pilot contains two complexes, three sequences and source-linked author
contacts, with no Kd/Ki inference. A validated binding predictor or protein-language-
model analysis has not been established.

## Proposed first research deliverable

Define a small, source-reviewed interaction table before attempting predictive
integration. The broader review target remains below; the 2026-11-12 pilot implements the
structural subset under explicit source declarations, with affinity/origin review
still unresolved:

| Information | Review requirement |
| --- | --- |
| Compound | Resolved structure/identifier, salt/stereo/material identity and natural-occurrence citation |
| Protein / organism | Stable accession, species, isoform/construct and sequence/version where supplied |
| Interaction evidence | Direct binding versus functional/enzyme inhibition versus inferred association; do not collapse these |
| Measurement | Reported endpoint (for example Ki/Kd when supplied), value, qualifier, unit and assay conditions |
| Primary support | Paper/DOI, figure/table/record locator, methods and source retrieval/version |
| Review judgment | Confidence, identity/context ambiguity, conflicting evidence and reviewer/date |

Start with a declared compound/target subset and confirm the original publications.
Record unknowns rather than filling empty ortholog/Ki cells from analogy. Preserve
raw references and retain direct measurement separately from database annotations,
docking scores, sequence similarity and language-model predictions.

## Later integration

Reviewed interactions could connect weed targets with crop/non-target orthologs,
resistance residues and toxicity endpoints. Conservation motivates hypotheses
about cross-reactivity; it does not establish selectivity or organism-level hazard.
A joint structure–target–toxicity model requires harmonized identities and
independent validation. Protein/large language models remain possible methods
under the goals, subject to a defined question and evidence-based evaluation.

[Next steps](next-steps.md) keeps this work visible without claiming that the
existing selection classifiers have completed it.
