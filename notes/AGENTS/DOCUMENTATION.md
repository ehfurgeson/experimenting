# Documentation updates required for every task

Every agent must assess which documentation its work affects and update those
owning documents as part of the same reviewable change. If no user-facing behavior,
policy, scientific result or documented state changes, say why existing guidance
remains accurate; do not create an artificial documentation edit.

## Choose the owning document

| Change | Update |
| --- | --- |
| Pipeline API, retrieval/cache behavior, identity, normalization or evidence contract | Relevant guide under `pipeline/docs/`; link from `pipeline/README.md` only if discovery/setup changes |
| Analysis command, inputs/outputs, models, labels, notebook or diagnostics | Relevant guide under `analysis/docs/`; `analysis/README.md` for entry-point/setup changes |
| Scientific/eligibility/missingness/validation policy | Owning pipeline or analysis `docs/decisions.md` with the rationale and limits, plus the affected usage contract |
| New scientific result or accepted checkpoint | Dated `analysis/FINDINGS.md` section and focused checkpoint when needed, with cohort, method, provenance and limits; `docs/results.md` for a new relevant bundle |
| Source/input/bootstrap/reference requirements | `docs/data.md`, `docs/references.md` or the source-table guide, whichever owns the fact |
| Significant capability, inventory or research dependency change | Relevant `notes/current/` topic; update `notes/notes.md` only if its high-level summary becomes inaccurate |
| Documentation added, removed or relocated | Owning index and every affected reference/anchor/path consumer |
| Development or agent-working convention | `notes/INCREMENTAL_COMMIT_GUIDE.md`, this folder or environment guidance as appropriate; keep one authoritative rule |

[Notes index](../README.md) routes to each current topic. Keep normative contracts
in tracked guides; local notes explain research status and link to them. Keep
scientific counts dated and tied to exact inputs rather than duplicating full metric
tables in multiple overviews. New source curation should be a dated reviewed record,
with retained citations/ambiguities, rather than a silent rewrite of old decisions.

## Efficient editing

Read the relevant source/contract before editing. Update the smallest owning section,
remove superseded text, and link from other documents. Keep entry points short.
Add a new document only for a distinct durable responsibility; do not generate
session diaries, delivery reports or redundant snapshots for routine work.

Document the final supported behavior, working directory, prerequisites, command,
outputs and material limits when affected. Distinguish implemented software, dated
findings, proposals and unresolved scientific dependencies. Avoid updating unrelated
summaries, repeating unchanged facts or copying implementation details into user flows.

Keep [GOALS.md](../GOALS.md) unchanged. Preserve dated scientific findings and
provenance-bearing sources. Delete obsolete plans, duplicate wrappers or reports
only after checking for unique scientific evidence, manifest/hash dependencies,
source-line citations and incoming references; then remove or redirect references.
Move outdated reports and superseded notes into `notes/archive/`, update their
incoming/outgoing links, and index them in its README. Keep the notes root for
current entry points and conventions; do not leave dated delivery reports there.
Still-used source curation belongs in `notes/provenance/`, even when its source
review is dated. Preserve code paths recorded in frozen manifests.
The [retained historical source](../archive/README.md) supplies old compound-citation
line numbers and is not a current work plan. Scientific frozen manifests must not
be rewritten to make newer documentation look historically identical.

## Verify and finish

Check active relative links and anchors, example/source paths and command options.
For a path move, update code/import/test/notebook/manifest consumers together and
run appropriate compatibility checks. For a documentation-only change, check
consistency and preserve scientific inputs/results; a rebuild is unnecessary.
Report only checks actually executed, with meaningful limitations.

Follow the [incremental guide](../INCREMENTAL_COMMIT_GUIDE.md): documentation travels
with its behavior or scientific evidence, including in authorized commits. A task
is unfinished if its implementation leaves the owning documentation misleading.
