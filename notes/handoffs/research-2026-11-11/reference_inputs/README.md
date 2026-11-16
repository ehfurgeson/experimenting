# Read-only evidence inputs

These are compact copies and excerpts for the 11 November handoff. Do not edit
these reference files; record new work under `../work/` with your own run ID.
The package inventory distinguishes exact source copies from derived excerpts.

- `toxicity/`: 41 aquatic records, 16 rat-review records, their 57 native contexts,
  20 bibliographic leads, 26 rat-priority overlap pairs and their EPA counterparts,
  historical rat baseline, approved identities and source coverage.
- `biology/`: actual adoption ledgers, 119 second-pass treatment observations,
  80 accepted activity feature rows, origin/structure information, held source
  crosswalks, original assay history and per-policy seven-column labels.
- `models/`: saved reports for the separate 171- and 30-compound tasks and
  interpretation tables. These contain no fitted estimator objects.

The label CSVs for M2020, T2024 and D2015 have no known activity labels despite
`HUMAN-` in their filenames. Refer to the guide, not the prefix alone. Historical
`NOT_FOR_TRAINING`, `AI-only` or pending-signoff text is retained verbatim in source
history; current acceptance is documented by the adoption ledgers and supplied
human-adoption statements. Explicit unresolved outcomes/identity holds persist.

`ecotox_native_context_excerpt.json` stores original native fields as JSON strings
inside each record. Decode e.g. `json.loads(record["test_json"])` to inspect source
test context. It is an excerpt, not the complete selected ECOTOX dataset. PDFs,
credentials, raw archives and the complete code checkout are not included.
