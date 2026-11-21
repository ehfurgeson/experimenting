# Professor presentation: herbicides and natural compounds

Maintained research workflows explore molecular traits, toxicity-evidence
availability and structural classification in a purposive compound selection.
[Findings](FINDINGS.md) preserves dated results; the [module map](../docs/architecture.md)
explains ownership. These analyses support toxicity-profile comparisons and
safer bioherbicide discovery; structural selection classification does not establish
herbicidal activity or protein binding.

Latest review workflow: [human review adoption](docs/human-review.md)
(versioned approvals, policy-specific activity readiness and reviewed-cohort models).
The [5 November verification release](docs/verification-release.md) preserves the
identity hold and earlier source checks.

## Quickstart

Requires Python 3.12+ and `uv`. All commands here run from the repository root:

```bash
uv sync --project analysis --locked
uv run --directory analysis --locked python -X utf8 -m pytest tests -q
uv run --project analysis ruff check analysis
```

The locked environment installs sibling `pipeline/` as an editable dependency.
Setup may download dependencies; tests use synthetic inputs without research caches.

For the current catalog-wide plant and toxicity results, start with the
[joint-screen notebook](docs/joint-catalog-notebook.md). Its rebuild driver
downloads pinned public releases and reads the supplied local imports. The
commands below cover the earlier curated-panel workflows.

For a local research bundle (absent from a fresh clone):

```bash
uv run --project analysis python analysis/rebuild.py --source experiments/data --output analysis/data
uv run --project analysis marimo run analysis/professor_notebook.py
```

Use a fresh `--output` directory for comparison runs; set `AGROTOX_ANALYSIS_DATA`
to that prepared directory before opening the notebook. Cached rebuilds do not
fetch data or require API keys. See [input requirements](../docs/data.md).

Choose a guide: [cached rebuild and presentation](docs/cached-analysis.md),
[structural screening and labels](docs/structural-screening.md),
[diagnostics and assay review](docs/diagnostics-review.md), or the
[researcher label guide](docs/label_review_guide.md). The
[deeper assay-review assessment](docs/deeper-assay-review.md) connects the local
study-level review package to dietary triage and the remaining activity-label needs.
See the [result inventory](../docs/results.md) for frozen local runs.

