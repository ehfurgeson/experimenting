# PubChem retrieval and cache behavior

[Component quickstart](../README.md) · [Repository documentation](../../docs/README.md)

Commands below run from the `pipeline/` directory. Real-data examples require the local inputs described in the [data guide](../../docs/data.md).

## Raw JSON storage

`agrotox.storage.write_json(path, payload)` creates missing parent directories
and writes UTF-8 JSON with readable Unicode. It flushes a unique temporary file
beside the destination, then atomically replaces the destination. A failed write
or replacement leaves any prior destination intact and removes the temporary
file. Nonfinite numbers such as NaN or infinity are rejected.

Paths are always derived from an explicit data root:

- `query_path(root, query)`: `raw/pubchem/queries/<query_key>.json`.
- `compound_path(root, cid, component)`: `raw/pubchem/<CID>/<component>.json`,
  where `component` is `properties`, `toxicity`, or `metadata`.

These path helpers validate identifiers and do not create directories. Each JSON
write is atomic on its own; writing a multi-file snapshot is not a transaction.
See [storage guarantees](decisions.md#json-storage) for details. Run the
focused checks with `uv run pytest tests/test_storage.py -q`.


## Cache validation

`agrotox.storage.read_snapshot(root, query)` reads the selected query alias and
validates its CID, raw property envelope, metadata, and toxicity envelope. A
missing alias returns `None`; a present alias referencing missing or corrupt
bundle files raises `ValueError`. Filesystem permission errors propagate.
The returned snapshot contains the single property record while saved raw JSON
remains unchanged.

`complete_record(root, cid)` checks a bundle independently of aliases. Valid
`found` and `missing` records are complete; absent, corrupt, and `pending` records
are not. Pending snapshots expose identity properties with `toxicity = None`,
without reading an older toxicity file. Missing sections require the explicit
`{"missing_section": "Toxicity"}` payload; malformed responses are errors.

Metadata must identify PubChem and the matching CID, supply a timezone-aware UTC
`retrieved_at`, and declare `found`, `missing`, or `pending`. Property responses
must contain exactly one matching CID. Found toxicity responses require a
PUG-View `Record` with the matching `RecordNumber`, `RecordType` of `CID`, and a
`Section` list or null.

The [cache recovery table](decisions.md#cache-state-and-recovery) describes
interrupted writes and the required refresh ordering.


## PubChem source adapter

`agrotox.sources.pubchem.PubChemClient` provides three operations:

- `resolve(query)`: return a positive integer CID. Numeric queries bypass HTTP;
  name lookup requires exactly one CID. Empty results raise `LookupError`, while
  ambiguous or malformed results raise `ValueError`.
- `properties(cid)`: request Title, MolecularFormula, MolecularWeight, SMILES,
  ConnectivitySMILES, InChI, InChIKey, and IUPACName, returning the validated
  original REST envelope.
- `toxicity(cid)`: retrieve the PUG-View Toxicity section. Its HTTP 404 returns
  `None`; successful responses return the validated original envelope.

The adapter accepts an injected HTTP client, and `agrotox.contracts.Source`
defines the smaller resolve/properties/toxicity boundary for orchestration and
fake sources. Construction performs no network request. Requests use a finite
connect/read timeout of `(10, 40)` seconds. Names are trimmed and URL-encoded as
one path segment, preserving punctuation and Unicode.

Only the Toxicity section's 404 means observed absence. Identity 404s and other
HTTP failures propagate as errors, as do transport failures and malformed JSON.
Successful property and toxicity responses use the same envelope validators as
the cache reader. The adapter performs no storage writes or toxicity-value
interpretation.

Redirects are disabled. HTTP 200 is accepted as successful; redirects and
asynchronous responses raise errors.

The default retry policy allows four retries after the first attempt, with
backoff delays of 1, 2, 4, and 8 seconds. It retries HTTP 429/500/502/503/504,
timeouts, and connection failures. SSL errors, permanent HTTP failures, malformed
JSON, and invalid envelopes do not retry. Exhaustion raises the final error.
`retries = 0` disables retries.

Request starts are paced at least 0.25 seconds apart, including failed attempts
and successive operations on the same client. The first request starts
immediately. A valid `Retry-After` integer-seconds or HTTP-date value can extend
backoff; malformed or expired values never shorten backoff. Pacing and retry
delays overlap, rather than being added together.

The constructor accepts `interval`, `retries`, and injected `clock`, `wall_clock`,
and `sleep` callables. The clock returns monotonic seconds; the wall clock returns
Unix epoch seconds for date headers. Production defaults use Python's time
functions. Requests session adapter retries are explicitly disabled, including
when a configured session is supplied. Other injected transports must perform
one attempt per `get` call. A client coordinates sequential calls; it is not a
shared concurrent rate limiter.

Run offline checks with `uv run pytest tests/test_pubchem.py -q`. Tests use fake
HTTP responses and fake clocks, forbid real sleeping, and make no live PubChem
requests.


## Resumable retrieval

`agrotox.retrieval.fetch_one(source, root, query, force = False)` retrieves one
curated query. `fetch_batch(source, root, queries, force = False)` validates and
merges the full selection before any requests, then continues independent queries
after remote or storage failures. Empty batches return an empty list; invalid or
conflicting batch inputs raise before writing files.

Each result contains `query`, nullable `cid`, `status` (`fetched`, `skipped`, or
`error`), `stage`, `error_type`, and `message`. Successful results have null error
fields. Error stages identify validation, cache access, resolution, property
retrieval, or the specific bundle write/request that failed.

Complete found/missing bundles are reused. Aliases that resolve to the same CID
share a bundle, and a new alias can reuse a complete bundle after resolution.
Alias files retain their first spelling and save the current curated input in
`input_metadata`. Corrupt cache content is repaired; filesystem access failures
are reported as errors. Pending snapshots reuse valid identity properties and
retry toxicity without another name or properties request.

`force = True` re-resolves the query and refreshes its evidence. Pending metadata
is committed before properties are replaced, followed by the alias, toxicity,
and terminal found/missing metadata. A failed toxicity request leaves readable
identity and hides any older toxicity file. Archive the selected data root before
force refresh when retaining evidence for a publication or report. Serialize
access to the data root; multi-file bundles are not transactions.

Run offline checks with `uv run pytest tests/test_retrieval.py -q`. A separate
[live checkpoint record](live_retrieval_check.md) describes reviewed real
queries, snapshots, and cache reuse; live data is not a test fixture.


## Source annotations

`agrotox.parsers.pubchem.flatten_sections(payload, cid = 101, raw_file = "saved.json",
retrieved_at = "2026-01-01T00:00:00Z")` walks nested PUG-View sections without
reading files or making requests. It returns annotation records with section
paths, record title, Information name/description, raw value and representation
kind, references, source URLs, Information URL, file location, and retrieval time.
Missing or null child sections and Information lists are empty.

`extract_values(value)` preserves StringWithMarkup text and numeric units.
Singleton numeric lists produce one scalar representation; lists with multiple
numbers stay together as `NumberArray`. Unknown representations remain
JSON-serialized for review. The full original Information object is also retained
in `information_json`, including markup and unfamiliar fields.

Each referenced source has its number, name, URL, and original `reference_json`.
Dangling reference numbers retain null source metadata. Distinct source records
sharing a reference number are all retained. Reference lists and source ordering
are canonicalized for stable identities, independently of traversal order.

Annotation IDs hash the compound, source context, full Information/value content,
and references. They exclude query aliases, file paths, timestamps, and traversal
positions. Reordering sections, Information entries, or reference declarations
does not change IDs for unchanged annotations. Repeated content keeps its rows
and can share an ID. Flattening does not identify independent studies or extract
standardized toxicity measurements.

See [annotation decisions](decisions.md#annotation-content-and-provenance).
Run focused checks with `uv run pytest tests/test_flatten.py -q`.


## Selected snapshot tables

`agrotox.workflow.parse_snapshots(root, queries)` returns `(annotations, compounds)`
as typed Polars DataFrames. It validates the selection, reads its query aliases,
loads each referenced CID bundle once, reconciles identities, and flattens each
found toxicity payload once. It performs no requests or writes.

Only selected queries contribute rows. Aliases resolving to the same CID share
one compound row and do not multiply annotations. Missing aliases remain
unresolved, even when an unrelated CID directory exists. Pending and missing
toxicity retain compound identities and explicit statuses without annotations.
Classification comes from the current curated selection, rather than saved alias
input metadata. Corrupt selected evidence raises; unrelated caches are not read.

The annotation schema retains typed section/reference lists and a List(Struct)
`sources` column, including complete reference JSON. Empty selections and found
records without annotations produce typed empty annotation tables. Compound
denominators include unresolved queries and compounds with no annotation data.

Run the synthetic integration checks with `uv run pytest tests/test_parse.py -q`.
They establish four compounds and seven annotations under a blocked network,
including alias invariance, nested Parquet round-trips, and unchanged raw hashes.

The runnable example accepts a curated input file and/or positional names/CIDs:

```bash
uv run python examples/inspect_snapshots.py --data .live-smoke/2026-10-15 caffeine "citric acid" 2244
uv run python examples/inspect_snapshots.py --data data --input chemicals.csv
```

Use the first command with the locally saved checkpoint cache; the second
illustrates supplying your own files. The example prints compound/status tables,
normalization counts, and source-linked exact, threshold, range, and review
previews when available. Check each preview's parse status: a parsed range or
threshold can still require review. The example does not fetch missing queries
or save products. The [checkpoint record](live_retrieval_check.md#offline-ingestion-tables)
lists the separately verified Parquet outputs from the saved real cache.
