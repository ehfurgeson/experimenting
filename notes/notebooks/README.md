# Local notebooks

## Native Markdown authoring example

[markdown_cells_demo.py](markdown_cells_demo.py) demonstrates dedicated native
Markdown cells, kept separate from reactive Python computation cells, following
[marimo_markdown_example.py](marimo_markdown_example.py). See the [authoring guidelines](../AGENTS/MARIMO.md).
Open the notebook from the repository root:

```bash
uv run --project analysis --locked marimo edit notes/notebooks/markdown_cells_demo.py
```

[markdown_cells_demo.html](markdown_cells_demo.html) is the executed default-view
snapshot. Python-backed interaction requires the live notebook.
Nothing under `notes/` may be staged, force-added, or committed to Git.

## Local professor review — 3 November 2026

[professor_review.py](professor_review.py) is a read-only marimo review of the
existing structural, stress, ablation and ChEMBL-review bundles. It maps the overall
research goals and the professor's specific structural-model requests to implemented
capabilities, recorded results, scientific limitations and next decisions.

## Open interactively

From the repository root, using the existing locked analysis environment:

```bash
uv run --project analysis marimo run notes/notebooks/professor_review.py --port 2718
```

Open **http://127.0.0.1:2718**. Replace `run` with `edit` to edit the notebook.
`notes/` is ignored; notebook, helper, session state and export remain local.
No dependencies or lockfiles were changed.

[professor_review.html](professor_review.html) is a static snapshot of the default
view. Python-backed selectors need the live notebook; the HTML is an offline
reading fallback. Regenerate it only after intentional local notebook changes:

```bash
uv run --project analysis marimo export html notes/notebooks/professor_review.py -o notes/notebooks/professor_review.html --no-include-code --force
```

The export contains displayed research data. No upload or sharing is performed.

## What to inspect

- Goal-by-goal readiness, including the distinction between implemented software
  and a validated biological activity classifier; broader toxicity/binding goals.
- Formula/element, descriptor, synthetic-accessibility and rule-proxy distributions.
  Formula-only models use 27 features, not just the distinct-element count.
- All nine fixed/nested profiles on identical 171-compound cohorts and five outer
  scaffold folds; avoid comparisons with the older different-cohort models.
- Held-out confusion/errors at the recorded 0.50 cutoff; slider changes are exploratory
  sensitivity checks, not a new validated decision threshold.
- Fold-local PCA dimensions, C selection, scaffold sensitivity and shuffled controls.
- The inspected working activity/origin labels, assay contexts and remaining review needs.
- Expanded-source roles, 3 November source-page checks and decisions to agree today.

## Inputs and verification

The notebook reads `analysis/outputs/structure-2026-10-28-stress-baseline/`,
`stress-2026-10-28/`, the two `ablations-*-2026-10-29-final/` bundles,
`chembl-review-2026-10-29-final/`, `chembl-review-screen-2026-10-29-final/`,
and the researcher handoff's `reviewed_labels.csv` (or frozen template if absent).
An optional broader-goals panel also reads `analysis/data/compound_traits.csv`
after checking its hash against the prepared-data manifest.
It needs those ignored local assets; see the tracked [data guide](../../docs/data.md).

[review_support.py](review_support.py) verifies frozen output hashes before display,
reports input/code/lock integrity separately, validates the common cohort and identical
outer-fold assignments, rejects scaffold leakage, and recomputes report metrics from
held-out probabilities across all eighteen model/mode pairs. Working labels remain
an independent local copy. Notebook execution performs no acquisition, model fitting
or scientific input/result writes; only normal marimo UI/cache state and a requested
HTML export are generated locally.

Use `marimo check` and Ruff for source validation, then execute/export to check the
cells. The recorded bundle checks and model scores are not a new external activity
validation. Current scientific findings remain in tracked `analysis/FINDINGS.md`.


## New professor follow-up — 4 November 2026

