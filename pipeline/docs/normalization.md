# Normalization and study context

[Component quickstart](../README.md) · [Repository documentation](../../docs/README.md)

Commands below run from the `pipeline/` directory. Real-data examples require the local inputs described in the [data guide](../../docs/data.md).

## Study and benchmark context

Normalized measurements, EPA comparison inputs, and consolidated comparison
records retain nullable string fields for `study_type`, `duration_class`,
`effect`, `evidence_basis`, `benchmark_response`, `benchmark_response_type`,
`model_name`, `model_id`, `confidence_level`, and `study_id`. Definition fields
with these names require exact matching values; missing values fail configured
equalities. Numeric response and confidence text retains the source's spelling
and scale rather than assuming percentages or fractions.

Consolidation keeps differing study or benchmark context in separate records.
PubChem extraction currently leaves these fields null. Tables saved under an
older schema must be regenerated before reading with the expanded measurement
or comparison-record schema; acute coverage still accepts the original minimal
comparison input when no extra context is configured.

Run the focused checks with `uv run pytest tests/test_comparisons.py -q`.


## Units and durations

`agrotox.units.normalize_unit(unit, endpoint, medium = None)` returns a standard
unit and multiplier. It does not extract numbers from text or infer context.

For NOAEL, LOAEL, BMD, and BMDL, mass doses convert to `mg/kg`; explicitly
daily doses convert to `mg/kg-day`. Supported daily spellings include
`mg/kg-day`, `mg/kg/day`, `mg/kg/d`, `mg kg-1 day-1`, and `mg/kg bw/day`,
with g/mg/ug and Unicode microgram variants. A daily dose is never converted
to a total dose. Concentrations, ppm, and weekly doses remain unsupported
for these endpoints and return `(None, None)`. Source extraction requires its
own endpoint recognition rules.

| Endpoint | Accepted mass/denominator | Standard unit | Multipliers for g / mg / ug |
| --- | --- | --- | --- |
| LD50 | g/kg, mg/kg, ug/kg | mg/kg | 1000 / 1 / 0.001 |
| LC50, EC50 | g/L, mg/L, ug/L | mg/L | 1000 / 1 / 0.001 |

Both `µg` and `μg` mean micrograms. Case and whitespace variants and equivalent
inverse-denominator spellings such as `mg kg-1` and `mg L-1` are accepted. Explicit
trailing `bw` or `body weight` is accepted for dose units. Dose/concentration
mismatches and unsupported units return `(None, None)`.

Ppm converts to mg/L only for LC50/EC50 with an explicit `water` or `aqueous`
medium. This is an approximation for a dilute solution with density near 1 kg/L,
not a general ppm conversion. Air, seawater, unknown media, and organism labels
do not enable it. No molecular-weight-based or gas conversions are implemented.

`duration_hours(value, unit)` converts numeric hours (`h`, `hr`, `hrs`, `hour`,
`hours`), days (`d`, `day`, `days`) or weeks (`wk`, `wks`, `week`, `weeks`) into
Float64-compatible hours. A week is seven days (168 hours). Missing values
and unsupported units return `None`. Negative, nonfinite, or overflowing durations
raise `ValueError`; Boolean and nonnumeric values raise `TypeError`. Zero remains
zero at this conversion boundary; missing never becomes zero.

Examples: `normalize_unit("μg / L", "EC50")` returns `("mg/L", 0.001)`, and
`duration_hours(4, "days")` returns `96.0`. Run the focused checks with
`uv run pytest tests/test_units.py -q`.


## Numeric values and uncertainty

`agrotox.normalize.parse_value(text)` returns a `ParsedValue` record for one
positive finite numeric result with a supported unit, or `None` when extraction
is invalid or ambiguous. It retains the raw unit and does not convert values.

| Text | Qualifier | Scalar | Lower bound | Upper bound |
| --- | --- | --- | --- | --- |
| `560 mg/kg` | `=` | 560 | null | null |
| `≥1e3 mg/kg` | `>=` | 1000 | null | null |
| `3–5 mg/L` | `range` | null | 3 | 5 |

The record fields are `value_numeric`, `value_lower`, `value_upper`, `qualifier`,
and `unit_raw`. ASCII inequalities and Unicode `≤`/`≥` retain their thresholds.
Ranges use a shared trailing unit and an ascending pair separated by a hyphen,
en dash, em dash, or `to`. No midpoint or bound becomes an exact scalar.

Supported numeric notation includes properly grouped thousands commas, decimal
points (including `.5`), and scientific exponents. Endpoint labels and explicit
hour/day/week durations can accompany a result; other unconsumed numbers cause
rejection. Numeric boundaries prevent unsigned substrings of negative or
malformed values from being selected.

Zero, negative/nonfinite values, overflow/underflow to zero, reversed/equal ranges,
competing values, approximation prose, and error-bar notation return `None`.
Unsupported verbal comparisons such as `less than` also return `None`, rather
than becoming exact values. Unary plus signs and inequality-prefixed ranges are
unsupported. Missing text returns `None`; nontext inputs raise `TypeError`.

Run focused checks with `uv run pytest tests/test_values.py -q`. This helper
extracts numeric expressions; annotation context and parse-status assignment
are handled separately by `normalize_annotation`.


## Annotation normalization

`agrotox.normalize.normalize_annotation(annotation)` returns one row retaining
all source fields, with endpoint, species/group, exposure route, duration,
medium, numeric values, standardized units/values, formulation flag, status,
and review notes. It does not modify the input or consult comparison definitions.

- `complete`: one supported endpoint and a valid compatible conversion, with no
  detected ambiguity or formulation context. Optional context may remain null.
- `partial`: a supported endpoint is present, but the value, conversion,
  attribution, or context requires review.
- `failed`: no supported endpoint can be identified. The annotation remains
  available, with its source evidence and review reason.

Context comes from section headings, Information name/description, and raw value
text. Chemical titles, compound metadata, reference names, and serialized metadata
do not supply context. Specific trout/minnow/Daphnia aliases override generic
names. Conflicting species, routes, durations, endpoints, or media remain partial,
with ambiguous fields left null. Missing or unrecognized species/route alone can
still accompany a complete numeric extraction; nothing defaults to rat, oral,
96 hours, or water.

A single `Concentration:` field isolates the value and duration until the next
semicolon or opening parenthesis, excluding age, hardness, and confidence-interval
numbers. Multiple or empty concentration fields cannot fall back to ancillary
values. Explicit age and follow-up/observation periods are not exposure durations.
Equivalent explicit durations such as four days and 96 hours agree; conflicting,
nonpositive, nonfinite, or unsupported exposure durations require review.

Numeric arrays, unfamiliar value shapes, formulations/mixtures/extracts, and
unstructured multi-sentence or interaction evidence cannot become complete
measurements. Scalar thresholds and both range bounds use the same conversion
factor. Conversion overflow or underflow leaves standardized quantities null.
`complete` describes extraction, not study quality, safety, or independent studies.

`normalize_rows(annotations, compounds)` applies the same rules and joins selected
compound metadata by ID, returning one typed row per annotation in source order.
It preserves structured provenance and noncolliding extra annotation columns.
Missing compound identities, duplicate compound rows, malformed schemas, and
columns colliding with derived fields raise errors. Empty inputs retain the
measurement schema, including Float64 values and Boolean formulation flags.

Run focused checks with `uv run pytest tests/test_normalize.py -q`. The synthetic
integration produces seven rows: five complete, one partial array, and one failed
narrative. Saved real-cache observations are recorded in the
[normalization checkpoint](live_retrieval_check.md#offline-annotation-normalization).
