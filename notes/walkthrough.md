# Read the project in 15–20 minutes

Current walkthrough, reviewed 2026-11-02. Agents first read the
[required orientation](AGENTS/README.md) and [incremental guide](INCREMENTAL_COMMIT_GUIDE.md).

1. Read [GOALS.md](GOALS.md), then [notes.md](notes.md). Keep both toxicity-profile
   comparison and known natural-product–protein interactions visible. Goals are never edited.
2. Read [project state](current/project-state.md). Distinguish implemented software,
   dated scientific findings, local inventory counts and unresolved validation.
3. Use the tracked [documentation index](../docs/README.md) and
   [architecture](../docs/architecture.md) to find maintained APIs/scripts and tests.
   `pipeline/` and `analysis/` are tracked; local preparation and research products remain ignored.
4. Read [evidence conventions](current/evidence-and-identities.md),
   [research interpretation](current/research-questions.md) and
   [data requirements](../docs/data.md). A fresh clone cannot reproduce local
   scientific results without the research bundle; API keys do not replace manual curation.
5. Read the relevant dated section of [FINDINGS.md](../analysis/FINDINGS.md) and
   locate its [result bundle](../docs/results.md). Do not combine results across
   different cohorts/folds as one model ranking.
6. For activity research use [structures/activity](current/structure-and-activity.md)
   and the [label-review guide](../analysis/docs/label_review_guide.md). For known
   interactions read [binding/targets](current/binding-and-targets.md).
7. Consult [next steps](current/next-steps.md) for live dependencies and
   [development](current/development.md) for commands. Old plans are historical
   execution records, not instructions to redo work.

For the original seven-candidate PubChem check, use the dated
[candidate review](archive/reports/candidate_review.md) and tracked
[live retrieval checkpoint](../pipeline/docs/live_retrieval_check.md). This
walkthrough does not recreate historical API responses or authorize new acquisition.
