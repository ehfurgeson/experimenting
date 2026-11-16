# Separate experimental and external-model evidence

This is an AI experimental workflow, not human scientific review. A and B are
evidence pathways within the existing research tracks. They do not establish
plant activity, natural origin, safety or field efficacy.

## First-release protocol (declared before new model scores)

Collect source-first, retaining immutable raw files and hashes. Keep NIH ICE
acute-oral workbook versions separate: the lowercase `acute_oral.xlsx` has
structures and metadata; the uppercase workbook is a distinct older export,
not extra independent experiments. Use only the lowercase file for this release.
The official [bulk index](https://ice.ntp.niehs.nih.gov/downloads/DataonICE/)
and workbook metadata identify the product. Archive the OPERA repository commit
and `OPERA_Data.zip`, including `CATMoS_QR50k.sdf`; its predictions are stored
outside-model results, not a local run of OPERA. Source labels describe each
field, including log10(mg/kg) CATMoS outputs. Preserve the individual consortium
consensus and OPERA CATMoS prediction columns separately. The primary B target is
`CATMoS_LD50_pred`, not its embedded experimental comparator or `consensus_LD50`.

A outcome labels must be experimental. Structural descriptors are calculated
from supplied structures; they are not measured inputs. A stricter both-X-and-y
measured policy is unsupported here. Retain all source rows, including mixtures,
missing structures, reference gaps, inequalities, unknown domains and failures.
Retain each ICE row’s source evidence type even when excluded: In Vivo/In Vitro
is experimental, In Silico is predicted, and unrecognized types stay unknown.
Do not admit provider experimental comparator fields to A without original-study
review. The source-first inventory does not inherit the project's human-approved
identities or activity labels. No historical medians, cutoffs or labels change.

The descriptive A cohort uses explicit In Vivo, Rat, chemical rather than mixture,
LD50, mg/kg records with positive finite exact values, a source reference and a
valid single-component structure. It is provisional: database references can
mirror the same study and actual tested form/purity remains incompletely audited.
Collapse identical chemical/sex/reference/value records before computing a
per-structure median. Preserve censored observations separately; never use bounds
as exact values. Report source counts as provider references, not independent
studies. Preserve original and QSAR-ready forms and join only full structure keys.
Do not infer equivalent salt, stereoisomer or acid forms.

The primary B cohort uses finite CATMoS log10(mg/kg), valid single-component
QSAR structure and provider AD=1. Keep outside and unknown AD records separate.
Do not fill A from B. CATMoS training/test labels concern the source release;
shared ICE/TEST/ChemIDplus lineage prevents assuming independent validation,
including for a provider `Tst` label in an updated model archive.

## Fixed evaluation design

Freeze separate A/B CSV releases, identities, exclusions, lineage and coverage
before evaluation. Model regression target log10(mg/kg) and classification with
fixed historical cohort cutoffs 1,080 and 3,400 mg/kg (low/medium/high **LD50**).
Lower LD50 means greater acute hazard. These are not regulatory bins. No target
quantile fitting or score-driven feature/profile selection is allowed.

Use one row per full structure. Group outer folds by connectivity and Bemis–Murcko
scaffold; merge scaffolds sharing connectivity so stereo variants cannot leak.
All acyclic molecules share a conservative single scaffold. Five deterministic
GroupKFold folds require train/test class support; unsupported classification
folds are recorded, not silently replaced with random row splits. Keep actual
fold membership. Features: RDKit molecular weight, TPSA, HBD, HBA, rotatable bonds,
ring count and fraction sp3; no external property/toxicity estimates as inputs.
Only logistic/ridge preprocessing is standardized, inside each training fold.
Fixed seed 20261112. No tuning. Primary diagnostics:

- Regression: training-median baseline, ridge (alpha=1), random forest (200 trees,
  min_samples_leaf=5, max_features=1.0). MAE, RMSE, Spearman rank correlation and
  bias in log10 dose. One log10 unit is a tenfold dose difference.
- Classification: majority baseline, balanced logistic (C=1, max_iter=2000),
  balanced random forest (same tree settings). Macro-F1, per-class F1/precision/
  recall, balanced accuracy, one-vs-rest AUROC where defined, confusion counts.
  Report class support. Positive classes for per-class metrics are explicit.
- Logistic weights are standardized within training folds and reported with
  fold variation. Forest tree-specific OOB permutation diagnostics use the
  existing repository implementation where supported. Repeat SD is stability,
  not a p-value; OOB is not scaffold validation. No formal significance claim.

No calibrated prediction intervals are fitted in this first release; interval
coverage and calibration remain unavailable. Models trained on B reproduce a
teacher model; their scores are not experimental accuracy. Source-publication
holdouts require original publication identifiers, which bulk reference labels
do not reliably provide: mark this validation unsupported, without claiming
scaffold folds replace it. Report provisional outcomes and exclusions explicitly.

Pair A and B only by the same full key, rat/oral/LD50 and compatible dose basis.
Compare fixed bins and log-dose/rank differences with AD and training membership.
Report agreement, not independent validation. TEST fathead minnow LC50 cannot
validate rainbow trout, and Daphnia LC50 cannot silently match immobilization
EC50. Keep TEST units exactly as delivered until the API scale/form conversion
has independent documentation. Do not infer linear semantics from value ranges.

Decide on C only after separate releases and evaluations. Defer C when original
study/teacher lineage and untouched experimental test data are unavailable.
Never concatenate A/B labels as independent observations.

## Reproducible collection and freeze

From the repository root, public acquisition has its own explicit command. It
uses no EPA credential and refuses an existing destination. HTTP failure bodies
and exception types remain in the log. Inspect status/content before freezing:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/collect_evidence_sources.py \
  --output experiments/external-evidence-NEW_RUN/sources
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/evidence_release.py \
  --sources experiments/external-evidence-NEW_RUN/sources --data experiments/data \
  --output analysis/outputs/separate-evidence-NEW_RUN
```

Acquisition needs network access even though the environment is locked/offline;
`--offline` controls uv package resolution, not Requests. Normal tests make no
source requests. The offline freeze streams the ICE XLSX and CATMoS SDF without
recalculating or modifying source files. Its workbook reader handles source-cell
values and rejects formulas; it is not a general spreadsheet engine.

Outputs include separate `A_observations`/`A_compounds` and
`B_predictions`/`B_compounds`, identity, source, exclusion, duplicate-resolution
and lineage ledgers, TEST raw-version/endpoint audits, collection state for every
original selected EPA identity, the full cached predicted-property inventory and
a hash manifest. No salt/parent mass conversion is performed. The source SDF and
workbook preserve unpromoted tested-form, context and model fields. Original and
QSAR-ready forms remain distinct. A missing reference, identity, unit or domain
never becomes a zero. Conflicting duplicate B targets are excluded explicitly.
`chemical_identity.csv` describes provider structures with provisional AI review;
it does not add entries to the project's approved crosswalk.

The release can expand beyond the selection through source-first bulk structures.
EPA TEST coverage expansion still requires approved new identities and API access
or a qualified local installation; the current reader only audits stored output.
The source registry records documentation-only platforms separately from actual
prediction products. A catalog page is not a successful prediction batch.

## Additional stored TEST coverage

`expand_test_evidence.py` accepts the locally resolved dietary feature inventory
(`compound_id`, `query`, `canonical_structure`, `structure_inchikey`). It rechecks
the structure/key, then reuses the EPA full-key identity resolver. Only an
unambiguous exact match may fetch stored predictions. Ambiguous/unresolved
identities, empty stored outputs and sanitized request failures remain in the
collection ledger. Each chemical can fail without erasing other results. The
source inventory's dietary membership supplies no tested-inactive label.

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/expand_test_evidence.py \
  --features analysis/outputs/dietary-review-2026-11-04-final/features.parquet \
  --output experiments/external-evidence-NEW_RUN/dietary-test
```

Supply `COMPTOX_API_KEY` through the established local environment setup. Never
copy the key, `.env` file, request headers or exception messages into outputs.
The batch writes fresh raw EPA cache envelopes, candidates/crosswalk, separate
B TEST tables, source-code snapshots and hashes. It refuses an existing output
root. This is retrieval of existing provider predictions, not novel-structure
inference or a change to the project's original approved identities.

## Evaluate frozen pathways separately

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/evidence_models.py \
  --release analysis/outputs/separate-evidence-NEW_RUN \
  --output analysis/outputs/separate-evidence-models-NEW_RUN
```

Evaluation verifies every frozen output hash and refuses an existing destination.
It writes per-fold/pooled metrics, actual train/test membership, all held-out
predictions, standardized class/fold logistic weights, source/runtime/code
manifests, static figures and a standalone offline `walkthrough.html`. The
whole-cohort OOB diagnostic uses the existing binary API on low-LD50 versus the
other bins, with three repeats and the fixed seed; unsupported binary support
is explicit. It is separate from the primary three-class held-out metrics.
Code snapshots make frozen runs recoverable when maintained scripts evolve.

A/B agreement joins exact full keys. Membership `Tr` identifies known
teacher-training compound overlap, while `Tst`/unknown do not establish an
independent study or independence from a later model version. The workflow
writes a defer decision for C when the necessary independent evidence is absent.

## Compare sources and describe selection groups

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/evidence_comparison.py \
  --release analysis/outputs/separate-evidence-NEW_RUN \
  --models analysis/outputs/separate-evidence-models-NEW_RUN \
  --dietary experiments/external-evidence-NEW_RUN/dietary-test \
  --traits experiments/data/compound_traits.parquet \
  --output analysis/outputs/separate-evidence-comparison-NEW_RUN
```

The comparison verifies frozen input hashes and the exact traits input, reconciles
repeat TEST retrievals without votes or silent averaging, and reports unique full
structures. It retains source-cohort memberships separately from inferred labels.
Group descriptions use original selection membership; unknown origin/activity is
not converted into tested inactivity. Paired chemistry similarity uses radius-2,
1,024-bit Morgan fingerprints against the archived training-tag inventory. It does
not establish independence from an updated teacher or identify original studies.
A standalone offline walkthrough shows completed/provisional/planned status, the
actual metrics and the C decision. The [dated checkpoint](modeled-evidence-2026-11-12.md)
records the canonical local bundles and scientific limits.

The CATMoS SDF contract here is archive-specific. Provider documentation identifies
log(mg/kg), while current executable code exponentiates its internal prediction
before export. Do not apply this SDF scale interpretation to a new OPERA executable
CSV solely because it repeats the column name. Preserve this as an explicit
provisional normalization boundary, alongside TEST API and held Zenodo scale gaps.

## Same-target forest OOB exploration

The primary three-class LD50 models already have held-out macro-F1, logistic
class/fold weights and per-class metrics. `evidence_oob.py` adds a separate
whole-cohort forest diagnostic with the **same three-class target and fixed forest
profile**: 200 trees, leaf size 5, balanced class weights, seed 20261112. Ten
fixed-seed repeats shuffle each feature only within each tree's unsampled rows;
aggregate their changed class-probability votes and measure the macro-F1 drop.
Every row requires OOB votes. Constant/unused features have zero change.

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/evidence_oob.py \
  --release analysis/outputs/separate-evidence-2026-11-12-v2 \
  --models analysis/outputs/separate-evidence-models-2026-11-12-v3 \
  --output analysis/outputs/separate-evidence-multiclass-oob-NEW_RUN
```

This fits additional full-cohort diagnostic forests, without changing frozen
outer-fold predictions, choosing hyperparameters or combining A/B. Outputs retain
OOB class probabilities, votes, per-repeat macro-F1 drops, mean/SD importance,
profile, source/code/runtime hashes and class support. Larger positive drops
indicate greater reliance by that forest. Negative drops remain visible. Repeat
SD is stability, not a confidence interval or p-value: no formal significance
null test is performed. OOB F1 does not replace scaffold-held-out F1. A/B outcomes
and interpretation remain distinct; B measures teacher reproduction.