[findings.py](findings.py) is a new notebook explaining newly
run halogen attribution/ablations, raw fingerprint logistic/forest comparisons,
held-out errors and the 40-identity dietary candidate pilot. Unlike the older
read-only review above, its accompanying commands have generated new result
bundles. The notebook itself remains read-only and verifies output hashes and
held-out metrics/folds before display. It includes a descriptive chemical-space
view, source citations and exact human review actions. No dietary candidate has
been assigned a biological label.

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis marimo run notes/notebooks/findings.py
```

The earlier selective-tracking convention is superseded by the
[notes Git rule](../AGENTS/README.md#before-finishing): all notes remain local.
The sibling
[HTML](findings.html) is a locally exported static snapshot; live Python
selectors require marimo. The tracked [analysis entry point](../../analysis/README.md)
links to commands/contracts and local-input requirements.


The follow-up notebook now includes **section 6a: automated preliminary review**.
It reads `analysis/outputs/dietary-triage-2026-11-04-final/`, verifies output
hashes/counts/unknown biological labels, and offers a group filter and candidate
evidence drill-down. Counts are 12 provisional dietary candidates, 26 priority
review and 2 presumed-plant-negative exclusions; five rows retain evidence gaps.
See the tracked [triage contract](../../analysis/docs/dietary-triage.md).
The static HTML was re-exported after executing the new cells.


Section **6b** now connects the local 29 October deeper source-review package to
the dietary triage. It reads the verified 5 November audit bundle and displays
file/study inventories, identity overlaps and hypothetical scaffold-support checks.
It performs no source edits, policy approval or model fitting; see the
[integration assessment](../../analysis/docs/deeper-assay-review.md).


The notebook now starts with a separated **research-findings presentation**
(5 November) answering the professor's formula/halogen, fingerprint/classifier,
dietary comparator and three-group requests. A separate working-instructions
section follows before the detailed analysis. The headline model table uses
verified frozen metrics. Exact manual steps and the editable 82-compound source
matching/dietary review pack are described in the maintained
[verification checklist](../../analysis/docs/verification-checklist.md).
No known labels or scientific approvals were created by preparing the pack.


## Chemistry model experiments — 12 November 2026

[presentation_essentials.py](presentation_essentials.py) is a concise, live marimo
experimental notebook for walking through saved models with a professor. Six
sections cover target definitions, F1-first comparisons, standardized logistic
feature weights, random forest OOB permutation F1 loss, new-paper transfer and
next experiments. A single experiment selector updates scores and diagnostics
for the 171-compound selection, 30-compound reviewed contrast and 73-compound
heterogeneous activity pool. Full coefficient tables, ablations and file inventory
are collapsed to keep the reading path short.

From the repository root:

```bash
uv run --project analysis --locked marimo edit notes/notebooks/presentation_essentials.py
```

Use `run` instead of `edit` for a reading view. The notebook verifies each loaded
CSV against its frozen manifest, checks common cohorts/folds and scaffold
separation, and recomputes displayed held-out F1 and confusion counts. It reads
local ignored scientific assets and fits no models or changes reviewed evidence.
OOB importance and shuffle SD are descriptive; the saved runs contain no formal
feature-significance tests or p-values.

This version is intended for the live notebook. The sibling
[presentation_essentials.html](presentation_essentials.html) is an **older tutorial
snapshot** and does not reflect this rewrite; it is retained without regeneration.
All notebook files remain ignored and uncommitted.


## A/B evidence experiments — 12 November 2026

[evidence_experiments.py](evidence_experiments.py) is the current concise working
notebook for Track 1/2 counts, F1-first model comparisons, class-specific logistic
weights and same-target forest OOB importance. It identifies B's exact OPERA
archive/member/field and distinguishes teacher reproduction from experimental
validation. It retains the activity transfer failure and binding evidence limits.

```bash
uv run --project analysis --locked --offline marimo edit notes/notebooks/evidence_experiments.py
```

[evidence_experiments.html](evidence_experiments.html) is an executed default-view
snapshot; use live marimo for Python-backed controls. Both remain gitignored.
