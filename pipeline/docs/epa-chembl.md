# EPA and ChEMBL evidence

[Component quickstart](../README.md) · [Repository documentation](../../docs/README.md)

Commands below run from the `pipeline/` directory. Real-data examples require the local inputs described in the [data guide](../../docs/data.md).

## EPA compound identity

`agrotox.sources.comptox.ComptoxClient` reads EPA CompTox chemical records.
It sends the API key in a request header only, so the key never appears in a
URL, a cached snapshot, or an error message. Construction performs no request,
and the client needs `COMPTOX_API_KEY` in the environment or an explicit
`api_key` argument before it can be used. The exact-search endpoint documents
its 400 response as "data not found", so a term with no match is an empty
result and not an error; the near-miss identifiers the provider offers with it
are returned alongside the result.

`agrotox.epa_identity.resolve_identities(root, compounds, client)` searches EPA
for every selected compound, reusing any cached search, and returns the
candidate table and the crosswalk. A compound is searched by its full InChIKey
first and by its preferred name afterwards.

`agrotox.epa_identity.identity_candidates(compounds, evidence)` keeps every
candidate with its identifiers and the strength of its match: `exact_structure`,
`connectivity_only`, `name_only`, or `none`. The strength compares the
compound's InChIKey with the candidate's own chemical record, because the
search response does not carry a structure. The candidate row keeps that
record's formula, structure, and assay counts, and the provider's near-miss
suggestions are kept for a search that found nothing.
`agrotox.epa_identity.identity_crosswalk(compounds, candidates)` gives each
compound one status: `approved`, `unresolved`, or `needs_review`, with the
reason and the number of candidates. Only a single candidate with the same
full InChIKey is approved. `agrotox.epa_identity.identity_review_queue` returns
the rows that need a human decision.

The PubChem CID stays the internal compound key. A DTXSID is an external
resolved identifier, and an unresolved or ambiguous mapping never triggers
downstream retrieval. The raw EPA responses are cached under
`raw/comptox/chemical/search/` and can rebuild the crosswalk offline.

Run the focused checks with `uv run pytest tests/test_epa_identity.py -q`.


## ToxCast assay evidence

`agrotox.toxcast.fetch_toxcast(root, crosswalk, client)` retrieves the in-vitro
bioactivity records of every approved compound and returns the assay evidence
table and its coverage table. Only a compound with an approved DTXSID is
requested, so an ambiguous identity never attaches the wrong evidence to the
wrong chemical. Cached responses are reused, and the same cached response
always reparses to the same rows.

`agrotox.toxcast.parse_bioactivity(records, compound_id, dtxsid, annotations,
retrieved_at)` reads the source records into typed evidence. Each row keeps the
assay endpoint, its function, target, technology, organism, tissue, cell
format, and timepoint, together with the hit call, activity value, benchmark
dose, concentration range and unit, response range, model, and fit category.

A substance that was never tested in an assay has no row for it. A substance
that was tested and showed no activity keeps its row and is marked `inactive`,
so the two are never confused. The hit call is a continuous value: a positive
call is an active curve, a negative call is an inactive one, and a call of
exactly zero is neither, and the coverage table counts the three states
separately. `measurement_kind` distinguishes a fitted assay metric from a
directly observed endpoint, and `evidence_class` records that the evidence is
experimental. An assay result is never converted into an LD50, an LC50, or any
other acute toxicity endpoint, and the assays are never merged into a single
toxicity number.

`agrotox.toxcast.toxcast_coverage(assays)` reports the number of assays with a
result, the number with a hit, the number inactive, the number whose call is
exactly zero, and the number of distinct target families, for each compound.

Run the focused checks with `uv run pytest tests/test_toxcast.py -q`.


## EPA experimental hazard

`agrotox.epa_hazard.fetch_hazard(root, crosswalk, client)` retrieves the hazard
observations of every approved compound and returns three tables: the hazard
evidence, its coverage, and the comparison input the existing matching rules
use. Only an approved DTXSID is requested, and a cached response is reused.

`agrotox.epa_hazard.parse_toxval(records, compound_id, retrieved_at)` keeps
the source fields of each observation: the endpoint and its definition, the
value and its unit, the qualifier, the species, the exposure route, method,
form, and medium, the study duration, the study type, the effect, the
guideline, the quality flags, the bibliographic reference, and whether the
record is experimental or predicted. That classification comes from the record
itself.

