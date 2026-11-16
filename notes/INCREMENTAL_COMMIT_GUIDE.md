# Incremental work and commits

Required working convention for every agent in this repository. Updated 2026-11-02.
Read the [agent entry point](AGENTS/README.md), then follow this guide for each
implementation, research or documentation task. Documentation belongs in the same
unit of work as the behavior or evidence it describes.

## Before changing files

1. Read the unchanged [GOALS.md](GOALS.md), [current overview](notes.md) and relevant
   component guide/source. Identify the concrete outcome and scientific boundary.
2. Inspect Git status and applicable instructions. Preserve existing work, curated
   inputs, reviewed labels and frozen evidence. Keep this task's changes separate
   from unrelated edits; use an isolated branch/worktree when needed and practical.
3. Break substantive work into small, independently reviewable behavior boundaries.
   For each boundary, identify implementation, meaningful verification and the
   documentation that owns the change. A short working plan is sufficient; do not
   create a permanent plan/report file for every session.

## Implement one coherent boundary

Keep implementation, relevant tests/examples and documentation together. Separate
unrelated behavior changes, broad refactors, dependency changes or data migrations
when that improves review. A small dependency required by a behavior may accompany
it; line counts and file counts are prompts to review scope, not quotas.

For a bug, reproduce the failure with an appropriate regression check. For new
behavior, verify its contract and important failure states. Use existing checks
for a behavior-preserving change; do not manufacture a failing test or write tests
that mirror trivial implementation details. Documentation-only changes need link,
anchor, path and consistency checks rather than a scientific rebuild.

Update the [owning documentation](AGENTS/DOCUMENTATION.md) immediately as the
boundary changes. Describe supported behavior, inputs/outputs, missingness,
provenance and limits where affected. Add policy rationale when a policy changes;
do not append a diary entry for a rename or routine fix.

Run focused checks first, then required relevant suites in the proper locked
environment. Keep normal tests offline. Broaden testing when changed behavior,
a failure or an unresolved concern warrants it. See [environment commands](current/development.md).
Inspect the complete diff, links and unintended files before moving on.

## When making commits

Follow the user's task authorization for creating commits and publishing changes.
Incremental work and documentation updates are required even when the task stops
at a reviewable uncommitted diff. Do not create commits, switch branches or stage
unrelated files merely to satisfy a historical workflow example. Existing user
authorization carries forward; do not add repeated permission requests.

When commits are authorized, make one logical boundary per commit, with tests and
documentation included. Stage explicit relevant paths and inspect the staged diff.
Use a concrete Conventional Commit subject, for example
`fix: preserve unknown EPA assessment states`. Add a short body explaining the
problem, resulting behavior and material limits when needed. A message must describe
the final change; update a task plan if its old wording no longer fits.

Keep local work separate from publishing. Pushes, merges and history rewrites
require task authorization; do not infer it from an old branch note or commit guide.
Follow the [notes Git rule](AGENTS/README.md#before-finishing): nothing within
`notes/` may be staged, force-added, or committed. Keep the entire directory ignored.

## Finish the boundary and task

Report the outcome, meaningful verification and remaining scientific or technical
limitations. State what could not be verified; do not claim historical tests were
rerun. Update current state/next steps only when their facts changed. Preserve
[GOALS.md](GOALS.md), source exports, snapshots and historical result manifests.
Leave the next agent a clear source of truth rather than another duplicate report.
