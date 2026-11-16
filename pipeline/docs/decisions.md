# Design decisions

Topic index (policy rationale; workflow commands live in the component guides):

- [Queries and resolved compounds](#queries-and-resolved-compounds)
- [Curated metadata and evidence](#curated-metadata-and-evidence)
- [Structures and status](#structures-and-status)
- [Compound table schema](#compound-table-schema)
- [JSON storage](#json-storage)
- [Cache state and recovery](#cache-state-and-recovery)
- [Typed table persistence](#typed-table-persistence)
- [PubChem source boundary](#pubchem-source-boundary)
- [Pacing and retry ownership](#pacing-and-retry-ownership)
- [Resumable retrieval and failure outcomes](#resumable-retrieval-and-failure-outcomes)
- [Annotation content and provenance](#annotation-content-and-provenance)
- [Selected offline ingestion](#selected-offline-ingestion)
- [Unit and duration conversion](#unit-and-duration-conversion)
- [Numeric values and uncertainty](#numeric-values-and-uncertainty)
- [Annotation interpretation and review rows](#annotation-interpretation-and-review-rows)
- [Definition validation and required matching context](#definition-validation-and-required-matching-context)
- [Compound coverage denominators](#compound-coverage-denominators)
- [Comparison record consolidation](#comparison-record-consolidation)
- [Two-level summaries](#two-level-summaries)
- [Extraction audit and review queue](#extraction-audit-and-review-queue)
- [Offline composition](#offline-composition)
- [EPA identity crosswalk](#epa-identity-crosswalk)
- [ToxCast assay evidence](#toxcast-assay-evidence)
- [EPA hazard evidence](#epa-hazard-evidence)
- [EPA chemical properties](#epa-chemical-properties)
- [Shared normalized endpoint policy](#shared-normalized-endpoint-policy)
- [Point of departure dose units](#point-of-departure-dose-units)
- [EPA TEST predictions](#epa-test-predictions)
- [Explicit study and benchmark context](#explicit-study-and-benchmark-context)
- [Point of departure availability and potency](#point-of-departure-availability-and-potency)
- [EPA point of departure normalization](#epa-point-of-departure-normalization)
- [Source-specific offline EPA analysis](#source-specific-offline-epa-analysis)
- [Experiment endpoint evidence](#experiment-endpoint-evidence)
- [Experiment endpoint availability flags](#experiment-endpoint-availability-flags)
- [Experiment availability distributions](#experiment-availability-distributions)
- [Experiment classifier validation](#experiment-classifier-validation)
- [Experiment endpoint classifier targets](#experiment-endpoint-classifier-targets)
- [Tracked analysis and local experiments](#tracked-analysis-and-local-experiments)
- [Read-only presentation rebuilds](#read-only-presentation-rebuilds)
- [Professor presentation comparisons](#professor-presentation-comparisons)
- [Measured plant-assay acquisition](#measured-plant-assay-acquisition)

## Queries and resolved compounds

Query equivalence uses stripped casefolded names or canonical positive ASCII
CIDs. It does not infer synonyms. Compound identity requires a resolved positive
integer CID; even a numeric query remains unresolved without a snapshot. Resolved
aliases share one compound row. Distinct CIDs are never merged on the basis of
similar names or structures.

Reconciliation reads only selected queries and their supplied snapshots. Missing
snapshots retain unresolved rows. Equivalent unresolved queries share one row.
Compound rows, distinct alias spellings, and distinct source notes retain
first-seen order. Inputs are not mutated.

## Curated metadata and evidence

Blank group, subgroup, and HRAC labels become null and can be enriched by
nonempty values. Conflicting nonempty values raise `ValueError`. Comparisons are
case-sensitive after trimming. Source notes are collected without discarding
distinct notes, including notes attached to equivalent query spellings.

Input-file loading rejects conflicting notes on duplicate query records; compound
reconciliation can receive separately curated alias records and preserves all of
their distinct notes.

Snapshots for one CID may enrich missing property fields, but conflicting
nonempty properties or toxicity statuses raise `ValueError`. No alias is chosen
as authoritative based on traversal order. Reconciliation does not decide which
of two inconsistent snapshots is newer. Property and metadata CIDs, when supplied,
must agree with the snapshot CID.

## Structures and status

`smiles` uses `SMILES`, falling back to `IsomericSMILES`. `connectivity_smiles`
uses `ConnectivitySMILES`, falling back to `CanonicalSMILES`. Connectivity-only
data never fills the stereochemical field. Missing or blank text properties
remain null; nontext values raise `TypeError`. Molecular weight accepts numeric
values or numeric strings, produces a float, and rejects nonpositive, nonfinite,
Boolean, or malformed values.

Resolved identity is independent of toxicity retrieval. Metadata may explicitly
report `found`, `missing`, `pending`, or `not_retrieved`; an absent status defaults
to `not_retrieved`. Reconciliation does not infer retrieval success from supplied
toxicity content. Unresolved queries always report `not_retrieved`.

## Compound table schema

Compound tables use explicit Polars types, including nullable Int64
`pubchem_cid`, Float64 `molecular_weight`, and List(String) `input_queries` and
`source_notes`. Other fields are strings. Empty and all-null tables retain these
types. Table construction uses strict conversion; identity reconciliation
validates scientific property values before table construction.

## JSON storage

All raw storage paths take a caller-supplied data root. Path helpers perform no
I/O, use canonical query keys, require positive integer CIDs for compound paths,
and restrict bundle components to properties, toxicity, and metadata. They do
not select a default directory from the process working directory.

JSON is UTF-8 with readable Unicode, indentation, and a trailing newline.
Nonfinite floats are rejected. Each write creates a unique temporary file in
the destination's parent directory, ensuring replacement stays on the same
filesystem. The temporary file is flushed, synchronized, and closed before
`os.replace` publishes it. Serialization, write, and replacement failures leave
any prior destination intact and clean up the temporary file during exception
handling.

Atomic replacement protects one file from partial writes. It does not make a
properties/toxicity/metadata bundle transactional or serialize concurrent
writers; the last successful replacement wins. The parent directory is not
synchronized, so this is not a guarantee of durability across power loss.
Abrupt process termination can leave an unpublished temporary file behind;
consumers use the named JSON destination, not temporary files.

## Cache state and recovery

An absent query alias returns `None`. A present alias must contain a query with
the expected canonical key and a positive integer CID. Numeric queries must
agree with the alias CID. A referenced bundle with absent or malformed components
raises `ValueError`; `complete_record` returns false for such bundles. Permission
and other filesystem access errors propagate. JSON objects are required, and
nonstandard NaN/infinity tokens are rejected.

Properties must use the REST `PropertyTable.Properties` envelope with exactly one
record matching the CID. Metadata requires the same integer CID, `source` equal
to `PubChem`, a timezone-aware UTC timestamp, and an explicit cache status.
Found toxicity requires a PUG-View record with the matching CID and a Section
list or null. Missing toxicity requires exactly the Toxicity absence marker.
Neither an HTTP error envelope nor a malformed response counts as absence.

| Saved state | Reader behavior | Complete? | Recovery |
| --- | --- | --- | --- |
| No alias | `read_snapshot` returns `None` | CID bundle checked separately | Resolve or restore the query alias |
| Alias and properties, no metadata | Raises `ValueError` | No | Resume identity setup and publish pending metadata |
| Valid properties and pending metadata | Exposes identity; toxicity is null | No | Retry toxicity retrieval |
| Pending metadata with old, corrupt, or absent toxicity | Never reads toxicity; exposes identity | No | Replace toxicity before publishing terminal metadata |
| Found metadata and matching PUG-View payload | Exposes validated snapshot | Yes | Reuse |
| Missing metadata and explicit absence marker | Exposes validated snapshot | Yes | Reuse |
| Terminal metadata with absent, corrupt, or mismatched payload | Raises `ValueError` | No | Repair or refetch the bundle |

For a first fetch, interruption between writing properties and metadata leaves
an incomplete bundle. For refresh of an existing bundle, pending metadata must
be committed **before overwriting properties**. Until properties are replaced,
readers may expose the prior identity but no toxicity. After the new properties
and toxicity are saved, terminal found/missing metadata publishes completion.
Interruption after saving toxicity but before terminal metadata leaves the bundle
pending and retryable.

Overwriting properties while retaining old terminal metadata is prohibited: a
CID-matching reader cannot distinguish that mixed generation from a complete
bundle. Per-file atomicity alone cannot detect or prevent that sequence. The
retrieval writer must enforce the pending-first refresh protocol; cache readers
do not infer generations from file timestamps. Reads and refreshes must be
serialized by the caller; these checks do not provide a multi-file transaction
or protection against a concurrent writer changing files during a read.

## Typed table persistence

Record-to-table construction requires an explicit schema and uses strict Polars
construction. Parquet persistence preserves the caller's schema, column order,
nulls, and nested lists/structs using the native engine. It neither converts
tables through pandas/PyArrow nor introduces inferred stage schemas. Additional
stage schemas are defined when their producers are implemented.

Required table reads propagate missing-file and corrupt-Parquet errors. An
optional expected schema is compared exactly, including column order; mismatches
raise `ValueError`. No columns are selected away, values cast, NaNs converted to
nulls, or missing files replaced with empty tables. An actual zero-row typed
table is valid. Scientific validation remains the producing stage's responsibility.

Each saved table has a `.metadata.json` sidecar replacing the `.parquet` suffix.
It records `generated_at` as timezone-aware UTC, explicit `code_version`,
`row_count`, and SHA-256 `input_hashes`. Dependency keys preserve the caller's
path spelling. The caller supplies all consumed aliases, metadata, raw/processed
inputs, configs, and implementation files; the writer cannot infer those
dependencies from a DataFrame. Dependencies must remain unchanged from stage
computation through hashing. A code version supplements implementation hashes;
it does not replace them.

All dependency hashes are computed before writing. Missing inputs raise without
modifying existing products, and a dependency cannot also be either output path.
Parquet is written to a unique sibling temporary file and atomically replaced;
failed writes or replacement remove the temporary file and preserve the previous
table. The sidecar is then written with the atomic JSON writer.

The two files are not a transaction: a sidecar failure after table replacement
can leave the new table with an absent or older sidecar. Such an interrupted
export must be rerun before publishing or relying on its provenance. The table
reader validates the supplied schema, not sidecar consistency or dependency
freshness. Concurrent input mutation and concurrent exports require caller
coordination. Native Parquet replacement does not promise power-loss durability.

## PubChem source boundary

The source protocol exposes name resolution, property retrieval, and toxicity
retrieval without cache management or scientific interpretation. PubChemClient
accepts a minimal HTTP transport implementing `get`; its default transport is a
Requests session. Construction performs no requests, and positive ASCII CID
queries bypass name lookup. Name equivalence does not authorize selecting one
CID from an ambiguous response, even when returned CIDs are duplicated.

Name lookup requires a well-formed IdentifierList with positive integer CIDs:
an empty list is unresolved (`LookupError`), multiple entries are ambiguous
(`ValueError`), and malformed envelopes are errors. Property responses require
exactly one matching CID. Toxicity responses require the matching PUG-View CID
record. Shared pure validators keep these rules identical for HTTP responses and
saved cache envelopes; raw source content is retained without modification.

Only an HTTP 404 from the explicit Toxicity-section request maps to `None`.
Name/property 404s and all other HTTP or transport failures propagate. A
successful HTTP response containing an absence marker, fault envelope, or invalid
JSON never becomes missing data. Connect/read timeouts are fixed at 10/40 seconds.

Redirects are disabled to avoid hidden requests; only HTTP 200 is accepted as
successful. Asynchronous or redirected responses are errors. Transport tests
inject fakes and never contact the provider.

## Pacing and retry ownership

The application owns retries. Standard Requests session adapters, including
adapters on a supplied session, have their retry policy reset to zero during
client construction. Other custom transports must not retry internally. Each
`get` call represents one observable attempt, with its own finite timeout.

HTTP 429/500/502/503/504, Requests timeouts, and connection errors are retryable.
SSL errors are excluded from connection-error retries. Permanent errors, identity
404s, invalid JSON, and invalid envelopes are never retried. Toxicity 404 remains
observed absence, including when it follows a transient failure. Exhausting the
retry budget propagates the final HTTP or transport error; it never becomes
missing data.

Defaults allow four retries after the initial attempt, using exponential backoff
of 1, 2, 4, and 8 seconds. The budget resets for each operation. Retry counts must
be nonnegative integers, excluding Booleans. Intervals must be nonnegative finite
numbers, excluding Booleans; zero disables inter-attempt pacing.

Each client tracks the start of every HTTP attempt using a monotonic clock.
The first request starts immediately; subsequent starts are separated by at
least the configured interval, defaulting to 0.25 seconds. Request duration counts
toward this interval. Failed attempts retain their start time. Numeric CID
passthrough performs no request and does not alter pacing state.

Before a retry, the next start waits until both the prior-start pacing deadline
and a response-relative backoff deadline have passed. Backoff is the greater of
the exponential delay and valid Retry-After delay. Integer ASCII seconds and
timezone-aware HTTP dates are supported. The date delay uses the injected Unix
epoch wall clock at response handling time. Malformed, nonfinite, negative, or
timezone-less headers fall back to exponential backoff; past dates and zero
seconds cannot shorten it. No sleep occurs after the final exhausted attempt.

Monotonic clock, epoch wall clock, and sleep are injectable; tests forbid actual
sleeping and assert attempt counts and start times. Wall-clock changes do not
affect ordinary pacing. A client is intended for sequential operations; it does
not coordinate concurrent callers or other client instances. Current provider
guidance must be reviewed separately before live validation.

## Resumable retrieval and failure outcomes

Retrieval accepts a Source and explicit data root. A batch first validates and
merges curated queries; conflicting inputs raise before any requests or writes.
Single-query domain, HTTP, and filesystem errors become structured outcomes with
query, nullable CID, failing stage, exception type, and message. Batches preserve
selection order and continue after these errors. Unexpected programming errors
outside the handled exception types propagate.

Aliases are validated independently of bundle content. A valid alias retains its
CID when a corrupt bundle needs repair; a corrupt alias is re-resolved. Complete
found/missing bundles need no remote calls. A newly resolved alias may reuse an
existing complete CID bundle. Reusing a bundle updates only the alias's current
curated metadata while retaining its first spelling. Curated-input conflict
checks apply within the selected batch; a later run may explicitly update saved
input metadata.

Valid pending snapshots retain properties, so resumption requests only toxicity.
Otherwise properties are fetched and validated in memory before publication.
Once the replacement identity is ready, pending metadata is committed before
overwriting properties, followed by alias publication, toxicity retrieval/write,
and terminal found/missing metadata. Invalid source payloads cannot complete a
bundle, even when a fake or alternate source bypasses HTTP-adapter validation.

A properties request or pending-write failure during refresh leaves the prior
complete snapshot intact. After pending commits, later failures leave toxicity
hidden and the bundle retryable. If force re-resolution changes the CID, the old
CID bundle is retained; the alias switches only after the new properties have
been saved. Interrupted identity setup with no usable alias may need resolution
again. Missing-section results use the explicit absence marker and are reusable.

Force refresh always re-resolves, even if the alias or resulting CID already has
a complete cache. No automatic cache expiry is inferred. Archive a data root
before force refresh when a prior evidence generation must remain reproducible.

## Annotation content and provenance

Flattening operates on supplied PUG-View dictionaries and produces records without
I/O or scientific interpretation. A caller-supplied positive CID establishes the
compound identity; upstream envelope validation establishes agreement with the
source record. Missing/null Section and Information lists are empty; malformed
traversal containers raise `ValueError` rather than silently dropping content.

Each Information value representation yields an annotation. StringWithMarkup
items retain their text individually. Scalar numbers and singleton numeric lists
retain units; multi-number arrays stay one `NumberArray`. Unknown or malformed
value representations are serialized as JSON. `information_json` retains the
entire original Information object, including markup and unrecognized metadata.
This allows review without reconstructing source content from extracted text.

Reference numbers are positive integers and are stored as a sorted unique list.
Malformed reference identifiers raise `ValueError`. Sources retain structured
number/name/URL fields and complete canonical `reference_json`; dangling references
retain the number with null metadata. Different source records sharing one number
are all retained, while exact duplicate reference records collapse. SourceName
takes precedence over Name for the display field, and both remain in raw JSON.
Information URLs are stored separately from source URLs.

IDs use SHA-256 over canonical JSON containing the compound, record title,
heading path, full Information content except its original ReferenceNumber field,
the extracted value text/kind, normalized reference numbers, and source records.
Dictionary keys and source records are ordered canonically. Reference order and
duplicate reference numbers do not affect identity. Original Value array order
is preserved and remains part of content identity.

Query aliases, raw-file location, retrieval time, and traversal indices are
excluded. Sibling-section, Information-entry, and reference-table reordering
therefore leave unchanged annotation IDs stable. Changing the heading context,
source metadata, or content changes identity. Repeated equal content may share an
ID, but rows and their provenance are retained. These IDs do not establish study
independence.

## Selected offline ingestion

`parse_snapshots` validates and merges the curated selection before reading any
cache. Every selected alias is validated, but each CID's property, metadata, and
toxicity files are loaded once. The resulting snapshots feed existing compound
reconciliation and annotation extraction. Returned table order is annotations,
then compounds; both use explicit schemas, including empty results.

The workflow does not scan cache directories or infer resolution from numeric
queries without an alias. Missing aliases remain unresolved. Corrupt selected
aliases/bundles raise, while unselected cache content is irrelevant. Current
selection metadata supplies classifications and source notes; saved alias
input_metadata does not override it. Classification conflicts among aliases of
one CID remain visible errors.

Compound rows retain resolution and toxicity status for downstream audit without
filesystem rereads. Pending and missing bundles contribute identities without
annotations; a found but empty section remains distinct from a missing section.
Each found CID is flattened once regardless of alias count. Equal-content
repeated source annotations remain separate rows as defined by the parser.

Rows preserve first-seen selection/CID order and source traversal order. Repeated
reads of unchanged inputs yield equal tables. No raw files are modified and no
network dependency is created. Callers serialize access to the selected cache,
as with individual snapshot reads. Table persistence remains an explicit separate
operation using `save_table`; the inspection example only prints previews.

## Unit and duration conversion

Unit helpers return explicit factors, without parsing prose, converting unknown
context into defaults, or modifying annotation evidence. Supported LD50 doses
convert g/mg/ug per kg to mg/kg; LC50/EC50 concentrations convert g/mg/ug per liter
to mg/L. Factors are respectively 1000, 1, and 0.001. Endpoint case/spacing and
unit case/whitespace are normalized, both Unicode micro symbols are accepted,
and slash or inverse-denominator forms are supported. Explicit trailing bw/body
weight labels are recognized only for LD50 dose units. Unsupported endpoints,
dimensions, or units remain `(None, None)`.

The ppm approximation is permitted only for concentration endpoints with explicit
medium `water` or `aqueous`, case-insensitively after trimming. It assumes dilute
aqueous density near 1 kg/L, approximating 1 ppm as 1 mg/L. The helper does not
infer water from fish, an endpoint, or a desired comparison. Air, seawater, and
unknown media remain unsupported; gas and molar conversions require additional
scientific assumptions and are not implemented.

Duration conversion accepts numeric hours, days or weeks and returns float hours.
Days multiply by 24; explicit weeks (`wk`, `wks`, `week`, `weeks`) multiply by 168.
Elapsed weeks have a fixed seven-day meaning; months and event-relative times
remain unsupported. The ECOTOX adapter additionally requires the exact `wk` code
in its source dictionary and an equality/unqualified scalar. This support was
added after a primary rat-study review found native two-week observation metadata
previously normalized to null. Unit conversion does not establish acute dosing or
turn a follow-up duration into continuous exposure. Frozen exports remain intact.
Missing values or unsupported/missing units remain null.
Negative and nonfinite values are rejected before examining unit support;
conversion overflow also raises `ValueError`. Booleans and numeric strings are
not duration numbers at this boundary and raise `TypeError`; text extraction is
a separate responsibility. Zero is preserved as a numeric conversion result,
while downstream endpoint policies may require a strictly positive duration.
These helpers perform unit/duration conversion; annotation interpretation
composes them separately.

## Numeric values and uncertainty

`parse_value` returns an unconverted ParsedValue or `None`. Exact positive finite
values use qualifier `=`. Inequalities retain their positive numeric threshold
as `value_numeric`; Unicode ≤/≥ map to ASCII <=/>=. Strictly ascending positive
ranges use qualifier `range`, separate lower/upper bounds, and null scalar.
Equal bounds are not silently reclassified as an exact value. Inequality-prefixed
ranges and error bars are unsupported rather than coerced into another category.

The numeric grammar accepts ASCII digits, correctly grouped three-digit thousands
commas, dot decimals including a leading decimal point, and scientific notation.
Exponent signs are supported; unary result signs are not. Zero, negatives,
nonfinite values, numeric overflow, and underflow to zero are rejected. Malformed
tokens cannot contribute a convenient trailing numeric substring.

Values require one recognized mass-dose, mass-concentration, or ppm unit. Units
remain exactly as matched, without factors or endpoint compatibility decisions;
the unit helper supplies those separately. Ranges support hyphen/en/em dash or
`to` with one shared trailing unit. Unsupported dimensional extensions such as
mg/L/day are not shortened to a supported unit.

Endpoint labels are masked before matching so their 50 is context, not a
competing numeric result. Explicit hour/day/week durations may accompany the result.
Other unconsumed numeric content causes rejection, including confidence-interval
numbers; labelled-field isolation belongs to annotation interpretation. The
parser does not select a preferred measurement from competing candidates.

Approximation phrases and supported approximation symbols are rejected globally.
Verbal comparisons such as less-than/at-least are unsupported rather than
treated as exact. Supported symbolic inequalities must attach to the numeric
result. Source text remains on the annotation; a failed extraction does not
delete evidence. Complete/partial/failed annotation statuses are not assigned
by this numeric helper.

## Annotation interpretation and review rows

Each annotation produces exactly one normalized or reviewable row. The normalizer
deep-copies provenance and retains all original source fields. Context is read
only from section headings, Information name/description, and value text. Record
titles, compound names/classifications, reference metadata, and serialized JSON
are excluded from interpretation so chemical identity and source labels cannot
impute desired exposure context.

Supported endpoints are LD50, LC50, and EC50. Multiple or competing supported/
unsupported endpoint labels are ambiguous. Species aliases use an explicit
vocabulary, with specific rainbow-trout, fathead-minnow, and Daphnia-magna names
overriding generic matches. Species and routes are never selected arbitrarily
from conflicting hits. A shared organism group can remain known even when its
species are ambiguous, but the row remains partial.

Exposure durations use explicit hours/days. Equivalent representations agree
after conversion; the first equivalent raw value/unit is retained alongside the
canonical hours. Conflicting durations leave duration fields null. Unlike the
basic duration helper, annotation exposure requires a strictly positive value;
invalid, overflowing, or unsupported duration context produces a partial row.
Explicit age and follow-up/observation periods are excluded from exposure duration.

A unique Concentration field isolates its numeric result and duration until a
semicolon or opening parenthesis. The full annotation still supplies species,
route, medium, endpoint, and formulation checks. Hardness, age, or confidence
intervals outside that field cannot supply a missing result or replace an
ambiguous concentration. Multiple or empty labelled fields remain partial.

Only String, StringWithMarkup, and scalar Number representations are eligible
for numeric interpretation. NumberArray and unfamiliar shapes remain review
rows. Formulation, mixture, and extract terms force partial status. Unstructured
multi-sentence narratives and Interactions sections require attribution review,
even when they contain one syntactically valid numeric range. Such ranges may
describe administered doses or other substances rather than the selected
compound's endpoint; they are never promoted to complete solely by numeric fit.

Valid numeric fields and qualifiers are retained even in partial rows when
available. One factor converts the scalar or both bounds; any resulting
nonpositive/nonfinite quantity prevents publishing standardized quantities.
Ranges retain null scalar fields, and inequalities retain their qualifiers.
Missing optional context alone does not prevent completeness. Complete means
supported numeric extraction and compatible conversion with no detected review
condition, not study validation or a safety conclusion.

The Polars wrapper validates schemas and the unique compound universe before
joining metadata by compound_id. Orphan annotations and duplicate compound IDs
raise instead of disappearing or multiplying rows. Canonical measurement types
remain explicit for empty and all-null outputs; structured provenance and
noncolliding extra annotation columns survive. Reserved derived/context column
collisions raise rather than overwriting input provenance.

## Definition validation and required matching context

Policies use a closed vocabulary, positive finite numeric exposure hours, and
canonical endpoint-compatible units. Safe YAML loading rejects duplicate keys
instead of allowing later values to overwrite earlier policies. Display fields
endpoint_family, label, and context_note are retained but never interpreted as
measurement context. Unknown fields and malformed configuration raise ValueError.

One Polars predicate defines eligibility and required context equality. The
single-row helper adapts a record to that predicate with explicit measurement
types; table consumers use the expression directly. Complete status alone is
insufficient: the row must explicitly exclude formulations and contain a valid
converted scalar/threshold or ascending interval in the endpoint's canonical
unit. Intervals cannot simultaneously supply a scalar.

Configured preferred route and duration are requirements, never imputed values.
Broad endpoint coverage and narrower species/duration comparisons can therefore
select different rows without changing any normalization or source evidence.

## Compound coverage denominators

Coverage starts with the selected compound universe. Each named policy filters
normalized measurements with the shared matching predicate, selects distinct
compound IDs, and left-joins binary availability onto that universe. Group counts
sum those flags and count selected compounds, retaining null groups and zero-data
groups. Unresolved query identities remain denominator members until resolved.

Exact duplicate compound rows can collapse; conflicting duplicate identities
raise, including conflicting alias lists or metadata. Alias reconciliation belongs
before coverage. Measurements outside the universe raise rather than silently
disappearing. Coverage reports availability of eligible evidence, not independent
study counts, study quality, or comparative safety. An interval or threshold can
establish availability without becoming an exact toxicity value.

## Comparison record consolidation

A comparison record is one eligible value in one context. Eligibility is the
shared matching predicate, so a record cannot exist for a context the
comparison does not define. Consolidation groups by comparison, compound,
endpoint, species, exposure route, duration, standardized unit, qualifier, and
the standardized scalar or bounds. `organism_group` is excluded from the key: a
definition that constrains it already fixes that value, and splitting on it
would fragment otherwise equal evidence. Inequalities and ranges keep distinct
qualifiers. A threshold is never reclassified as an exact value, and a range
never becomes a scalar.

Consolidation is equal-value consolidation, not study deduplication. Equal
numbers from different sources become one record with several support
identifiers. That record does not claim independent studies, and it does not
discard a repeated observation. Every supporter keeps its annotation identifier,
original value text, and nested source reference, so a reviewer can trace the
record back to the saved evidence.

Records are ordered by definition order and then by the consolidation fields,
with nulls last, so the same inputs always produce the same rows. Missing
required measurement columns, null compound identities, and invalid policy
definitions raise `ValueError`.

## Two-level summaries

Summaries are computed at two levels. The compound level counts the
consolidated records for one compound in one comparison and reports the median,
minimum, and maximum of the exact results. The group level is then derived from
the compound summaries, so each compound contributes exactly one value however
many studies or annotations it has.

The group median is the median of compound medians, never the median of pooled
records. The two differ when studies are unevenly distributed, so the pooled
value is not interchangeable with the compound-weighted one. As a numeric
counterexample, one compound with three records at 1000 mg/kg and a second
compound with one record at 9000 mg/kg give a pooled record median of 1000
mg/kg, while the median of the two compound medians is 5000 mg/kg. Only the
second number answers "what is the middle compound in this group".

Thresholds and ranges are counted separately from exact values and never enter
the median. A compound with only censored or interval results therefore has a
typed null exact median rather than a substituted value. Compound and
uncertainty counts may overlap at the compound level, because one compound can
have both an exact result and a threshold.

Every observed chemical group appears for every comparison, including groups
that were not anticipated, groups with a null label, and groups with no
matching evidence. Group denominators come from the selected compound
universe, so unresolved queries and compounds without data remain counted.
Conflicting duplicate compound identities raise rather than depend on row
order.

## Extraction audit and review queue

Every selected compound gets one audit row explaining why comparable data is
present or absent. The reasons are evaluated in a fixed priority order, and the
first applicable reason is reported: `unresolved_query`,
`toxicity_request_failed_or_pending`, `toxicity_section_missing`,
`no_annotations_in_saved_section`,
`annotations_present_no_supported_complete_measurement`,
`complete_measurements_outside_comparison_contexts`, and
`comparison_data_available`.

A compound that is both unresolved and pending is reported as unresolved,
because the earlier state explains the later one. A compound whose toxicity
request was never completed is reported with the pending and failure reason
rather than with an empty-section reason, since nothing was ever saved to
inspect. These states describe the PubChem retrieval for the selected
compounds only. They are not a general statement about a chemical, and the
absence of comparable data never means the absence of hazard.

The review queue holds every partial and failed measurement with its parse note
and full nested source provenance, so a reviewer can read the original evidence
beside the reason extraction did not succeed. Complete measurements are not
queued. The queue is a worklist, not a result: nothing in it is evidence of
either hazard or safety.

## Offline composition

`build_offline` composes the analysis tables from the selected snapshots in one
pass, without network access, reporting, plotting, or command-line
orchestration. The stage tables are the compounds, annotations, measurements,
coverage matrix, coverage group summary, comparison records, compound summary,
group summary, extraction audit, and review queue.

The composition is deterministic. The same selection, the same raw evidence, and
the same definitions produce the same rows in the same order, because the
underlying stages are ordered and the consolidation key is content based. This
is what makes a rerun comparable to the run before it, and it is checked by
comparing whole tables rather than timestamps.

Raw evidence is only read. The workflow never writes, refreshes, or moves the
cache, and the returned dependency hashes identify every file that was
consumed, so a manifest can state which evidence produced a result. A pending
bundle contributes its identity and its properties, but its toxicity file is
neither read nor listed as a dependency, because nothing in it was used.

Selection is consistent across every table. A selected query without a saved
alias remains in the compound universe as an unresolved identity, which keeps
it in the denominators while the evidence tables stay empty for it. Cached
records outside the selection never enter the output, and adding an alias for
an already selected compound does not add a compound or an annotation.

## EPA identity crosswalk

A PubChem compound and an EPA substance are different records of the same
thing. The PubChem CID remains the internal compound key, and a DTXSID is an
external identifier that is only attached when the match is defensible.

A match is approved only when exactly one EPA candidate has the same full
InChIKey as the compound. A candidate that shares the connection layer of the
InChIKey but not the full key differs in stereochemistry, tautomer, or
protonation; a candidate with a different connection layer is a different
substance, such as a salt or an ester. Both are recorded and both are sent to
review. A candidate found by name alone is never approved, because a shared
name is not evidence of a shared structure.

Ambiguity is never resolved by choosing the first or the highest ranked
candidate. Several candidates with the same full InChIKey, a connectivity-only
match, and a name-only match all produce `needs_review`, and the candidate
evidence is kept so a reviewer can decide. A compound with no defensible
candidate stays `unresolved`, and a compound whose PubChem identity is itself
unresolved stays unresolved without a search.

The same substance can be found by more than one search. It is recorded once,
described by its strongest evidence, so a substance found by both InChIKey and
name is not mistaken for two ambiguous candidates.

The structure comparison uses the candidate's own chemical record, not the
search response. The search response identifies the candidate but does not
carry its structure, so comparing against it would approve a candidate whose
InChIKey was never seen. A candidate whose record cannot be read keeps a null
structure and is never approved. The provider's near-miss suggestions are kept
for a search that found nothing, because they usually name the alternative
structure of the same compound, which is exactly the case a reviewer needs to
see.

The EPA API key travels in a request header only. It is never written to a
cached response, a URL, a log, or an error message, and the cached envelope
records the search term, the path, the retrieval time, and the response
status. Cached searches are reused, so a rerun makes no request for a term that
was already retrieved, and the crosswalk can be rebuilt entirely offline.

## ToxCast assay evidence

In-vitro bioactivity and acute toxicity are different kinds of evidence. An
assay result is a fitted measurement of a cellular or biochemical response at
a set of concentrations. It is not an LD50, an LC50, or a statement about the
harm a chemical does to an organism, and the pipeline never converts one into
the other or merges the assays into a single toxicity number.

Each row records the source fields as they were provided, including the hit
call, the activity value, the benchmark dose, the concentration range and its
unit, the response range, the fitted model, and the fit category. Units are
carried through unchanged. Nothing is reinterpreted, because the source does
not label the activity value with a unit, and inventing one would be a
fabrication.

Absence and inactivity are different states. A substance that was never tested
in an assay has no row for that assay. A substance that was tested and showed
no activity keeps its row and is marked `inactive`. The hit call is a
continuous value rather than a count, so a positive call is an active curve, a
negative call is an inactive one, and a call of exactly zero is neither. The
coverage table reports those three states separately, and none of them is read
as safety.

`measurement_kind` distinguishes a fitted assay metric from a directly
observed endpoint, and `evidence_class` records that the evidence is
experimental. Only an approved DTXSID is retrieved, so a compound awaiting
identity review never receives another substance's evidence.

The bioactivity API does not report the invitrodb release it serves, so the
source is named explicitly as the CompTox bioactivity API rather than
implying a pinned release. A bulk import of a pinned invitrodb release would
be a separate source with its own version, and the two must not be silently
combined.

## EPA hazard evidence

Hazard observations are a different kind of evidence from PubChem annotations.
An observation is one study result with a full context: the endpoint, the
species, the route, the duration, the value and its unit, the formulation, and
the reference. Every field is taken from the record, including whether the
record is experimental or predicted, which the source states explicitly. A
record whose value cannot be read keeps a null value; it is not dropped and it
does not become zero.

The mapping to the pipeline's comparison contract is deliberately narrow. Only
LD50, LC50, EC50, NOAEL, LOAEL, BMD, and BMDL are mapped, and only when the
unit converts cleanly and the value and converted result are positive and finite. A
record with an incompatible unit, an unsupported endpoint, or a missing value
stays outside the comparison and remains inspectable in the hazard table, so
nothing is silently dropped and nothing is silently reinterpreted.

The duration is converted to hours through the same validated helper the
normalization stage uses, and an unsupported duration unit leaves the duration
unknown rather than assuming one. The source marks a missing duration with a
negative sentinel and a placeholder unit, so a missing duration is unknown and
is never an error. The organism category is mapped to the pipeline's
vocabulary, including the plural forms the source uses, and an unmapped
category stays null while the original text is kept.

A record states whether it is experimental, not experimental, or
undetermined. Only an explicit `experimental` mark admits a record to comparison
inputs. Nonexperimental, undetermined, and unmarked records stay in the hazard
evidence table, where their source classification remains inspectable, but
cannot contribute to experimental comparisons. This classification follows the
source and does not independently establish study quality.

Only an approved DTXSID is retrieved, so a compound awaiting identity review
never receives another substance's hazard evidence. Cached responses are
reused, and the cache holds the response and its retrieval time, never the API
key.

Equal values from different studies are not deduplicated here. A hazard record
is a study observation, and whether two records are independent is a question
for the analysis stage, not for the parser.

## EPA chemical properties

Properties are recorded in long form: one row per compound, property, and
source, so a value that two sources report differently keeps both rather than
one overwriting the other. A PubChem value and an EPA value for the same
property are two rows with two sources, and neither is silently preferred.

The origin of a value is not guessed. The source separates measured properties
from computed ones by the endpoint that serves them, so `property_origin` is
`measured` for a record from the experimental property endpoint and
`calculated` for a record from the predicted property endpoint. The endpoint is
kept in the row, so a reader can check the basis of every value, and the
model name and identifier are kept for a calculated value so the model is
known.

A missing optional trait is null. It is never replaced by zero, and a property
the source does not report is simply absent. A value is never reinterpreted
into a different quantity, and the applicability domain fields are kept
beside a calculated value so a prediction outside the model's domain is
visible rather than hidden.

The cache holds the response and its retrieval time, never the API key. The
experimental and the predicted responses are cached separately, so a rerun
makes no request for a response that was already retrieved.

## Shared normalized endpoint policy

Normalized endpoint membership and standard units have one read-only policy in
`agrotox.endpoints.ENDPOINT_UNITS`. The policy covers LD50, LC50, and EC50;
source evidence tables may preserve other endpoint labels without admitting
them to normalized comparisons.

The shared mapping prevents separate endpoint lists in context extraction,
coverage, units, and EPA hazard mapping from drifting apart. It does not infer
source aliases, supply missing study context, or make observations comparable
merely because they share an endpoint and unit. Numeric parsing and accepted
unit spellings remain separate rules. This organization preserves existing
eligibility, conversion, validation, and summary behavior.

## Point of departure dose units

NOAEL, LOAEL, BMD, and BMDL conversions preserve the reported dose time basis:
`mg/kg` and `mg/kg-day` are distinct standard units. Mass scaling changes only
g/mg/ug, never the exposure period. `POINT_OF_DEPARTURE_UNITS` records these
allowed units separately from the acute endpoint policy.

Inhalation concentrations and dietary ppm require context and conversions
beyond mass scaling, so they remain unsupported for these endpoints. Exposure
duration is not used to multiply a daily dose into a total dose. Existing acute
endpoint conversions continue to reject daily dose units.

## EPA TEST predictions

Predicted values are not measurements. They are kept in their own table, every
row records `evidence_class` as `predicted`, and no prediction ever enters a
measured endpoint median, the experimental coverage, or the comparison
records.

This stage reads the predictions the provider has already stored. It does not
post a SMILES or an InChIKey to any service, and it provides no function that
runs a model on a novel structure. Predicting a compound that the provider has
no stored prediction for would need a separate integration with the standalone
TEST service, and that is a different piece of work with its own validation
and its own versioning. Until that exists, the honest answer for an
unsupported compound is that no prediction is available, not a fabricated one.

Only the records the source attributes to a TEST model are kept, and the
applicability domain method, value, conclusion, and reasoning travel with the
prediction, so a prediction the source places outside the model's domain stays
visible. A missing prediction is absent, and a missing value is null; neither
is ever recorded as zero.

The predictions are read from the cached predicted-property response, so
re-running this stage costs no request.


## Explicit study and benchmark context

Study type, duration class, effect, evidence basis, benchmark response and its
interpretation, model name/identifier, confidence level, and study identifier
are nullable context fields in normalized measurements and comparisons. They
are string-valued source metadata, with no assumed response scale, default
confidence level, or inferred study/model link. Each can constrain a definition
by exact equality; missing required context fails eligibility.

These fields participate in consolidation so equal numeric results with
different effects or benchmark/model context do not collapse. Existing acute
rows without this information retain null context. Adding the fields changes
persisted measurement and comparison schemas; regenerate those products from
raw caches instead of casting older tables into the new schema.


## Point of departure availability and potency

NOAEL/LOAEL observations and model-derived BMD/BMDL results are distinct
endpoint comparisons. Their definitions must select either mg/kg or mg/kg-day;
these unit bases never share a comparison. Matching enforces the expected
evidence basis as well as any configured context. Source-reported qualifiers
retain their numeric meaning; endpoint semantics do not invent inequalities.

Point of departure definitions default to availability-only summaries. All
eligible observations remain inspectable as comparison records with counts,
but no median, minimum, or maximum is produced unless the definition explicitly
requests potency and constrains species, route, exact exposure hours, study
type, and effect. Benchmark results additionally require an explicit response
interpretation and model, with confidence level required for BMDL. This is a
conservative contract: incomplete source metadata can support availability
without supporting a potency comparison. Existing acute summary defaults are
unchanged. The label "exact" counts reported scalar values, including a
reported BMDL; it does not change a lower confidence bound into a point estimate.


## EPA point of departure normalization

Every structured hazard record has a normalized annotation, including an
explicit review reason when source status, endpoint, units, numeric result,
qualifier, or formulation prevents completeness. The original source record is
retained as JSON in the hazard table and normalized provenance. Retrieval time
is excluded from content-derived annotation identities, while compound identity
is included. Older typed hazard tables remain readable by the normalizer, but
full original metadata requires rebuilding from raw caches.

BMD/BMDL carry a model-derived evidence basis independently of the source's
experimental flag. Explicit experimental status remains necessary for admission
to comparison inputs. A parenthetical numeric response in a BMD/BMDL label is
retained as a string token without an inferred percent/risk interpretation,
model, confidence level, or partner result. These missing fields block potency
summaries under the comparison contract while allowing availability counts.
NOAEL/LOAEL preserve reported qualifiers rather than acquiring invented bound
semantics. Source variants such as LOAEL (HEC) remain unsupported for review.

## Source-specific offline EPA analysis

EPA hazard analysis reads only selected approved identity caches, preserving
the full selected compound universe as its denominator. An unapproved identity
is a distinct audit state from an approved identity with an explicitly empty
response. A missing approved cache raises instead of masquerading as an empty
response. Envelope and record substance identifiers must agree with the
approved crosswalk. Crosswalk duplicates for selected compounds are rejected.

EPA extraction and review states are source-specific; PubChem section-missing
and request-pending states cannot explain EPA evidence. Comparison and summary
rules are shared, with point of departure definitions defaulting to availability
only. Source tables stay separate: assay bioactivity and TEST predictions are
not inputs to organism-level hazard comparisons. The workflow rebuilds from
raw caches, preserves them unchanged, and records hashes for consumed evidence;
the runnable export example also hashes selection, policies, and implementation.

## Experiment endpoint evidence

Experiment consumers rebuild EPA endpoint tables from selected raw caches using
the offline workflow rather than trusting legacy processed products. PubChem and
EPA coverage use the same full selected denominator. Unapproved identities remain
visible through the EPA audit and are not interpreted as evidence of no hazard.
Chronic availability policies retain the pipeline's prohibition on potency
medians without comparable study context; model-derived BMD/BMDL observations
are not interchangeable with TEST predictions.

## Experiment endpoint availability flags

Experiment traits preserve source-specific endpoint flags and a union over the
two sources. An unavailable source is null rather than zero; a union can still
be positive when the other source supplies evidence. A negative union requires
both sources to be assessed. All selected identities remain in the trait table.
These flags measure extraction availability, including PubChem's acute-only
parser limitation, and do not supply chronic potency estimates.

## Experiment availability distributions

Every configured endpoint flag remains in distribution and comparison products,
including all-null and all-zero flags. Its category is endpoint availability,
not molecular property or potency. Missing groups yield null estimates and
explicit sample counts. No endpoint dose distributions are pooled across the
heterogeneous chronic contexts in the example availability definitions.

## Experiment classifier validation

Held-out compounds use training-fold medians, means, and standard deviations.
No held-out distribution is used to fit preprocessing. Five-fold accuracy is
unavailable for targets with fewer than five examples of either class. This
limits unsupported claims for absent BMD or sparse BMDL evidence; it does not
make the purposive compound selection representative of a population.

## Experiment endpoint classifier targets

Every configured source-specific or combined endpoint flag is a potential
classifier target. Only assessed labels enter that target's sample; descriptor
imputation never invents a label. Sparse and absent targets remain explicit
result rows with unavailable accuracy. Endpoint doses and predictions are not
used as classifier features or converted into safety categories.

## Tracked analysis and local experiments

The professor-facing analysis lives under `analysis/`. `experiments/` stays
ignored and retains local working files even when its formerly tracked sources
are removed from the index. Analysis tests import the tracked analysis sources;
raw inputs, computed tables, environment caches, and presentation exports remain
local. This separation does not change endpoint eligibility or evidence classes.

## Read-only presentation rebuilds

The analysis rebuild takes a source-cache root and a separate output directory.
Missing descriptors stay missing without network access. It uses the retained
pipeline workflow and records raw/cache inputs, analysis code, and outputs in a
manifest. The marimo environment has its own lockfile and a local pipeline
reference; neither source caches nor generated presentation data are committed.

## Professor presentation comparisons

The seven primary endpoint charts compare evidence availability with explicit
unassessed states, not heterogeneous toxicity-dose distributions. Chemical-trait
CDFs normalize within group and exclude missing/nonfinite values. Classifier
performance is shown beside its majority-class baseline. Presentation loading
checks prepared product hashes before showing results, so mutated data do not
silently appear under an earlier checkpoint.

## Measured plant-assay acquisition

ChEMBL assay snapshots preserve measured records and publication context before
any policy converts evidence to labels. Database membership, missing activity,
assay names and structure similarity do not supply active/inactive ground truth.
Source values, relations, units, text outcomes and validity comments remain
unchanged. No species, application dose, timing or endpoint pooling is implicit.
Raw structures can later enter the structural analysis after identity review.

Each call targets one explicit assay under a caller-specified activity bound.
The complete bundle is published atomically only after stable page counts,
unique activity IDs and matching assay/document references are verified. Local
snapshots are immutable through this entry point; no silent refresh or partial
snapshot is treated as complete. Existing outputs require a new root to refresh.
Concurrent writers must be serialized. Source version and requests are recorded,
but separate API requests cannot establish a transactional source snapshot.

Requests stay on the fixed EMBL-EBI API origin, use explicit ordered offsets,
pace calls and have finite timeouts. Remote next links cannot redirect traversal.
Transport failures propagate without retries or publication; the user can rerun
against the same root after a failure. Collections and generated evidence stay
ignored; unit tests use synthetic payloads rather than live network responses.

## ECOTOX inventory preflight — 2026-11-10

Introduce a separate source namespace and offline bulk-ZIP inventory before the
full ECOTOX measurement adapter. The inspected official snapshot establishes
actual chemical/test/result/reference/species keys. Read quoted pipe-delimited
ASCII with strict widths; preserve sentinels and qualifiers in bounded raw
samples, and reject broken core relationships before publishing output. Native
chemical keys remain usable without PubChem/CompTox identities. DTXSID crosswalk
overlaps are candidates requiring source-specific approval. No normalized hazard
rows, inferred plant labels or mammalian LD50 comparisons are emitted. See the
[preflight contract](epa-chembl.md#ecotox-bulk-inventory-preflight).

## Selected ECOTOX observations and context policies — 2026-11-11

Keep native snapshot/result grain separate from concentration-slot measurements;
equal values do not establish duplicate experiments. Source identity decisions are
independent of the existing CompTox crosswalk, and canonical IDs require explicit
source-specific approval. Decode the frozen source vocabulary and retain unknown
codes/reasons. Potency policies require effect **and measurement**, including ITX/
IMBL for Daphnia immobilization, explicit elapsed observation duration, water
medium, concentration basis, exposure analysis and a recognized pure/active form.
Keep exposure-analysis strata separate. Publish only complete staged products.
See [selected import](epa-chembl.md#complete-selected-cohort-ecotox-import).
