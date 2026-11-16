# Endpoint policies and comparisons

[Component quickstart](../README.md) · [Repository documentation](../../docs/README.md)

Commands below run from the `pipeline/` directory. Real-data examples require the local inputs described in the [data guide](../../docs/data.md).

## Shared endpoint policy

`agrotox.endpoints.ENDPOINT_UNITS` maps acute endpoints to their standard
units: LD50 uses `mg/kg`, while LC50 and EC50 use `mg/L`.
`POINT_OF_DEPARTURE_UNITS` maps NOAEL, LOAEL, BMD, and BMDL to their allowed
`mg/kg` and `mg/kg-day` units. Both mappings are read-only. Definition matching,
EPA hazard eligibility, and unit conversion share these policies; PubChem
annotation extraction consults the acute policy only.

An entry describes endpoint/unit support, not study comparability. Source label
recognition, explicit context requirements, and conversion rules still apply;
adding an entry alone does not implement a new endpoint end to end. Unsupported
definitions raise `ValueError`; unsupported unit conversions return
`(None, None)`.

Run the focused checks with `uv run pytest tests/test_units.py tests/test_definitions.py tests/test_matching.py tests/test_normalize.py tests/test_epa_hazard.py -q`.


## Point of departure comparisons

NOAEL, LOAEL, BMD, and BMDL definitions require an explicit `standard_unit`
(`mg/kg` or `mg/kg-day`). Matching also requires `evidence_basis` to be
`observed` for NOAEL/LOAEL or `model_derived` for BMD/BMDL. Reported qualifiers
are preserved: an exact NOAEL or BMDL is not rewritten as an inequality.

These definitions default to `summary_mode: availability`: comparison records
and exact/censored/range counts remain available, while medians/minima/maxima
stay null. Records expose this choice as `summary_eligible`. Acute definitions
retain their default `summary_mode: potency`; either mode can be set explicitly.

A point of departure definition requesting `summary_mode: potency` must specify
`species`, `preferred_route`, `preferred_duration_hours`, `study_type`, and
`effect`. BMD/BMDL also require `benchmark_response`, `benchmark_response_type`,
and `model_name`; BMDL additionally requires `confidence_level`. Invalid or
incomplete policies raise `ValueError`. Every configured field must match the
observation, so a missing duration or unknown benchmark interpretation cannot
silently enter a potency summary. These requirements constrain comparisons;
they do not establish study quality or justify a safety conclusion. A BMDL
summary describes reported lower bounds, not BMD point estimates.

Run the focused checks with `uv run pytest tests/test_pod_comparisons.py -q`.


## Endpoint definitions and matching

`agrotox.coverage.load_definitions(path)` loads a nonempty YAML mapping of named
policies. `validate_definitions(mapping)` validates an in-memory mapping and
returns an independent copy. Invalid YAML, duplicate keys, unknown fields, and
invalid policy values raise `ValueError`; file I/O errors propagate.

Every policy requires `endpoint` (`LD50`, `LC50`, `EC50`, `NOAEL`, `LOAEL`,
`BMD`, or `BMDL`). Optional matching
fields are `organism_group`, `species`, `preferred_route`,
`preferred_duration_hours`, and `standard_unit`. Durations must be positive finite
numeric hours; units must be canonical and endpoint-compatible (`mg/kg` for LD50,
`mg/L` for LC50/EC50). String fields must be nonempty. `endpoint_family`, `label`,
and `context_note` are display metadata and do not affect matching. Context names
use the canonical normalized spelling; definitions do not normalize aliases.

`matches(record, definition)` checks one row. `matching_expr(definition)` builds
the same predicate for a normalized Polars measurement table:

```python
from agrotox.coverage import load_definitions, matching_expr

rules = load_definitions("tests/fixtures/comparisons.yaml")
selected = measurements.filter(matching_expr(rules["trout_96h"]))
```

Matching requires a complete, explicitly non-formulation row with a compatible
standardized unit and a positive finite scalar/threshold or ascending pair of
range bounds. Ranges must have a null scalar; scalar results must have null range
bounds. Qualifiers retain their meaning. Missing values and invalid numeric
shapes are ineligible. The row helper rejects malformed field types; the
expression expects normalized measurement columns and their declared types.

Every configured context is a required equality. In particular, `preferred_*`
does not supply a default: absent route or duration fails a rule that requires
it. Unconfigured context can remain missing. Thus a fish LC50 row can satisfy a
broad fish rule while failing a rainbow-trout 96-hour comparison. Neither API
changes rows or fills context from policy metadata.

Small synthetic policies are in `tests/fixtures/endpoints.yaml` and
`tests/fixtures/comparisons.yaml`. Run focused checks with
`uv run pytest tests/test_definitions.py tests/test_matching.py -q`.


## Compound endpoint coverage

`agrotox.coverage.coverage_tables(compounds, measurements, definitions)` returns
two Polars tables. The matrix retains `compound_id`, `input_queries`, and
`chemical_group`, followed by one Int64 binary column per named policy. A one
means at least one eligible annotation, including valid thresholds and ranges.
Repeated annotations and aliases cannot increase a compound's availability.

