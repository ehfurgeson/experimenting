# Research scope and interpretation

Maintained research context, reviewed 2026-11-02. [GOALS.md](../GOALS.md) remains
the authoritative, unchanged research direction. Implementation status lives in
[project state](project-state.md); this document records the questions and limits.

## Questions that guide the work

| Workstream | Question | Evidence needed |
| --- | --- | --- |
| Toxicity profiles | How do synthetic herbicides and natural products differ under comparable endpoint/species/route/duration conditions? | Curated identities, source-linked observations, qualifiers and comparable study context |
| Differentiating properties | Which composition, structural and physicochemical properties distinguish the selection or relate to reviewed biological outcomes? | Declared target and cohort; structural validation; independent outcome labels |
| Evidence availability | Are apparent group differences explained by what was studied or extracted? | Assessed-source status, full denominators, missingness and source audits |
| Binding interactions | Which natural products have known protein interactions, and under which conditions? | Defined compound/protein identities, cited binding measurements and experimental context |
| Safer bioherbicides | Which candidates warrant further experimental examination for useful weed activity and lower non-target hazard? | Reviewed efficacy plus separate hazard profiles, uncertainty and exposure context |

The original HRAC Group 1/2 focus and four requested natural products motivated
the prototype. The inspected selection now spans more herbicide classes and
natural-product candidates. Historical source curation listed 188 candidates;
that is not the current 178-row input file or 176-row prepared cohort. See
[compound provenance](../CURATED_COMPOUNDS.md) and [evidence](evidence-and-identities.md).
Selection group names are not an independently verified natural-origin/activity label set.

## Scientific interpretation

Natural origin does not establish safety. Hazard under a test condition is not
risk without exposure, application, formulation and environmental context.
Missing evidence, unapproved identity and tested inactivity are different states.
PubChem annotations are not uniformly independently verified experimental studies.

Endpoint names alone do not establish comparability. Species, route, duration,
effect, life stage, material and benchmark/model context can change meaning.
Preserve qualifiers, ranges and uncertainty. Parent compounds, salts, isomers,
mixtures, extracts and formulations cannot be casually merged.

Repeated database rows or publications do not automatically constitute independent
studies. Avoid allowing heavily studied compounds to dominate group comparisons.
The pipeline's consolidation preserves supports for equivalent records; it does
not solve all publication-level deduplication. Purposive compound selection,
unequal testing and unadjusted multiple comparisons limit broader inference.

Selection discrimination, in-vitro assay activity, measured binding and whole-organism
toxicity answer different questions. Formula features cannot distinguish isomers;
protein conservation can motivate a cross-reactivity hypothesis but does not prove
binding, selectivity or toxicity. Model extrapolation needs chemical-space context,
external validation and calibration appropriate to its intended use.

## Methods and deliverables

The implemented stack uses Python/Unix, Polars, statistical summaries, RDKit,
scikit-learn and a marimo presentation. Large language/protein language models
are research methods named in the goals; no validated workflow using them is
established by the current implementation. Their use should answer a defined
research question with traceable evidence and validation.

Maintain analyzed datasets with manifests, computational workflows with explicit
inputs and a presentation that labels what is measured, inferred and unresolved.
Do not compress efficacy, hazard, missingness and uncertainty into an unsupported
single safety ranking.