`agrotox.epa_hazard.as_comparison_input(hazards)` maps the records onto the
pipeline's comparison contract. Only records explicitly marked `experimental`
are eligible; nonexperimental, undetermined, and unmarked records remain in the
hazard evidence table but are excluded from comparisons.
LD50, LC50, EC50, NOAEL, LOAEL, BMD, and BMDL are mapped when the unit
converts cleanly through the endpoint unit rules. A record with
an incompatible unit or an unsupported endpoint stays outside the comparison,
where it remains inspectable in the hazard table. The source marks a record as
`experimental`, `not experimental`, or `undetermined`, and the duration is
often absent: a negative sentinel or a unit the pipeline does not convert
leaves the duration unknown rather than failing.

`agrotox.epa_hazard.normalize_hazards(hazards)` returns one normalized annotation
per source record, including partial/failed rows with `parse_note` review reasons.
`source_record_json` in the hazard table preserves every source field, including
unrecognized metadata; normalized `information_json` and source provenance keep
that original record. Stable annotation IDs include compound identity and source
content, excluding retrieval time. Older hazard tables without this JSON field
can still normalize using their retained typed fields; rebuilding from raw caches
recovers the full original record.

Study type, duration class, and effect use trimmed lowercase source text;
placeholder values stay null. Species use lowercase Latin names when supplied,
otherwise common names, so EPA-specific species definitions must use that
spelling. BMD/BMDL are tagged `evidence_basis: model_derived` even when the source
marks them experimental. A label such as `BMDL (10)` retains the response token
`"10"` and the original label, without assuming its risk interpretation. The
current adapter leaves model, confidence, response interpretation, and study
link fields null because the source contract does not supply them explicitly.
It never fabricates a BMD to accompany a BMDL.

`agrotox.epa_hazard.hazard_coverage(hazards)` reports the number of records,
experimental records, distinct endpoints, distinct species, and distinct
references for each compound.

Run the focused checks with `uv run pytest tests/test_epa_hazard.py -q`.


## Offline EPA hazard analysis

`agrotox.epa_workflow.build_epa_hazard_offline(root, queries, definitions)`
returns an `OfflineAnalysis` from selected PubChem identities, the required
`epa_identity_crosswalk.parquet`, and the raw hazard JSON of selected approved
DTXSIDs. It makes no requests and changes no input files. It rebuilds normalized
rows from raw evidence instead of trusting previously saved comparison inputs.
Selected approved identities require a cached response; missing files raise
`FileNotFoundError`, and invalid envelopes or mismatched substance identifiers
raise `ValueError`. Unapproved and unselected hazard caches are not read.

The eleven tables are `compounds`, `hazards`, `annotations`, `measurements`,
`coverage`, `coverage_by_group`, `comparison_records`, `compound_summary`,
`group_summary`, `audit`, and `review_queue`. Coverage denominators include
every selected compound. The EPA-specific audit distinguishes unapproved or
absent crosswalk identities, empty saved responses, reviewable extraction,
context mismatches, and matching evidence. It does not reuse PubChem retrieval
states. Raw-file paths and source JSON accompany review rows; dependency hashes
cover the selected evidence and crosswalk.

`examples/endpoints.yaml` includes the existing acute policies plus four
oral mammalian daily-dose point of departure availability policies, covering
all seven endpoint types. It does not include an algal policy. Run the offline
example from the repository root:

```bash
uv run --project pipeline python pipeline/examples/analyze_epa_hazards.py \
  --data experiments/data --input experiments/data/compounds.csv \
  --output pipeline/.live-smoke/chronic-endpoints
```

Omit `--output` to inspect without writing. With an output directory, each table
is written as Parquet with a dependency-hash metadata sidecar, including input
selection, policies, and implementation files. These products are separate from
existing experimental results; regenerate older comparison products before
using them with the expanded schema.

The [cached evidence checkpoint](point_of_departure_check.md) records
verified coverage, source limitations, and the distinction between rebuilt
outputs and stale experiment comparison tables.

Run the focused checks with `uv run pytest tests/test_epa_workflow.py -q`.


## EPA chemical properties

`agrotox.epa_properties.fetch_properties(root, crosswalk, client)` retrieves the
experimental and the predicted property records of every approved compound and
returns the long-form property table and its coverage. Only an approved DTXSID
is requested, the two responses are cached separately, and a rerun makes no
request for a response that was already retrieved.

`agrotox.epa_properties.parse_properties(records, compound_id, origin,
retrieved_at)` keeps one row per property per source. A row holds the property
name, the value and its unit, the original text, the source name and
description, the public source URL, the dataset, the model name and identifier,
and the applicability domain fields when the source supplies them.

