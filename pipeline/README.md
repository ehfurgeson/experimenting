# Agrotox pipeline

Agrotox is the maintained Python package for auditable evidence retrieval and
analysis. It implements PubChem retrieval and caching, identity reconciliation,
annotation normalization, endpoint matching, coverage, comparison records and
context-constrained summaries. EPA identity, hazard, property, ToxCast and TEST
adapters and bounded ChEMBL assay snapshots retain their own evidence provenance.
An offline ECOTOX bulk inventory preflight preserves source chemicals and bounded
raw evidence before full measurement ingestion; see the EPA/ChEMBL guide.

Use the Python API and the scripts in `examples/`; there is no unified installed
CLI. Live retrieval is separate from offline processing and testing. See the
[repository overview](../README.md), [architecture](../docs/architecture.md) and
[data prerequisites](../docs/data.md).

## Minimal offline example

After setup below, run from `pipeline/`:

```bash
uv run python -c 'from agrotox.inputs import classify_query; print(classify_query("009750"))'
```

Expected: `('cid', '9750')`. This needs no research bundle or API key.

Choose a guide: [inputs/identity](docs/inputs-identity.md),
[retrieval/cache](docs/retrieval-cache.md), [tables/provenance](docs/tables-provenance.md),
[normalization](docs/normalization.md), [endpoints/comparisons](docs/endpoints-comparisons.md),
or [EPA/ChEMBL](docs/epa-chembl.md). The [decision record](docs/decisions.md)
explains the contracts and rationale.

## Setup and verification

Requires Python 3.12 or newer and `uv`. Run from this directory:

```bash
uv sync --locked
uv run pytest tests/test_setup.py -q
uv run pytest -q
uv run ruff check .
```

The lockfile pins runtime and development dependencies. Setup may download
dependencies; tests use local synthetic JSON and block Requests calls, including
explicit sessions. Generated test outputs should use pytest's `tmp_path`.
The test suite checks that `agrotox` imports from this project's `src/` directory
and that its version agrees with the installed distribution metadata.

Python code uses one space on each side of `=`, including keyword arguments
and parameter defaults (for example, `timeout = 1`). Ruff linting is enabled;
its formatter excludes Python files because it cannot preserve this spacing.

If the default uv cache is unavailable in a sandbox, prefix each uv command with
`UV_CACHE_DIR=.uv-cache`. This project-local cache is ignored by Git.

## Project layout

- `pyproject.toml`: package metadata, dependencies, and tool configuration.
- `uv.lock`: pinned dependencies.
- `src/agrotox/`: package source code.
- `examples/inspect_snapshots.py`: runnable offline ingestion, normalization, and source previews.
- `tests/conftest.py`: shared fixtures and Requests network blocking.
- `tests/test_setup.py`: package installation and offline infrastructure checks.
- `tests/fixtures/`: synthetic JSON and [fixture documentation](tests/fixtures/README.md).

Synthetic data is for testing only and must never be submitted as live chemical
queries or cited as measured toxicity.

## Detailed guide links

Former section anchors are retained below for existing bookmarks.

## Chemical queries

See [Chemical queries](docs/inputs-identity.md#chemical-queries).

## Curated input files

See [Curated input files](docs/inputs-identity.md#curated-input-files).

## Compound identities

See [Compound identities](docs/inputs-identity.md#compound-identities).

## Raw JSON storage

See [Raw JSON storage](docs/retrieval-cache.md#raw-json-storage).

## Cache validation

See [Cache validation](docs/retrieval-cache.md#cache-validation).

## Typed tables and provenance

See [Typed tables and provenance](docs/tables-provenance.md#typed-tables-and-provenance).

## PubChem source adapter

See [PubChem source adapter](docs/retrieval-cache.md#pubchem-source-adapter).

## Resumable retrieval

See [Resumable retrieval](docs/retrieval-cache.md#resumable-retrieval).

## Source annotations

See [Source annotations](docs/retrieval-cache.md#source-annotations).

## Selected snapshot tables

See [Selected snapshot tables](docs/retrieval-cache.md#selected-snapshot-tables).

## Study and benchmark context

See [Study and benchmark context](docs/normalization.md#study-and-benchmark-context).

## Shared endpoint policy

See [Shared endpoint policy](docs/endpoints-comparisons.md#shared-endpoint-policy).

## Units and durations

See [Units and durations](docs/normalization.md#units-and-durations).

## Numeric values and uncertainty

See [Numeric values and uncertainty](docs/normalization.md#numeric-values-and-uncertainty).

## Annotation normalization

See [Annotation normalization](docs/normalization.md#annotation-normalization).

## Point of departure comparisons

See [Point of departure comparisons](docs/endpoints-comparisons.md#point-of-departure-comparisons).

## Endpoint definitions and matching

See [Endpoint definitions and matching](docs/endpoints-comparisons.md#endpoint-definitions-and-matching).

## Compound endpoint coverage

See [Compound endpoint coverage](docs/endpoints-comparisons.md#compound-endpoint-coverage).

## Comparison records

See [Comparison records](docs/endpoints-comparisons.md#comparison-records).

## Compound and group summaries

See [Compound and group summaries](docs/endpoints-comparisons.md#compound-and-group-summaries).

## Extraction audit and review queue

See [Extraction audit and review queue](docs/endpoints-comparisons.md#extraction-audit-and-review-queue).

## Offline workflow

See [Offline workflow](docs/endpoints-comparisons.md#offline-workflow).

## EPA compound identity

See [EPA compound identity](docs/epa-chembl.md#epa-compound-identity).

## ToxCast assay evidence

See [ToxCast assay evidence](docs/epa-chembl.md#toxcast-assay-evidence).

## EPA experimental hazard

See [EPA experimental hazard](docs/epa-chembl.md#epa-experimental-hazard).

## Offline EPA hazard analysis

See [Offline EPA hazard analysis](docs/epa-chembl.md#offline-epa-hazard-analysis).

## EPA chemical properties

See [EPA chemical properties](docs/epa-chembl.md#epa-chemical-properties).

## EPA TEST predictions

See [EPA TEST predictions](docs/epa-chembl.md#epa-test-predictions).

## Bounded ChEMBL assay snapshots

See [Bounded ChEMBL assay snapshots](docs/epa-chembl.md#bounded-chembl-assay-snapshots).
