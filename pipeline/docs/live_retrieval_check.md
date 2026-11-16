# Live retrieval checkpoint

Checked October 15, 2026, separately from the synthetic offline test suite.

## Provider guidance and selection

Reviewed PubChem's [PUG REST usage policy](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest)
and [dynamic throttling guidance](https://pubchem.ncbi.nlm.nih.gov/pcfe/docs/markdown/dynamic-request-throttling.md).
The policy limits clients to five requests per second; the throttling guidance
also describes changing service load and HTTP 503 responses. This small check
used sequential calls with `interval = 1.0`, the default bounded retry policy,
and no force refresh.

Selected names were checked against the compound pages for
[Caffeine](https://pubchem.ncbi.nlm.nih.gov/compound/2519) and
[Citric Acid](https://pubchem.ncbi.nlm.nih.gov/compound/311). Numeric CID 2244
was reviewed as Aspirin using PubChem's
[compound-page documentation](https://pubchem.ncbi.nlm.nih.gov/docs/compound-page).
These are retrieval examples, not the curated analysis selection.

## Observations

| Input | Returned CID | Property title | Formula | Toxicity status |
| --- | --- | --- | --- | --- |
| caffeine | 2519 | Caffeine | C8H10N4O2 | found |
| citric acid | 311 | Citric Acid | C6H8O7 | found |
| 2244 | 2244 | Aspirin | C9H8O4 | found |

Eight HTTP requests returned 200: two name lookups, three property requests, and
three Toxicity-section requests. Property envelopes each contained one matching
CID. PUG-View envelopes had matching RecordNumber/RecordType and a Toxicity
heading. No absence or remote error occurred; synthetic tests cover these states
deterministically. Request-count/time feedback remained green; service-load
feedback varied, including red and black responses. No further live fetches were
needed after this small checkpoint.

The second pass returned `skipped` for all three queries with **zero HTTP
requests** and unchanged raw-file hashes. Snapshot counts and source values are
observations, not permanent regression expectations or toxicity conclusions.

## Local evidence

The separate data root is `.live-smoke/2026-10-15/`, ignored by Git. It contains:

- `raw/pubchem/queries/<key>.json`: query aliases and input metadata.
- `raw/pubchem/2519/`, `311/`, and `2244/`: property, toxicity, and metadata JSON.
- `observations.json`: outcomes, repeat-run results, identity inspection, HTTP
  statuses, and throttling feedback.

Review these files locally; the ignored directory is not distributed in a fresh
checkout. The checkpoint does not add live-response assertions to pytest.

## Offline annotation inspection

The saved snapshots were subsequently flattened without network access. Caffeine
produced 170 annotation representations, citric acid 73, and Aspirin 136. Raw
toxicity-file SHA-256 hashes were unchanged. These counts describe only the saved
snapshots; they are not measurement counts or permanent test expectations.

## Offline ingestion tables

Selected queries caffeine, citric acid, and 2244 were assembled using
`parse_snapshots`, without new HTTP requests. The result was three compound rows
and 379 annotation representations. Example previews retained source text,
section paths, reference numbers, source URLs, and the matching raw-file paths.
These are source annotations, including narrative, rather than standardized
measurements.

Repeated execution produced equal frames. Native Parquet round-trips preserved
both schemas, including nested provenance. SHA-256 hashes of all 12 raw JSON files
were unchanged. The ignored local data root additionally contains:

- `ingestion_selection.json`: the explicit query selection used for assembly.
- `interim/pubchem_annotations.parquet` and `interim/pubchem_annotations.metadata.json`.
- `processed/compounds.parquet` and `processed/compounds.metadata.json`.
- `ingestion_observations.json`: counts, output paths, and verification results.

Each product sidecar hashes the selection, selected aliases, bundle files, and
local implementation dependencies (24 files). These local outputs document this
checkpoint; fresh checkouts can always run the synthetic integration test without
the ignored cache.

## Offline annotation normalization

The saved real cache was normalized without new requests. Its 379 annotation
rows produced 13 complete, 14 partial, and 352 failed extraction rows. All source
rows remained present. Repeat frames and native Parquet round-trips were equal,
including nested provenance, and raw-file hashes were unchanged. These counts
describe this snapshot and vocabulary, not endpoint coverage or safety.

Inspected examples included:

- Caffeine annotation `sha256:46b5f2b82efa740080a4f758919f8d14928a7c7e5d90615738c41b717af4345d`:
  a direct rat intraperitoneal LD50 statement retained its source value and mg/kg
  unit, with reference 63 and the saved CID 2519 toxicity path.
- Citric-acid annotation `sha256:0b3b0a8b9771929b5b886b17597bb3a207893fbc134f6f53965e1854e01c7b9b`:
  a multi-compound interaction narrative contains a dose range for administered
  aluminum nitrate, not a direct citric-acid LD50 result. It remains partial for
  attribution review; its survival follow-up is not exposure duration. The full
  narrative, range, reference 63, source URL, and CID 311 raw-file path survive.
- An estimated human LD50 narrative remains partial because it contains
  approximation prose and competing values. General safety narrative without a
  supported endpoint remains failed rather than becoming a numeric result.

The real cache provided a reviewable range but no complete inequality threshold
under these rules. Synthetic cases independently verify exact, threshold, and
range conversions, including keeping the range scalar null. No unsupported case
was forced into the complete set to match a desired comparison.

Additional ignored local artifacts are
`processed/toxicity_standardized.parquet`, its `.metadata.json` sidecar, and
`normalization_observations.json` under `.live-smoke/2026-10-15/`. The observations
include full source/structured examples and verification results. Sidecar hashes
cover the explicit selection, raw bundle/alias inputs, and local implementation
files. The runnable inspection example displays these classifications and source
links without saving products or fetching data.
