# Cached evidence analysis and presentation

[Component quickstart](../README.md) · [Repository documentation](../../docs/README.md)

Commands below run from the repository root. Real-data examples require the local inputs described in the [data guide](../../docs/data.md).

## Open the marimo notebook

After obtaining the local input bundle and rebuilding prepared products (see below):

```bash
uv run --project analysis marimo run analysis/professor_notebook.py
```

For editing, replace `run` with `edit`. The notebook starts with all seven
primary endpoint availability distributions, followed by molecular weight,
XLogP, polarity, complexity, evidence coverage, and classifier accuracy versus
baseline. Source, extra-trait, and observation selectors support exploration.
Actual toxicity observations are shown with study context; chronic doses are
not pooled without comparable context.

To capture a shareable snapshot of the current view:

```bash
uv run --project analysis marimo export html analysis/professor_notebook.py -o analysis/outputs/professor_presentation.html
```

An HTML export may exist in the original local workspace; it is absent from a fresh clone. It captures the default view;
Python-backed controls require the live app. See the
[marimo export guide](https://docs.marimo.io/guides/exporting/static_html/).
The HTML includes the displayed data, so share the intended prepared selection.
Exports, session state, input data, and source experiments remain ignored.
Use `AGROTOX_ANALYSIS_DATA` to select another prepared product directory.


## Environment and cached rebuild

Run from the repository root:

```bash
uv sync --project analysis --locked
uv run --project analysis python analysis/rebuild.py --source experiments/data
```

The locked analysis environment installs the pipeline from `../pipeline` plus
marimo and Altair. `--source` can be any existing selection and raw-cache root;
there is no dependency on experiment Python files. Products are written into
ignored `analysis/data/` by default, outside the source directory. Source files
are read only. The rebuild never fetches missing descriptors or API records;
absent cached descriptors stay missing, and missing approved EPA caches raise.

Required source inputs are `compounds.csv`, `compound_classes.csv`, validated
PubChem caches, and optionally `epa_identity_crosswalk.parquet` with raw EPA
hazard caches. Cached computed descriptors, ToxCast coverage, and property
coverage enrich the traits when present. The existing local preparation scripts
and curated provenance in `notes/` stay outside the tracked presentation code.

The rebuild runs trait assembly, source coverage, distributions, comparisons,
and models, then writes `data/manifest.json` with input/code/output hashes and
an explicit EPA-availability state. PubChem-only rebuilds are supported in a
clean output directory. No API key is needed for cached analysis.


## Endpoints and evidence classes

The experiments load `pipeline/examples/endpoints.yaml`, covering all seven
types through eight named policies:

| Policy | Endpoint | Context |
|---|---|---|
| `mammal_oral_ld50` | LD50 | Mammal, oral, mg/kg |
| `fish_lc50` | LC50 | Broad fish availability, mg/L |
| `trout_lc50_96h` | LC50 | Rainbow trout, 96 hours, mg/L |
| `daphnia_ec50_48h` | EC50 | Daphnia magna, 48 hours, mg/L |
| `mammal_oral_noael_daily` | NOAEL | Mammal, oral, mg/kg-day |
| `mammal_oral_loael_daily` | LOAEL | Mammal, oral, mg/kg-day |
| `mammal_oral_bmd_daily` | BMD | Mammal, oral, mg/kg-day |
| `mammal_oral_bmdl_daily` | BMDL | Mammal, oral, mg/kg-day |

EPA measurements are rebuilt from selected raw caches through
`agrotox.epa_workflow.build_epa_hazard_offline`; legacy processed experiment
hazard tables are never analysis inputs. Source eligibility requires an explicit
experimental mark. BMD/BMDL remain **model-derived points of departure from that
evidence**, distinct from stored TEST predictions. Normalized study-level values
retain units, qualifiers, study context, provenance, and review reasons.

Chronic example policies count availability only: no heterogeneous chronic doses
are pooled into potency medians. Their summary medians remain null unless a
custom potency policy supplies the context required by the pipeline.
PubChem prose extraction remains acute-only. Its chronic zeros describe parser
coverage, not absence of chronic evidence. PubChem annotations are not all
independently verified as experimental. TEST predictions remain in their own
table and do not enter these distributions or classifiers.


## Trait flags and denominators

Both sources' coverage reports retain the full selected compound universe,
including unresolved identities and those awaiting EPA review. Audits explain
why a compound has no extracted match; coverage zero never implies no hazard.

The trait table preserves every selected compound and provides:

- `has_pubchem_<policy>`: evidence extracted from the PubChem cache.
- `has_epa_<policy>`: eligible evidence extracted from the EPA hazard cache.
- `has_<policy>`: the union of those source flags, replacing the earlier
  PubChem-only meaning of this prefix.

A source flag is one for a match, zero for an assessed source with no match,
and null when the identity/retrieval is unavailable. A union is one if either
source matches, zero only if both sources were assessed without a match, and
otherwise null. Empty retrieved EPA responses are assessed; unapproved identities
are not. Source-specific flags and audits must accompany interpretation.

Other traits retain computed PubChem descriptors (mass, XLogP, TPSA, hydrogen-bond
counts, complexity, etc.), PubChem extraction counts, ToxCast assay activity,
and EPA hazard/property counts. Missing optional traits remain missing.


## Distributions and comparisons

The distribution and comparison scripts retain numeric traits and every endpoint flag, including all-null and
all-zero flags. Output kinds separate `molecular_property`,
`endpoint_availability`, `study_coverage`, and `assay_activity`.

Availability distributions describe binary evidence indicators, not toxicity
doses or concentrations. Each group has explicit present/missing counts. Missing
groups yield null estimates and console `NA`, not zero or exceptions. Group
comparisons report median differences, percentile bootstrap intervals,
unadjusted permutation p-values, and the probability that a value from the
herbicide group exceeds one from the natural-product group (AUC).

The selection is purposive, not representative. Multiple unadjusted tests and
sparse endpoints cannot establish general population differences, causation,
or safety. ToxCast fractions also depend on which assays tested each compound;
a shared-assay analysis is needed to investigate that confounding.


## Classifiers

Descriptors predict group membership, PubChem study coverage, or each
source-specific/combined endpoint availability flag. Endpoint flags are labels,
never predictor features. Missing labels are excluded rather than imputed to
zero. Training-fold median imputation and scaling are applied to held-out
compounds using the training parameters.

Five-fold validation requires at least five examples of each class. Other
targets retain a row with `insufficient_class_support`, null accuracy, and no
fitted weights. This includes absent BMD and sparse BMDL in the current caches.
Reported coefficients are full-sample descriptive fits for evaluated targets;
the models predict evidence availability, not endpoint doses or safety.


## Outputs and checks

| Output under `data/` | Contents |
|---|---|
| `epa_analysis/*.parquet` | Eleven current EPA evidence, coverage, audit, review, and summary tables, each with a dependency sidecar |
| `epa_endpoint_coverage.csv` | Source-specific counts with equal full-selection denominators |
| `compound_traits.parquet`, `.csv` | Wide traits with source-specific and combined endpoint flags |
| `traits.parquet`, `traits_long.parquet` | Existing compatibility exports; the long-form value column is text |
| `distributions.csv` | Per-group numeric summaries and availability distributions |
| `comparison.csv` | Group differences with sample counts, intervals, p-values, and AUC |
| `classifiers.csv` | Target counts, class balance, status, accuracy, and fitted weights |

Older `epa_hazard_comparison.*` and raw-ingestion products may still exist;
current endpoint consumers rebuild from raw caches instead of using them.
`FINDINGS.md` records a dated cached-run checkpoint.
Generated outputs stay local and must be refreshed after pipeline changes.

From the repository root:

```bash
pipeline/.venv/bin/python -m pytest pipeline/tests/test_experiment_endpoints.py pipeline/tests/test_experiment_distributions.py pipeline/tests/test_experiment_models.py -q
pipeline/.venv/bin/python -m pytest pipeline/tests -q
```

Tests use synthetic data and injected descriptor values. They verify raw-cache
rebuilding, all-seven-endpoint availability, null/zero distinctions, sparse
summaries, and valid classifier preprocessing without live API calls.


## Presentation views

The presentation helpers order the seven primary endpoints before chemical
traits. Endpoint charts show evidence found, no extracted match, and unassessed
states as shares of the full selected group. Actual toxicity observations retain
their units and study context; the presentation does not pool chronic doses.
Molecular distributions use empirical CDFs normalized within each group, with
finite-value sample sizes in tooltips. Classifier charts show held-out accuracy
beside the majority-class baseline rather than treating raw accuracy as skill.
Prepared product hashes are checked before presenting; changed results require
a rebuild. Source code for these views is in `presentation.py`.