`property_origin` is `measured` for a record from the experimental property
endpoint and `calculated` for a record from the predicted property endpoint.
The endpoint each row came from is kept in `source_endpoint`, so the basis of
every value is visible. A missing optional trait is null; a value is never
replaced by zero.

The PubChem property values are not touched. The EPA and the PubChem values
for the same compound both exist, each in its own row with its own source, and
neither overwrites the other.

`agrotox.epa_properties.property_coverage(properties)` reports the number of
properties, measured properties, calculated properties, and distinct sources
for each compound.

Run the focused checks with `uv run pytest tests/test_epa_properties.py -q`.


## EPA TEST predictions

`agrotox.epa_test.fetch_test_predictions(root, crosswalk, client)` reads the
TEST predictions the provider has already stored for the approved identities,
and returns the prediction table and its coverage.

This stage never predicts a new molecule. It does not post a SMILES or an
InChIKey anywhere, and there is no function that runs a model on a novel
structure. The only input is a stored prediction for a compound whose EPA
identity is already approved, and the cached predicted-property response is
reused when there is one.

`agrotox.epa_test.parse_test_predictions(records, compound_id, retrieved_at)`
keeps only the records the source attributes to a TEST model, and keeps the
model name and identifier, the endpoint, the predicted value and its unit, the
applicability domain method, value, conclusion, and reasoning, and the quality
reference. Every row records `evidence_class` as `predicted`.

Reparsing also retains `provider_record_id`, `source_name` (including the raw
version label, for example TEST5.1.3), source description, DTXCID, provider and
QSAR structures, endpoint description, provider error text and the complete
`source_record_json`. Numeric/nontext error metadata remains recoverable in that
JSON. Embedded `provider_experimental_value`/`provider_experimental_text` are
unreviewed comparators, not admissions to measured evidence: their original study,
chemical form and training lineage need a separate audit. Older stored tables
require reparsing immutable raw responses to recover these fields. Missing fields
remain null. Provider Inside is a domain conclusion, not an accuracy guarantee.

`agrotox.epa_test.prediction_coverage(predictions)` reports the number of
predictions, the number of distinct models, and the number of predictions the
source places outside the model's applicability domain.

A prediction is never included in a measured endpoint median or in the
experimental coverage. A compound with no stored prediction has none, and that
absence is never recorded as a value of zero.

Run the focused checks with `uv run pytest tests/test_epa_test.py -q`.


## Bounded ChEMBL assay snapshots

`agrotox.chembl.fetch_assay(root, assay_id, http = None, page_size = 1000,
max_activities = 10000, sleep = None)` freezes one explicit ChEMBL assay into
`root/raw/chembl/<assay_id>.json`. The bundle preserves the API database version,
retrieval time, requested URLs/parameters, assay description, source publication,
and every raw activity page, including structures, source values, qualifiers,
validity comments and unrecognized fields. It does not assign activity labels.

Identifiers must be positive `CHEMBL` IDs. Page size is 1–1000; the positive
activity bound rejects oversized assays before downloading further pages.
Pagination uses a fixed endpoint, explicit offsets and activity-ID ordering;
server-provided next links are preserved but never followed. Invalid shapes,
duplicate activity IDs, mismatched assay/document identities, changing counts,
and incomplete pages raise `ValueError` without publishing a snapshot. Network
and HTTP errors propagate. Requests have connection/read timeouts and a minimum
250 ms pause between calls; there is no automatic retry.

Publication uses the atomic JSON writer only after every page passes validation.
An existing snapshot raises `FileExistsError`; choose a new root to refresh it.
Serialize writers to a root. Count/identity checks cannot guarantee an upstream
API transaction or detect equal-count edits during retrieval. Missing structures
and ambiguous measurements remain source records for explicit review.

From the repository root:

```bash
uv run --project pipeline python pipeline/examples/fetch_chembl_assay.py CHEMBL3079324 --data analysis/outputs/chembl-example --max-activities 500
```

Run the focused checks from `pipeline/` with
`uv run pytest tests/test_chembl.py -q`.

## ECOTOX bulk inventory preflight

A bounded offline preflight is available before full measurement ingestion:

```bash
UV_CACHE_DIR=pipeline/.uv-cache uv run --project pipeline --locked python -m agrotox.ecotox_inventory \
  --source experiments/data/raw/ecotox/<snapshot>/source.zip \
  --crosswalk experiments/data/epa_identity_crosswalk.parquet \
  --output analysis/outputs/ecotox-inventory-<date>-<run>
```

