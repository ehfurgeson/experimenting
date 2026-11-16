# Research notes index

Updated 2026-11-12. `notes/` is local and intentionally ignored by Git.
[GOALS.md](GOALS.md) remains the unchanged research compass. Start with the
[current overview](notes.md) or [walkthrough](walkthrough.md).
**Every agent must read [notes/AGENTS/README.md](AGENTS/README.md) and follow the
[incremental guide](INCREMENTAL_COMMIT_GUIDE.md) before changing this project.**

## Latest handoff and learning notebook

- [Modeled-evidence handoff](handoffs/modeled-evidence-2026-11-12/README.md): acquisition first, separate pathways and modeling, possible combination later.
- [Current progress tutorial](notebooks/presentation_essentials.py) and [HTML reading copy](notebooks/presentation_essentials.html): simple explanations, saved results and next-step plan.

## Current topic notes

| Topic | Maintained home |
| --- | --- |
| Capabilities, local inventory and checkpoint map | [Project state](current/project-state.md) |
| Scientific questions, scope and caveats | [Research context](current/research-questions.md) |
| Sources, identity, endpoints and missingness | [Evidence conventions](current/evidence-and-identities.md) |
| Structural models, validation and reviewed labels | [Structures/activity](current/structure-and-activity.md) |
| Known natural-product–protein interactions | [Binding/targets](current/binding-and-targets.md) |
| Remaining research deliverables | [Next steps](current/next-steps.md) |
| Planned ECOTOX pipeline integration | [ECOTOX ingestion plan](current/ecotox-ingestion-plan.md) |
| Environments and checks | [Development](current/development.md) |
| Definitions | [Glossary](current/glossary.md) |

## Working conventions and source provenance

- [Required agent orientation](AGENTS/README.md), [incremental work](INCREMENTAL_COMMIT_GUIDE.md)
  and [documentation responsibilities](AGENTS/DOCUMENTATION.md) apply to every task.
- [Compound provenance](CURATED_COMPOUNDS.md) indexes historical candidates,
  sources and ambiguities; these are not current reviewed activity labels.
- [Archive](archive/README.md) contains dated reports/checkpoints and the retained
  historical source for compound-citation line numbers.
- [Local utilities](utilities.md) records all four scripts, dependencies and writes.

## Local model review

[Professor-review notebook](notebooks/README.md) maps the overall goals and the
3 November structural-model requests to existing results, readiness and decisions.
It includes interactive feature/model/error exploration and a local HTML snapshot.

## Archive

Dated reports, old findings and historical citation sources live in
[archive/](archive/README.md). They retain scientific provenance but are not
current instructions. The notes root holds entry points and working conventions;
`current/` holds maintained research topics, `provenance/` holds still-used source
curation, and `AGENTS/` holds agent instructions.

The tracked [documentation index](../docs/README.md), [findings](../analysis/FINDINGS.md),
[data guide](../docs/data.md), [results](../docs/results.md) and
[label guide](../analysis/docs/label_review_guide.md) own public contracts and checkpoint
context. Preserve scientific source data, reviewed decisions and frozen results.

## Co-worker research handoff — 11 November 2026

The local [handoff package](handoffs/research-2026-11-11/README.md) contains a project
handoff, separate toxicity and biological-evidence research guides, offline HTML
reading copies and compact read-only evidence inputs. The
[portable ZIP](handoffs/research-handoff-2026-11-11.zip) can be given to authorized
research colleagues. All files remain ignored; no source/results or tracked code
were changed to create this documentation package.
