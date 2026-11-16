# Inputs and compound identities

[Component quickstart](../README.md) · [Repository documentation](../../docs/README.md)

Commands below run from the `pipeline/` directory. Real-data examples require the local inputs described in the [data guide](../../docs/data.md).

## Chemical queries

`agrotox.inputs.classify_query` strips surrounding whitespace and returns a
`(kind, value)` pair. ASCII decimal strings represent positive PubChem CIDs:
`"009750"` and `"9750"` both return `("cid", "9750")`. Blank inputs and all-zero
CIDs raise `ValueError`. All other nonblank strings are names, including
`"1,8-cineole"` and strings containing non-ASCII digits.

`agrotox.inputs.query_key` returns the full SHA-256 hex digest of the query kind
and canonical text, separated by a colon. Names use stripped, casefolded text;
internal whitespace remains significant. Keys are safe filename components and
stable across processes. Different chemical synonyms retain distinct keys until
their compound identities are resolved.

The `Query` type in `agrotox.contracts` keeps the trimmed input spelling in
`query`, separately from its derived key, and allows optional curated group,
subgroup, HRAC group, and source-note fields. Merging equivalent records retains
the first spelling.

Run the focused query checks with `uv run pytest tests/test_inputs.py -q`.


## Curated input files

Use `agrotox.inputs.load_queries(Path("chemicals.csv"))` to load a CSV or TXT
file. Files use UTF-8, with an optional BOM. Empty files return an empty list;
missing files raise `FileNotFoundError`. Blank rows and comments beginning with
`#` in the first cell or at the start of a TXT line are ignored.

Headered CSV uses `query` and any of `chemical_group`, `subgroup`, `hrac_group`,
and `source_note`, in any order. Headers and values are trimmed. The first
noncomment row is treated as a header when any cell matches one of these field
names; it must include `query`. Duplicate or unsupported headers, missing or
extra cells, blank queries, and malformed quoting raise `ValueError` with the
input path. Quote names containing commas in CSV:

```csv
query,chemical_group,source_note
"1,8-cineole",natural_product,curated selection
009750,,numeric CID
```

Headerless CSV uses its first column and ignores subsequent columns. TXT uses
one whole query per line, so `1,8-cineole` needs no quoting. Only `.csv` and
`.txt` extensions are supported, case-insensitively.

`agrotox.inputs.merge_queries` accepts an iterable of `Query` records, including
combined file inputs and manually supplied queries. Both loading and merging
return one record per canonical key in first-seen order, keeping the first
trimmed spelling. Blank or absent metadata can be enriched by a nonempty value;
conflicting nonempty values in any curated field raise `ValueError` naming the
query and field. Metadata comparisons are case-sensitive after trimming. Input
records are not mutated, and unsupported fields or nonstring values are rejected.


## Compound identities

`agrotox.identity.reconcile_compounds(queries, snapshots)` combines selected
queries with hand-built or retrieved identity snapshots. Each snapshot is keyed
by its input query spelling and contains a positive integer `cid`, a single
`properties` record, and a `metadata` mapping. The properties record is not a
REST response envelope. This function performs no disk or network operations.

Aliases resolving to the same CID share one `PUBCHEM:<CID>` compound row.
Queries without snapshots remain unresolved as `QUERY:<query_key>`, preserving
their place in the selected compound universe. Rows retain `input_queries` and
distinct `source_notes` as lists in first-seen order. Blank classifications can
be enriched; conflicting nonempty group, subgroup, or HRAC labels raise errors.
Distinct CIDs remain distinct, including salts and esters.

Missing structures remain null. Stereochemical and connectivity SMILES occupy
separate fields. Molecular weight is a positive finite float when supplied.
Retrieval status comes from snapshot metadata, independently of identity status;
a resolved compound can have pending or missing toxicity data.

`agrotox.tables.compound_table(rows)` constructs a Polars DataFrame with an
explicit nullable schema, including typed lists, integer CIDs, and Float64
molecular weights. Empty inputs retain the same schema.

See [identity decisions](decisions.md) for field precedence and conflict
policies. Run the focused checks with `uv run pytest tests/test_identity.py -q`.
