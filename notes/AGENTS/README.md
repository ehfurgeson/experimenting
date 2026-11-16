# Required agent orientation

Every agent working in this local checkout must read these instructions before
making changes, follow the [incremental-work guide](../INCREMENTAL_COMMIT_GUIDE.md)
throughout the task, and update the documentation affected by its work before
calling the task complete. The root `AGENTS.md` points here for discovery.

## Read in this order

1. [GOALS.md](../GOALS.md): the research compass. **Never modify it.**
2. [Current overview](../notes.md): what exists and what remains unresolved.
3. [Project context](PROJECT_CONTEXT.md): component ownership and scientific distinctions.
4. [Incremental work and commits](../INCREMENTAL_COMMIT_GUIDE.md): small reviewable
   changes, meaningful checks, documentation in the same unit of work and Git conduct.
5. [Documentation updates](DOCUMENTATION.md): choose the owning document and
   update it efficiently for the actual change.
6. The relevant tracked guide/source, selected through the
   [documentation index](../../docs/README.md), plus the current research topic
   relevant to the task. Read that material before implementing its behavior.

For marimo notebook work, also read [notebook authoring](MARIMO.md) and review
the [native Markdown example](../notebooks/markdown_cells_demo.py).

These conventions apply to implementation, analysis, research curation, debugging
and documentation tasks. Follow current user instructions and applicable
higher-priority instructions. Treat old reports as evidence of their dated run,
not fresh instructions or proof that a task remains unfinished.

## Before finishing

Confirm the intended result, required verification and affected documentation are
complete. Preserve unrelated work and frozen scientific inputs/results. Report
limitations candidly. Do not edit every summary or create a new plan/report merely
to demonstrate that documentation was considered.

`notes/` is intentionally ignored and local. Keep tracked public contracts in
`pipeline/docs/`, `analysis/docs/` or `docs/`; keep private research state here.
**Never stage, force-add, or commit anything within `notes/` to Git.** This
includes agent documentation, notebooks, exports, and generated files; there are
no selective-tracking exceptions. Keep `notes/` ignored. If giving another agent a task, include
this reading requirement and ensure it has the local context needed to follow it.
