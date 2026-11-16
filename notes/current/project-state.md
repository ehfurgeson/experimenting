# Current project state

Reviewed **2026-11-02** against source, dated checkpoints and selected local table
headers/counts. This is an inventory update, not a new scientific run. The research
compass remains [GOALS.md](../GOALS.md).

## What is maintained

| Area | Implemented behavior | Current guide |
| --- | --- | --- |
| Reusable evidence pipeline | Curated input loading, identity reconciliation, PubChem caching, normalization, endpoint matching, context-constrained comparisons, audits and provenance | [Pipeline](../../pipeline/README.md) |
| EPA evidence | Identity candidates/crosswalk, ToxCast, source-admitted experimental hazard, measured/calculated properties, stored TEST predictions kept distinct | [EPA/ChEMBL](../../pipeline/docs/epa-chembl.md) |
| Evidence exploration | Cached trait assembly, eight policies for seven endpoint types, coverage, descriptive comparisons and classifier baselines | [Cached analysis](../../analysis/docs/cached-analysis.md) |
| Presentation | Maintained marimo notebook and static HTML export route | [Analysis quickstart](../../analysis/README.md) |
| Structural workflows | Formula/descriptor/Morgan features, identity checks, scaffold-held-out evaluation, reviewed-label validation and guarded candidate scoring | [Structural guide](../../analysis/docs/structural-screening.md) |
| Diagnostic/review workflows | Common-cohort stress controls, fixed/nested ablations, validated offline ChEMBL review exports | [Diagnostics/review](../../analysis/docs/diagnostics-review.md) |
| Known binding interactions | Source target/ortholog/resistance tables and assay/publication context available; no maintained, validated natural-product–protein binding characterization workflow established | [Binding workstream](binding-and-targets.md) |

The pipeline exposes Python APIs and individual example scripts, not a finished
unified CLI. `analysis/` is the maintained research implementation. Ignored
`experiments/` retains local preparation and earlier scripts, not a second
maintained analysis package. See [architecture](../../docs/architecture.md).

## Current local evidence inventory

Checked read-only on 2026-11-02:

- Selection CSV: **178 input rows** (62 herbicide, 116 natural-product rows).
- Prepared trait CSV: **176 rows**, 60 herbicides and 116 natural products, with
  **78 columns**. These are distinct stages/denominators; input-row differences
  must not be silently described as two new missing compounds.
- EPA crosswalk: 136 approved, 24 needing review, 16 unresolved identities.
- Researcher working worksheet: 154 rows, all activity and natural-origin labels
  still `unknown` in the inspected handoff copy. This does not assert that no
  researcher has other independently reviewed material elsewhere.

Paths and required inputs are in the [data guide](../../docs/data.md). They are
ignored local research assets and absent from a fresh clone.

## Dated research checkpoints

| Checkpoint | Supported result | Limit |
| --- | --- | --- |
| 2026-10-22 evidence/presentation | Seven endpoint types, eight availability policies; EPA expands mammalian/chronic coverage | Availability is not potency or safety; aquatic evidence remains sparse |
| 2026-10-27 structures | Formula and other representations discriminate the curated selection | Different eligible cohorts; labels describe selection, not verified activity |
| 2026-10-28 stress/acquisition | Common 171-compound structural cohort; 14 ChEMBL assays/publications, 157 activity records, 154 structures | Assay context is heterogeneous; candidate activity scoring remains blocked in recorded production run |
| 2026-10-29 feature comparisons | Nine profiles at fixed and nested C on identical cohort/folds; regularization explains much of the earlier combined-model gap | Exploratory selection comparisons; no new production default or independent activity validation |

Use [FINDINGS.md](../../analysis/FINDINGS.md) for exact metrics and denominators;
do not combine random-fold presentation, scaffold models and ablations as one
benchmark. [Results inventory](../../docs/results.md) maps local bundles and manifests.
Historical test counts belong to their original reports.

## Deliverables and remaining gaps

Analyzed products, computational workflows and the presentation route exist.
They are preliminary research deliverables, not a declaration that the final
semester presentation, safer candidates or binding characterization are complete.
The immediate scientific dependency is reviewed comparable activity evidence;
[target/binding curation](binding-and-targets.md), aquatic coverage, complete
input distribution and independent validation remain open. See [next steps](next-steps.md).


## Local main integration — 12 November 2026

At the user’s explicit request, the reviewed experimental branch was fast-forwarded
into local main at e94b9b6, twelve commits ahead of the unchanged origin/main.
Nothing was pushed; the experimental branch is retained. Final validation passed
300 analysis tests,1076 pipeline tests and Ruff. Review fixed input-version
attribution in activity preflight. The [preservation record](../../docs/data.md#local-experimental-preservation--2026-11-12)
identifies verified archives of677workspace files, historical code and the original
literature resource. One superseded preliminary transfer script hash remains
unresolved; canonical final-run source is recoverable. The broader research goal
remains paused; this merge does not approve experimental scientific claims.


## First separate A/B research release — 12 November 2026

Current user-authorized work on `codex/modeled-evidence-2026-11-12` now has
[a source-first checkpoint](../../analysis/docs/modeled-evidence-2026-11-12.md):
separate experimental/CATMoS releases, fixed scaffold/connectivity evaluation,
173-structure TEST union and paired teacher-lineage audit. Combined C is deferred;
archive-scale, tested-form and original-study independence remain provisional.
The checkpoint owns counts, commands, verification and canonical bundle paths.
Scientific assets remain ignored/local, and neither historical labels nor earlier
manifests changed. This task makes local commits only; no push or merge.