Download an official archive explicitly from [EPA's ECOTOX home page](https://cfpub.epa.gov/ecotox/)
and preserve its URL, retrieval time, HTTP metadata and SHA256. No key or network
is used by preflight. The inspected September 15, 2026 archive contains pipe-delimited
ASCII tables with chemical/test/result keys and PDF dictionary/help dated September
2024. The archive release date and dictionary revision are distinct.

The command accepts a single-root bulk ZIP containing `validation/chemicals.txt`,
`validation/references.txt`, `validation/species.txt`, `tests.txt` and `results.txt`.
It reads pipe-delimited records with CSV quoting (some comment fields contain
quoted pipes) and checks headers, row widths, core primary keys and test/result foreign keys,
without extracting archive members. It inventories every source chemical before
joining candidate DTXSID overlaps with an optional existing approved crosswalk.
Those overlaps are candidates only; this workflow does not approve source identity.
`ECOTOX:chemical:<cas_number>` is a namespaced native key; the numeric source field
is retained as text and is not asserted to be a validated CAS registry number.

New output directories contain CSV/Parquet chemical and ZIP-member inventories,
a bounded raw sample (default 25 per LD50, LC50, EC50, and other plant endpoint),
and a manifest with input/code/lock/product hashes, release notes, counts and
endpoint distribution. Sampling follows archive order and is not representative.
Sample rows preserve native result/test/reference/species context as JSON and
source line locators; qualifiers and source sentinel text are not normalized.
The complete immutable ZIP remains the evidence source. Empty samples are valid.

This is an inventory prototype, not the complete proposed ECOTOX adapter. It
performs no endpoint/unit normalization, toxicity binning, natural-occurrence
assignment or biological labeling. Core validation does not validate every ancillary
dose/media table relationship. Full source ingestion, controlled-vocabulary mapping,
approved identity links and study-overlap adjudication remain separate increments.

## Complete selected-cohort ECOTOX import

`python -m agrotox.ecotox_selected --source <official.zip> --chemical-ids <cohort.csv>
--crosswalk <source-decisions.csv> --policies <explicit-policies.yaml> --output <new-directory>`
imports every selected test/result, offline. The cohort CSV contains unique
`source_chemical_id` strings. Source decisions use `source_chemical_id`,
`compound_id`, `status`, `match_type`, `source_identity_reference`, `reviewer` and
`review_date`. Candidate IDs are review hints only. Canonical attachment requires
`approved`, `exact_structure`, a source-identity reference and reviewer/date;
unknown/conflicting/rejected rows retain native source identity only. These fields
record an approval assertion, not independent verification of the reviewer.

`native_observations` has one row per snapshot/result ID, raw test/result/species/
chemical/reference JSON and logical CSV record locators. `measurements` has one
row per occupied concentration slot (or an explicit missing-value placeholder),
with immutable snapshot/result/slot IDs. Slots are not independent studies.
Scalar inequalities and explicit min/max ranges remain distinct; unknown codes,
units, qualifiers and missing values remain reviewable. Exact LD50/LC50/EC50
codes are supported; log-transformed and other endpoints are not silently mapped.
Concentration basis, chemical analysis and formulation codes are preserved.
Observed duration is distinct from exposure duration; event-relative units such
as hours post hatch do not become elapsed hours.
Explicit elapsed `h`, `d` and `wk` codes must exist in the snapshot dictionary;
weeks convert at 168 hours per week. Inequalities remain unknown scalar durations,
and months/event-relative units are not converted. This preserves a native
two-week observation as 336 hours without asserting continuous exposure or acute
eligibility. Rebuild into a new directory to use the expanded unit support;
historical normalized exports and manifests are unchanged.

Frozen dictionary codes decode the source fields. In particular, `IMM` means
immunological; immobilization is measurement `IMBL` with effect `ITX`. The example
`examples/ecotox_policies.yaml` requires species, effect, measurement, elapsed
duration, medium, unit, concentration basis, formulation and analysis method.
Measured (`M`) and unmeasured (`U`) exposures remain identifiable and must be
reported separately. Unknown formulation/basis excludes potency admission, even
when conversion succeeds. The examples are conservative, not claims of uniform
study quality or direct observation of every fitted effect estimate.

Coverage reports source-context eligible slots **and distinct results**, preserving
selected zero-hit chemicals. Canonical coverage is null until identity approval;
an assessed zero is not plant inactivity. Admission exports explain each endpoint/
species candidate's exclusions. CSV/Parquet pairs, decoded dictionaries and a
manifest are published through a temporary sibling directory only after all
products are written. A new output directory is required; interrupted publication
cannot leave a completed output bundle. Input/code/lock/product hashes are recorded.
This extends inventory preflight without changing existing EPA/PubChem schemas,
union coverage flags or historical bundles.