The [professor follow-up notebook](../notes/notebooks/findings.py)
explains the halogen diagnostics, matched raw Morgan logistic/forest comparisons,
and dietary-comparator review pilot. It reads the local frozen model, dietary review/triage and deeper-review audit
bundles; it does not fit models or assign biological labels:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis marimo run notes/notebooks/findings.py
```

The opening is a concise three-part results walkthrough: halogen prevalence,
matched formula/fingerprint performance, and biological-verification priorities.
Graphs show the group counts and verified frozen AUROC/balanced accuracy on a
shared 0–1 scale. Verification instructions and detailed methods/audits follow;
the [full checklist](docs/verification-checklist.md) covers human source review.
The [200-compound update](docs/compound_sources.md#expanded-user-verified-dietary-list--2026-11-05)
adds user-reported benign dietary comparators, audited identities/overlaps and
section 6.1; the old 40-compound triage remains a historical pilot.
Data-loading and metric-validation cells precede the graphs, so the opening also
runs in source order. After updating an already-open session, restart its kernel
and run all cells to clear stale execution state. In an editor that still reports
duplicate definitions after cells were moved, close and reopen the notebook from
disk; restarting a kernel alone does not remove stale editor cells. The bundle
loader owns `frozen_bundle_integrity` once; the final table only reads it.
No model is refitted.
The notebook is now saved under
`findings.py`; its former filename was `professor_followup.py`.

Its local `findings.html` sibling is a static reading copy. See the
[diagnostic contract](docs/diagnostics-review.md#professor-follow-up-halogens-and-raw-fingerprints)
and [candidate review contract](docs/compound_sources.md#dietary-comparator-review-pilot--2026-11-04)
for reproduction commands and required human decisions. The
[preliminary automated triage](docs/dietary-triage.md) prioritizes the 40-candidate
worksheet using saved PubChem/CFR evidence, explicit rules and unadjudicated text
leads; it does not assign safety or plant-inactivity labels.

The [weekly research pilots](docs/weekly-pilots.md) add a conservative cached EPA
rat oral LD50 comparison alongside literature review and model-readiness work.

## Detailed guide links

Former section anchors are retained below for existing bookmarks.

## Structural evaluation ordering

See [Structural evaluation ordering](docs/structural-screening.md#structural-evaluation-ordering).

## Open the marimo notebook

See [Open the marimo notebook](docs/cached-analysis.md#open-the-marimo-notebook).

## Environment and cached rebuild

See [Environment and cached rebuild](docs/cached-analysis.md#environment-and-cached-rebuild).

## Endpoints and evidence classes

See [Endpoints and evidence classes](docs/cached-analysis.md#endpoints-and-evidence-classes).

## Trait flags and denominators

See [Trait flags and denominators](docs/cached-analysis.md#trait-flags-and-denominators).

## Distributions and comparisons

See [Distributions and comparisons](docs/cached-analysis.md#distributions-and-comparisons).

## Classifiers

See [Classifiers](docs/cached-analysis.md#classifiers).

## Outputs and checks

See [Outputs and checks](docs/cached-analysis.md#outputs-and-checks).

## Presentation views

See [Presentation views](docs/cached-analysis.md#presentation-views).

## Structural analysis environment

See [Structural analysis environment](docs/structural-screening.md#structural-analysis-environment).

## Formula composition

See [Formula composition](docs/structural-screening.md#formula-composition).

## Structural screening descriptors

See [Structural screening descriptors](docs/structural-screening.md#structural-screening-descriptors).

## Reviewed compound labels

See [Reviewed compound labels](docs/structural-screening.md#reviewed-compound-labels).

## Scaffold-held-out structural models

See [Scaffold-held-out structural models](docs/structural-screening.md#scaffold-held-out-structural-models).

## Offline structural screening workflow

See [Offline structural screening workflow](docs/structural-screening.md#offline-structural-screening-workflow).

## Complete formula identity checks

See [Complete formula identity checks](docs/structural-screening.md#complete-formula-identity-checks).

## Compound expansion sources

See [Compound expansion sources](docs/structural-screening.md#compound-expansion-sources).

## Structural stress diagnostics

See [Structural stress diagnostics](docs/diagnostics-review.md#structural-stress-diagnostics).

## Frozen assay review exports

See [Frozen assay review exports](docs/diagnostics-review.md#frozen-assay-review-exports).

## Researcher label handoff

See [Researcher label handoff](docs/structural-screening.md#researcher-label-handoff).

## Structural feature-block ablations

See [Structural feature-block ablations](docs/diagnostics-review.md#structural-feature-block-ablations).

## Nested structural regularization experiments

See [Nested structural regularization experiments](docs/diagnostics-review.md#nested-structural-regularization-experiments).

Separate source-first experimental and external-model evidence uses the
[A/B collection and evaluation protocol](docs/modeled-evidence.md). This workflow
keeps provisional bulk identities and teacher estimates apart from accepted labels.

For a local experimental reading/exploration notebook (when the ignored scientific
bundles and notebook are available):

```bash
uv run --project analysis --locked --offline marimo edit notes/notebooks/evidence_experiments.py
```

The notebook starts with compound counts for both tracks, then uses F1-first
scores, class-specific logistic weights and forest OOB permutation importance.
It distinguishes stability from statistical significance. The maintained
[same-target OOB command](docs/modeled-evidence.md#same-target-forest-oob-exploration)
rebuilds the additional diagnostic bundle; the notebook itself stays untracked.

## Local import inventory

Run `python analysis/import_inventory.py data_imports <fresh-output.jsonl>`
from the repository root. It records each file's SHA-256 and size, profiles
delimited tables including nested archives, and counts populated workbook
rows by sheet. The [import audit](docs/import-coverage-2026-11-18.md) maps
the sources to prior workflows.

From `analysis/`, run `uv run --locked python -m pytest tests/test_import_inventory.py -q`.

## Public toxicity cohort reconstruction

From the repository root, run:

```bash
uv run --project analysis --locked python analysis/public_toxicity.py \
  --ice data_imports/NICE/acute_oral.xlsx --opera <pinned-OPERA_Data.zip> \
  --output experiments/import-expansion/public-cohorts
