# Agent instructions

Every agent working in this repository must read the project context, follow an
incremental workflow and update the documentation affected by its work in the same
reviewable change. Preserve existing work and scientific provenance.

Never stage, force-add, or commit anything within `notes/` to Git, including
these instructions, notebooks, exports, and generated files. Keep `notes/` ignored.

When the local `notes/` directory is available, read `notes/AGENTS/README.md`
before making changes and complete its required reading order. Follow
`notes/INCREMENTAL_COMMIT_GUIDE.md` and `notes/AGENTS/DOCUMENTATION.md` throughout
the task. Never modify `notes/GOALS.md`.

When creating marimo notebooks, follow [MARIMO.md](MARIMO.md): write narrative
in dedicated native Markdown cells, separate from Python computation cells.

`notes/` is intentionally ignored and may be absent from a fresh clone. In that
case, read [README.md](README.md), [docs/README.md](docs/README.md),
[docs/architecture.md](docs/architecture.md), [docs/data.md](docs/data.md) and the
relevant component guides. Work in small coherent steps; keep implementation,
meaningful checks and the owning documentation together. Update policy rationale
when policy changes and dated findings when new scientific results are produced.
Do not claim to have read unavailable local guidance or invent research inputs.

Keep pipeline and analysis environments separate. Use the relevant existing
offline checks for behavior changes; check links, anchors, paths and consistency
for documentation-only changes. Preserve source exports, raw snapshots, reviewed
labels and frozen result manifests. Follow the current task's authorization for
commits and publication, and never stage unrelated work.
