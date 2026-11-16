# Current development and workflow guidance

Reviewed 2026-11-02. Every agent follows [required orientation](../AGENTS/README.md),
the [incremental guide](../INCREMENTAL_COMMIT_GUIDE.md) and
[documentation responsibilities](../AGENTS/DOCUMENTATION.md). This topic owns
environment and workflow commands.

## Environments and checks

Requires Python 3.12+ and uv. Commands run from the repository root:

```bash
uv sync --project pipeline --locked
uv sync --project analysis --locked
uv run --project pipeline pytest pipeline/tests -q
uv run --project analysis pytest analysis/tests -q
uv run --project pipeline ruff check pipeline
uv run --project analysis ruff check analysis
```

Setup can download dependencies. Existing tests use synthetic fixtures; pipeline
tests block Requests network access. The pipeline suite includes cross-component
analysis regressions with historical `test_experiment_*` names. Keep their environment
and network protection if reorganizing tests. See [test ownership](../../docs/architecture.md).

Use focused existing checks for behavior changes, then required relevant suites.
For documentation-only edits, verify links, anchors, paths and factual status;
a scientific rebuild is unnecessary. Historical test counts are not today's results.

## Research workflows

- [Cached rebuild/presentation](../../analysis/docs/cached-analysis.md): obtain an input bundle; no credentials/network retrieval during rebuild.
- [Structural screening](../../analysis/docs/structural-screening.md) and [diagnostics/review](../../analysis/docs/diagnostics-review.md): use fresh output directories and exact input manifests.
- [Live retrieval](../../pipeline/README.md): distinct acquisition work; EPA needs `COMPTOX_API_KEY`. Do not put credentials in docs, artifacts or logs.

Keep pipeline and analysis lockfiles separate; analysis installs sibling pipeline
as editable. Preserve flat analysis import/path conventions until a coherent
packaging change updates invocations, tests, manifest code collection and defaults.

## Making reviewable changes

Follow the [incremental guide](../INCREMENTAL_COMMIT_GUIDE.md) for small coherent
changes, verification and Git conduct. Update the
[owning documentation](../AGENTS/DOCUMENTATION.md) in the same unit of work.
Python spacing and lint/formatter conventions are documented in the
[pipeline setup](../../pipeline/README.md#setup-and-verification). Preserve source
snapshots, curated decisions, reviewed labels and frozen manifests. Never modify
[GOALS.md](../GOALS.md).