```

Use the pinned OPERA archive in [modeled evidence](docs/modeled-evidence.md).
The command uses the established A/B filters and aggregation, preserves source
observations, and emits a hash-verified cohort membership table for catalog
overlays. Its manifest identifies this as a public-only reconstruction. It can
feed `evidence_models.py` and the existing sprint overlays when reviewed
selection files and the historical cache are unavailable.

From `analysis/`, run `uv run --locked python -m pytest tests/test_public_toxicity.py -q`.

## NICE workbook context

`nice_context.py --nice data_imports/NICE --release <public-cohorts> --output <fresh-dir>`
profiles the other NICE workbooks against the measured ICE cohort. Its
compressed JSON Lines export retains native contexts and locators. The manifest
reports all scanned rows and coverage by identity tier per sheet.

From `analysis/`, run `uv run --locked python -m pytest tests/test_nice_context.py -q`.

## NICE archive coverage

`nice_archive_coverage.py --nice data_imports/NICE --release <public-cohorts> --output <fresh-dir>`
retains matched ClassyFire records and counts NICE cHTS endpoint rows per
unambiguous measured-cohort DTXSID. It reads the nested archive without
expanding it into the workspace. The exported cHTS counts show availability.

From `analysis/`, run `uv run --locked python -m pytest tests/test_nice_archive_coverage.py -q`.

## Public reference panel

`public_panel.py --release <public-cohorts> --models <evaluated-models> --hrac <master-list.xlsx>
--literature resources/annona_primary_review_2026-11-18.csv --output <fresh-dir>`
checks cohort and model hashes and emits per-record forest probabilities plus
observed ICE and CATMoS teacher evidence when available. Use the
`analysis/resources/` path for the literature input from the repository root.
Pass `--selection <original-structural_features.parquet>` to include an
original reviewed panel. Missing and held structures remain as output rows.
Repeat `--extra-literature <panel.csv>` to score evidence from named plant
studies separately. A study row needs a panel, compound name, SMILES,
identity status, DOI and source locator.

From `analysis/`, run `uv run --locked python -m pytest tests/test_public_panel.py -q`.

## Public evidence intersection

`import_screen.py --root <public-run> --panel <public-panel> --output <fresh-dir>`
verifies the public cohort, ECOTOX, NPASS, COCONUT and ToxValDB bundles. It writes
dose-point plant responses, catalog-linked EPA leads, group descriptors and
LD50 bins, and analogues to source-supported plant structures. A second EPA
audit can be passed with `--toxval-extra`.
The analogue output includes a sensitivity ranking restricted to structures
whose exact ICE reports all fall in the high LD50 bin.

From `analysis/`, run `uv run --locked python -m pytest tests/test_import_screen.py -q`.

See the [18 November import results](docs/import-results-2026-11-18.md)
for the completed public reruns, evidence counts and original-panel dependency.
The [Parthenium evidence workflow](docs/parthenium-evidence.md) extracts
controlled literature dose points and reconciles printed and recalculated
inhibition.
The [low-LD50 catalog review](docs/catalog-hazard-review.md) traces the
underlying ICE reports and separates NPASS links from reviewed origin evidence.
The [OOB randomization check](docs/oob-null-test.md) compares the binary
forests with a whole-block label permutation null.