The group table contains `chemical_group`, `endpoint` (the policy name),
`compounds_with_data`, and `total_compounds`. Denominators come from the selected
compound universe, including unresolved queries and resolved compounds with no
matching evidence. Null groups and groups with zero matches remain present.
Identical duplicate compound rows collapse; conflicting duplicate identities,
null IDs, invalid schemas, orphan measurements, and policy names colliding with
matrix identity columns raise `ValueError`. Reconcile aliases before counting.
Empty inputs retain typed columns, and neither input table is modified.

For a hands-on demonstration, run the scripts in `examples/`. They cover
retrieval, offline inspection, and matching evidence, with reproducible
commands.


## Comparison records

`agrotox.analysis.comparison_records(measurements, definitions)` returns one
Polars table of comparable records. Eligibility is shared with
`agrotox.coverage.matching_expr`, so a record exists only where a configured
comparison applies.

Records consolidate by comparison, compound, endpoint, species, exposure route,
duration, standardized unit, qualifier, and the standardized value or bounds.
Equal values from different studies collapse into one record that keeps
`support_ids` (unique annotation identifiers), `support_count`, and `supports`,
a nested list of the original value text and source reference for every
supporter. Thresholds and ranges keep their own qualifiers and are never
reclassified as exact values. `organism_group` is not part of the consolidation
key, because a definition that constrains it already fixes that value.

Consolidation is equal-value consolidation. It is not evidence of independent
studies, and repeated observations are not removed. Records are ordered by
definition order and then by the consolidation fields, so the same inputs always
produce the same rows. Missing required measurement columns and null compound
identities raise `ValueError`.

Run the focused checks with `uv run pytest tests/test_comparisons.py -q`.


## Compound and group summaries

`agrotox.analysis.compound_summaries(records)` returns one row per compound
and comparison: `n_records`, `n_exact`, `n_censored`, `n_ranges`, and the
`exact_median`, `exact_min`, and `exact_max` of the consolidated exact
results. Thresholds and ranges are counted separately and never enter the
median. A compound with many studies contributes one summary row.

`agrotox.analysis.group_summaries(summaries, compounds, definitions)` describes
each comparison and chemical group: `total_compounds`,
`compounds_with_data`, `compounds_with_exact`, `compounds_with_censoring`,
`compounds_with_ranges`, and the `median_of_compound_exact_medians` with its
minimum and maximum. Every observed group appears for every comparison,
including unexpected groups and groups with no matching evidence, and the
denominators come from the selected compound universe. The group median is the
median of compound medians, so a heavily studied compound cannot dominate the
group description. A group with no exact values keeps a typed null median.

`agrotox.analysis.comparison_tables(compounds, measurements, definitions)`
returns the records, compound summaries, and group summaries together.
Conflicting duplicate compound identities raise `ValueError`.

Run the focused checks with `uv run pytest tests/test_comparisons.py -q`.


## Extraction audit and review queue

`agrotox.analysis.extraction_audit(compounds, annotations, measurements, records)`
returns one row per selected compound with the counts of saved annotations,
complete, partial, and failed measurements, the number of comparison records,
and an `availability_reason`. The reasons are applied in a fixed order: an
unresolved query, an unfinished or failed toxicity request, an absent toxicity
section, an empty saved section, no supported complete measurement, complete
measurements outside every comparison context, and finally comparable data.
The first applicable reason explains the compound, so a compound that is both
unresolved and pending is reported as unresolved.

These states describe PubChem retrieval. They are not a general statement
about a chemical, and "no comparable data" never means "no hazard".

`agrotox.analysis.review_queue(measurements)` returns the partial and failed
measurement rows with their parse notes and full source provenance, so a
reviewer can read the original evidence beside the reason extraction did not
succeed. Complete rows are excluded.

Run the focused checks with `uv run pytest tests/test_audit.py -q`.


## Offline workflow

`agrotox.workflow.build_offline(root, queries, definitions)` composes every
analysis table from the selected snapshots and returns an `OfflineAnalysis` with
the named tables and the raw files they were built from.

The tables are `compounds`, `annotations`, `measurements`, `coverage`,
`coverage_by_group`, `comparison_records`, `compound_summary`, `group_summary`,
`audit`, and `review_queue`. The same selection, evidence, and definitions
always produce the same rows, and the composition makes no network request.

`analysis.dependencies` maps every consumed raw file to its SHA-256 digest, so a
manifest can record exactly which evidence produced a result. The workflow only
reads: it never writes to, moves, or refreshes the raw cache. A pending bundle
contributes its identity and its properties, but its toxicity file is not read
and is not listed as a dependency.

A selected query without a saved alias still belongs to the compound universe
as an unresolved identity, so the denominators keep it while the evidence
tables stay empty for it. Unselected cached records never enter the output.

Run the focused checks with `uv run pytest tests/test_workflow.py -q`.
