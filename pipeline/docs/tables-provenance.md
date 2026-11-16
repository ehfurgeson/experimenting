# Tables and provenance

[Component quickstart](../README.md) · [Repository documentation](../../docs/README.md)

Commands below run from the `pipeline/` directory. Real-data examples require the local inputs described in the [data guide](../../docs/data.md).

## Typed tables and provenance

`agrotox.tables.frame_from_rows(rows, schema)` builds a Polars table against an
explicit schema. Empty and all-null columns retain their specified types;
invalid numeric text raises rather than becoming null. Stage schemas are
defined as their corresponding data products are introduced.

`agrotox.storage.save_table(path, frame, sources, code_version = "0.1.0")` writes
native Parquet using the frame's own column order and types, including nested
lists and structs. No pandas or PyArrow installation is required. It also writes
a sibling sidecar: `compounds.parquet` produces `compounds.metadata.json`.
The sidecar contains a UTC generation timestamp, code version, row count, and
SHA-256 hashes keyed by the supplied dependency paths.

Supply every file consumed by the stage, including query aliases, metadata, raw
and processed inputs, configuration, and implementation files. Hashes are
computed before outputs change. Missing dependencies raise; output paths may not
overwrite dependencies. Callers keep dependencies stable during computation and
saving so the hashes describe the inputs actually used.

`agrotox.tables.read_table(path, schema)` reads a required Parquet file and checks
exact column names, order, and types without casting. Missing or corrupt files
raise; a valid typed empty table succeeds. Omit `schema` to read the file's own
schema without an expected-schema check. This reader does not validate sidecars.

Table and sidecar files are replaced individually, not as a transaction. See
[table persistence decisions](decisions.md#typed-table-persistence) for the
failure boundary. Run the focused checks with `uv run pytest tests/test_tables.py -q`.
