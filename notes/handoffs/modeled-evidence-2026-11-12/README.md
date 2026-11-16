# Handoff: grow both evidence pathways, then consider a combined pathway

Prepared **12 November 2026**. This is a **plan for a new agent**, not a record of
new acquisition, fitted toxicity models or a completed combined analysis.

## 1. The assignment in plain language

The professor wants comparisons supported by two kinds of evidence:

1. **Experimental pathway A:** toxicity or plant responses measured in real experiments.
2. **External-model pathway B:** estimates produced by documented outside models,
   such as EPA TEST. These estimates need not have a measurement for the compound.
3. **Possible combined pathway C, later:** consider using both kinds together,
   after A and B have been developed, evaluated and reported separately.

**The immediate priority is gathering as much useful, traceable data as possible
from as many accessible sources as possible.** Expand both the number of compounds
and the number of sources. Keep the original records, including failed queries,
out-of-domain predictions, missing results and disagreements. A larger number of
rows is not automatically a larger number of independent compounds or studies.

Follow this order: **audit → gather broadly → freeze separate datasets → model A
and B separately → compare them → decide whether C is justified**. Do not begin
by mixing predictions into the existing measured tables. Do not start pathway C
as a shortcut around a sparse experimental dataset.

This document was requested while the broader autonomous research goal was
paused. Creating the handoff does not resume that goal. The next agent should
follow the user's current authorization when starting execution.

## 2. Orientation, checkout and operating rules

Work in `/Users/ehfurgeson/Documents/GitHub/agrochem-toxicity` when using this
checkout. Local `main` is at `e94b9b6` after the reviewed experimental integration;
`origin/main` was still at `b771c87` when this handoff was written. Nothing was
pushed. Recheck Git state rather than assuming those pointers remain current.

Read these before editing:

- [Agent orientation](../../AGENTS/README.md), including project context.
- Unchanged [GOALS.md](../../GOALS.md), [current overview](../../notes.md),
  [incremental commit guide](../../INCREMENTAL_COMMIT_GUIDE.md) and
  [documentation rules](../../AGENTS/DOCUMENTATION.md).
- [Original handoff](../research-2026-11-11/README.md) for the experimental evidence.
- [EPA source contracts](../../../pipeline/docs/epa-chembl.md), especially TEST,
  hazard evidence and calculated properties; [decisions](../../../pipeline/docs/decisions.md).
- [Experimental findings](../../../analysis/docs/experimental-expansion-2026-11-12.md),
  [rat-source review](../../../analysis/docs/rat-source-review-2026-11-12.md),
  [binding pilot](../../../analysis/docs/binding-evidence.md), and
  [result inventory](../../../docs/results.md).

Use a new local-only branch for substantive research, for example
`experiment/external-modeled-evidence-2026-11-12`. Preserve main and prior bundles.
Create small, reviewable commits when authorized; **do not push**. Nothing under
`notes/` may be staged or committed. Do not alter GOALS.md, frozen source exports,
accepted labels or old manifests. Use new versioned outputs. The owner permits
creative, provisional experiments; identify them as AI experimental, not human
scientific review or established truth.

The [local preservation record](../../../docs/data.md#local-experimental-preservation--2026-11-12)
identifies the verified archive, historical Git bundle and one unresolved script
hash from a superseded preliminary run. The canonical final transfer run has
recoverable source. A clone alone lacks ignored research data. Keep raw scientific
assets local unless separate sharing permission exists. Do not copy credentials
into reports, logs or transfer bundles.

## 3. What exists now

### External predictions: collected, largely not analyzed

Read `experiments/data/epa_test_predictions.csv` or its Parquet sibling and
`experiments/data/epa_test_coverage.csv`. The cached retrieval dates are
**21 October 2026**. All 2,176 records are marked `predicted`; they represent
136 approved EPA identities ×16 endpoints. They are not 2,176 experiments, and
not every row contains a finite prediction.

| Endpoint as stored | Records | Finite values | Provider AD Inside / Outside | Stored units |
|---|---:|---:|---|---|
| Oral Rat LD50 | 136 | 120 | 120 /16 | mol/kg |
| 48 Hour Daphnia Magna LC50 | 136 | 125 | 125 /11 | mol/L |
| 96 Hour Fathead Minnow LC50 | 136 | 122 | 122 /14 | mol/L |

These counts describe this cache, not current service coverage or a validated
comparison cohort. In these three cached endpoints the finite-value and Inside
counts happen to agree. Do not generalize that rule to other endpoints/providers.
There are 16 endpoints overall, including toxicity and physicochemical predictions;
not all 16 are toxicity outcomes. Binary-labeled endpoint outputs may be scores
between zero and one; inspect documentation before thresholding.

Existing code:

- `pipeline/src/agrotox/epa_test.py` reads **already stored** TEST predictions.
  It does not submit a novel structure to a model. Keep that distinction.
- `pipeline/src/agrotox/epa_properties.py` separates calculated and experimental
  properties. Inspect its outputs for additional reusable provider estimates.
- `experiments/03_fetch_epa.py` orchestrates acquisition. It needs the existing
  environment credential; never print or archive the credential.
- Raw responses are under
  `experiments/data/raw/comptox/chemical/property/predicted/`.
- Current TEST rows preserve model name/ID, endpoint/value/unit, applicability
  domain (AD), QMRF fields and retrieval time. Raw responses also preserve useful
  fields **not promoted into the current TEST table**: source/model version
  (`sourceName`, e.g. TEST5.1.3), chemical structures, provider record ID,
  experimental comparator fields and error fields. Audit and retain these before
  extending the table. A provider's embedded experimental value needs its original
  source and training-set lineage checked before joining experimental pathway A.

### Experimental pathway: more developed, still limited

- Historical rat pilot:43 exact +25 censored observations,49 compound summaries,
  of which34 have exact medians. Frozen tertiles:1,080/3,400mg/kg. These are
  sample-derived bins, not regulatory hazard categories.
- Identity-approved ECOTOX screen:28 trout96h LC50 and13 Daphnia48h immobilization
  EC50 observations. Exposure duration is a separate field. The extra reported-
  context subset is0 trout/1Daphnia. Do not call all41 fully comparable experiments.
- Human adoption:19 natural-occurrence labels and80 activity decisions in four
  bounded policies. Individual policies still lack five-fold activity support.
- A73-compound heterogeneous activity experiment fit successfully but transferred
  poorly across publications. All three fixed models missed both high responses
  in a new20-compound radish test. More permissive pooling did not establish a
  general activity model. Read the checkpoint before repeating this approach.
- New primary rat review maps two acid-equivalent cases and distinguishes four
  overlap pairs. No historical rat admissions or bins changed. Material-tested,
  acid-equivalent, dietary and single-dose results remain distinct.
- The binding pilot has two structural complexes, no affinity predictor. Protein
  docking scores or crystal preparation concentrations are not measured Kd/Ki.
- Latest unfinished acquisition: `experiments/aquatic-series-2026-11-12/` has a
  downloaded, visually inspected Kühn1989 Daphnia paper. Its tables are **not yet
  transcribed or modeled**. A benzoic-acid full-text route failed; preserve the log
  under `experiments/daphnia-source-review-2026-11-12/`. Do not report planned data
  as an integrated dataset.

See `status_snapshot.json` in this folder for machine-readable cache counts and
hashes of starting inputs. It is an inventory, not a new scientific result.

## 4. Definitions that must stay separate

| Term | Meaning here | What it does not establish |
|---|---|---|
| Natural occurrence | A molecule is documented in a biological source | Plant inactivity, efficacy or safety |
| Plant activity | A response under a stated species/dose/time/endpoint | Universal herbicidal activity |
| Experimental toxicity | Measured outcome with traceable study context | Comparability with every same-named endpoint |
| External estimate | A named outside model's output | A new experiment or certain biological truth |
| Our surrogate model | Our model fitted to external estimates | Independent experimental validation |
| Binding structure | A deposited protein/ligand complex | A quantitative binding affinity or field efficacy |

**A/B are evidence pathways, not replacements for Track1/Track2.** Track1 studies
non-target toxicity and group differences. Track2 studies natural herbicidal
chemistry and plant activity. Either track may use A and B where scientifically
appropriate. TEST non-target toxicity predictions do not supply plant-activity
labels. For Track2, measured plant efficacy can be discussed alongside a separate
external non-target-hazard analysis. If a documented, fit-for-purpose external
plant-activity model cannot be found, record that gap; do not invent one.

Define “experimental-only” explicitly. At minimum all **outcome labels** in A
must come from experiments. Formula counts and structural fingerprints are derived
from structures, not toxicity experiments. Calculated logP and external predicted
properties must not be called measured inputs. If the professor requires both X
and y to be experimental, make a stricter measured-property subset and report its
coverage separately. Record feature provenance in either case.

BMD/BMDL are model-derived from experimental dose-response data, not independent
QSAR predictions. Retain them as a distinct evidence type. ToxCast/Tox21 are
experimental bioassays with processing/model-fit steps; a model-derived hit call
is not automatically an in-vivo toxicity measurement. CompTox and PubChem contain
mixed evidence; classify individual records, not entire websites.

## 5. Gather broadly: source queue and collection strategy

Use this as a starting queue, not a closed list. The official source links below
were checked for planning on12November2026. Recheck endpoint availability, version,
access method, licensing and validation documentation when executing. Do not
assume a source provides the same species/endpoint as another source.

| Priority | Source family | What to seek | Main caution |
|---|---|---|---|
| 1 | Existing EPA TEST cache; [CTX data domains](https://www.epa.gov/comptox-tools/computational-toxicology-and-exposure-apis-data-domains) | Audit all136 identities, missing outputs, endpoints, raw versions and domains; expand stored predictions to more compounds | Current adapter fetches stored outputs only; no new-structure inference |
| 1 | [EPA TEST](https://www.epa.gov/comptox-tools/toxicity-estimation-software-tool-test) | Documented external toxicity estimates; assess supported batch/local prediction routes for compounds without stored outputs | Installation, source version, structure handling, training overlap and AD must be retained |
| 2 | [NIEHS ICE/OPERA](https://ntp.niehs.nih.gov/iccvamreport/2025/technology/comp-tools-dev) | Predicted properties/ADME and relevant toxicity estimates; curated experimental data through the appropriate ICE products | Confirm which endpoint/model each product actually supplies; mirrored predictions are not independent |
| 2 | [VEGA](https://www.vegahub.eu/portfolio-item/vega-qsar/) | Relevant endpoint-specific QSAR outputs, reports and applicability-domain information | Do not turn platform reputation into blanket acceptance of every estimate |
| 2 | [EPA GenRA](https://www.epa.gov/comptox-tools/generalized-read-across-genra) | Documented read-across estimates where useful; retain analogues, similarity and source observations | Read-across may reuse the same experimental data used elsewhere |
| 3 | [OECD QSAR Toolbox](https://www.oecd.org/content/dam/oecd/en/topics/policy-issue-focus/quantitative-structure-activity-relationships-project/326598-qsar-briefing-notes.pdf) and well-documented published models/datasets | Additional transparent estimates and read-across; original underlying experimental studies | Qualify each workflow and endpoint; a database/model catalog is not itself a prediction dataset |
| parallel | ECOTOX, EPA hazard/ToxVal records, PubChem BioAssay, accessible primary papers, curated governmental datasets | More measured toxicities and full plant-response series, including low responses | Trace original experiments, dose basis and identities; mirrored citations do not add independent studies |
| expansion | Reviewed project compounds, dietary list, COCONUT/LOTUS and other documented structure/occurrence inventories | Broader chemical coverage; natural-origin leads with source/version metadata | Inventory membership is a lead, not verified plant inactivity or universal natural-origin truth |

Use multiple legitimate acquisition routes where available: existing local cache,
official API, official bulk files, permitted software/batch inference, repository
supplements and original papers. Avoid repeated single-compound calls when a
versioned bulk product is suitable. Do not bypass access controls or contact
people on the owner's behalf without explicit authorization. Log access gaps and
continue independent source work. Protect credentials and respect service limits.

Collection should proceed in auditable batches:

1. Start with the original176 resolved selection compounds and all currently
   reviewed literature/occurrence identities. Deduplicate exact structures while
   retaining aliases and memberships.
2. Extend to the200-compound dietary inventory and additional documented natural
   products/herbicides. Recheck full-key identity, stereochemistry, tested salt/
   acid/ester and mixtures. The Li2253255/2253236/2253237 identity holds persist.
3. Expand further through source-first chemical inventories. Do not stop at the
   original selection if sources support broader coverage. Keep a source-cohort
   field so later comparisons can assess selection bias.
4. For each source/batch, report attempted, resolved, ambiguous, successful,
   no-stored-output, failed and out-of-domain counts. Report unique structures,
   measured studies, model families, species and endpoint coverage separately.
5. Freeze versioned A and B releases after each major collection pass. Maintain a
   backlog for remaining sources so modeling does not wait for an impossible claim
   that every possible source in the world has been exhausted.

No hard numerical collection cap is set. Judge useful expansion by coverage,
independence, chemical diversity and endpoint compatibility, as well as row count.

## 6. Planned data contracts and quality checks

Proposed working root: `experiments/external-evidence-NEXT_DATE-run/`. Names below
are **planned artifacts**, not implemented commands or existing files.

- `sources.csv`: provider, product/model/version, official URL, access/rights,
  retrieval time, raw file/hash, method, endpoint scope, documentation, training-
  data availability and relationship to other sources.
- `chemical_identity.csv`: stable compound/substance IDs, exact SMILES/full key,
  parent/form relationship, molecular weight and its chemical basis, source IDs,
  mapping method, review status, aliases and unresolved reasons.
- `experimental_observations`: study/result IDs, actual tested form, species,
  strain/sex/stage, route, exposure and observation time separately, endpoint/
  effect, raw estimate/qualifier/units, bounds/CI and their meaning, concentration
  basis, purity/formulation, controls, measurement method and primary locator.
- `external_predictions`: provider record ID, model/family/version/method, exact
  queried structure and preprocessing, endpoint/species/route/duration, original
  value/units/transform, normalized value with conversion provenance, AD fields,
  uncertainty kind/value, analogues/training membership, retrieval/input/output
  hashes, failure state and review status. Keep sourceName from raw TEST payloads.
- `lineage_links`: original study/model IDs, mirrors, shared training datasets,
  consensus members, duplicates and uncertainty about relationships.
- `normalization_audit`, `coverage`, `excluded_records`, `collection_log` and a
  release `manifest.json` with code/locks/inputs/outputs/versions.

Keep A/B physical outputs and target columns separate. Never fill a missing
measurement with a prediction in A. Missing, outside domain, not calculable,
unavailable and zero are different. Unknown origin/activity stays unknown.
Provider embedded experimental comparators need their own measured-source audit.
Preserve rejected records and reasons; a parser accepting a row is not approval.

### Units and endpoint matching

Check whether a prediction is linear, logarithmic, negative-log molar or another
scale before conversion. The current cached TEST toxicity units are mol/kg and
mol/L, with small positive linear-looking values; retain raw metadata and verify
semantics from the provider. Never infer a transform from a plausible range alone.
For confirmed **linear** values and the correct queried chemical form:

- mg/kg = mol/kg × molecular weight(g/mol) ×1,000.
- mg/L = mol/L × molecular weight(g/mol) ×1,000.
- If supplied as pX = −log10(mol/unit), first recover mol/unit =10^(−pX).

Do not apply the parent acid's molecular weight to a salt or formulated mixture.
Do not treat mg/kg feed or mg/kg-day as an acute mg/kg body-weight dose. Do not
silently mix acid-equivalent and material-tested doses. Retain inequality/range
bounds and uncertainty separately; confidence intervals are not censoring bounds.

Rat oral LD50 is a practical first matching target. Fish TEST predictions name
**fathead minnow**, whereas the reviewed aquatic policy names **rainbow trout**.
They are not matched-species validation pairs. The cached Daphnia prediction is
labeled **LC50**, while the measured core is immobilization **EC50**. Check the
model training endpoint definition and effect, not just the species and48h label.
Start with matched subsets; show broader harmonization only as an explicit
sensitivity with its remaining differences.

## 7. Model each pathway separately

Write the protocol before new scores: target, chemical group meaning, endpoint
policy, exclusions, threshold/bin rules, feature set, splits, profiles, baselines,
metrics, uncertainty and selection rules. Freeze the inputs and keep test results
out of threshold or feature selection.

### A: learn from experimental outcomes

Use measured outcomes only. Begin with descriptive distributions and study-level
strata, then regression on a documented log-dose scale and/or classification when
support permits. State that **lower LD50 means greater acute hazard**. Call the
existing bins low/medium/high **LD50**, not low/medium/high safety. Their cutoffs
are historical cohort tertiles; do not call them regulatory categories.

Use fixed common cutoffs for direct A/B bin comparison; if estimating new cutoffs,
fit them on training data only and report a separate analysis. Do not turn lower
bounds into exact values. Use censored methods or bound-compatible sensitivity
analyses when appropriate. A sparse policy may validly return unsupported status.

### B: analyze external estimates and, where useful, learn a surrogate

First compare external predictions directly across chemical groups and model
families. Preserve AD Inside/Outside/unknown strata. Choose a documented primary
model/version before seeing favorable results; retain others as separate
sensitivity estimates. Several related models predicting one compound are not
several independent compounds or votes.

If fitting our own model to B outcomes, say explicitly: **the target is a model
estimate**. Its F1 or MAE measures reproduction of the teacher model, not agreement
with real animals or plants. Keep that surrogate separate from A models. Do not
use the same model's toxicity output or an algebraic equivalent as both feature
and target. Predicted physicochemical features need provenance and a separate
feature-block sensitivity; check for shared teacher/training-data leakage.

### Shared evaluation requirements

- Stable compound grouping across duplicate records, stereo/form-related
  structures where justified, and held-out scaffold/publication/provider checks.
  Keep all records for a chemical in one outer partition. No random row split
  across repeated doses, studies or predictions of the same chemical.
- Preprocessing and hyperparameter selection use training data only. Inspect
  actual train/test class and scaffold support. Do not relax validation to claim
  a strong model; separately named easier sensitivity tests may be informative.
- Fixed simple baselines first: majority classification; training-mean/median or
  simple descriptor regression. Logistic regression and random forest are useful
  comparisons, not presumed winners.
- Classification: F1 (positive class defined), macro-F1 for three bins, precision,
  recall, balanced accuracy, AUROC where defined, confusion counts and majority
  baseline. Explain class imbalance and calibration where support permits.
- Regression: MAE/RMSE on the stated transformed scale, rank correlation,
  residual/bias plots and prediction-interval coverage where available. Convert
  back carefully; a log-unit error is a multiplicative dose error.
- Explain standardized logistic feature weights without causal claims. Forest
  OOB permutation importance includes uncertainty/stability, but repeat SD is
  **not a p-value** and OOB does not hold scaffolds out. If formal significance is
  claimed, define a justified null/permutation scheme and account for grouping
  and multiple testing. Otherwise call it importance/stability, not significance.
- Report sample counts, independent groups, excluded/unsupported cases, AD,
  model version, source bias and uncertainty alongside scores. Never turn unknown
  plant activity or source membership into tested-inactive labels.

## 8. Compare A and B before considering C

Freeze paired, compatible compound/endpoint records with both evidence types.
Analyze coverage gained, dose/rank disagreement, error by group, AD and chemical
similarity, and sensitivity to experimental quality and duplicate resolution.
Do not treat B's larger coverage as evidence that its values are experimentally
correct. Disagreement can reveal identity, unit, context or model-domain problems.

Audit **external-model training overlap**: a measured record used to build TEST
or another teacher is not an independent test of that teacher. Use a truly
held-out experimental subset if identifiable. If training membership cannot be
established, mark independence unknown and describe the comparison as agreement,
not independent validation. Provider confidence/AD Inside is not proof of accuracy.

A model trained on B and evaluated against A must retain these same independence
cautions. Do not claim safety or field efficacy from a toxicity surrogate. For
Track2, keep literature efficacy evidence alongside non-target hazard, without
multiplying them into an unsupported universal score.

## 9. Only later: decide whether to try combined pathway C

This is a future decision, not authorization within this planning deliverable to
run C now. First complete and document A and B collection releases, model fits
or explicit unsupported statuses, and paired comparisons. Write a decision note
on what combination could add, the compatible endpoint, shared data lineage,
uncertainty and leakage risks. If no defensible design exists, defer C explicitly.

Possible designs to assess (do not implement all by default):

1. Use external predictions as an additional feature to predict measured outcomes,
   comparing against A-only on the **same untouched experimental test set**.
2. Pretrain on model estimates, then update on measured training data; keep
   experiments as the evaluation target and track teacher training overlap.
3. Use source-aware weighted or hierarchical models that retain evidence-type
   indicators and uncertainty, rather than pretending all rows are measurements.

Never simply concatenate duplicate measured/predicted labels as independent rows.
Measured and predicted values must remain distinguishable and recoverable.
Weights are documented assumptions, not scientific truth. Show A-only, B-only and
C on common evaluation cohorts where meaningful. Test sensitivity to AD, source
weights and coverage/chemical-class shifts. Fit any learned blend/calibration
inside training folds only. C earns support through measured held-out performance
and uncertainty, not just a higher training score or more completed rows.

## 10. Proposed deliverables and completion checks

A useful first release contains:

- A broad source-search/collection log, including attempted inaccessible sources,
  resource/version/rights notes and a next-source backlog.
- Separate raw and normalized A/B releases, identity/lineage tables and coverage
  by compound, chemical group, endpoint/species and model family/AD.
- An audit of the existing TEST136-compound cache, including raw version fields,
  unit semantics, missing/outside-domain results and duplicate/mirror handling.
- Expansion beyond the original selection where sources allow; report the actual
  increase in unique structures and independent source coverage.
- Independently documented A and B analysis/modeling reports with actual split
  membership, metrics/baselines, coefficients/OOB diagnostics and limitations.
- A paired A/B comparison with experimental-context and teacher-training overlap
  audits; no overstated external validation.
- A written **go/defer/design decision for C**, after the separate work above.
- A simple learning/presentation summary with “completed”, “provisional” and
  “planned” labels; versioned manifests, required tests and reproducible commands.

A blocked source or unsupported model is a recorded result, not permission to
invent data or hide the gap. Continue other collection sources while specific
access/identity issues remain open. The goal is more usable evidence and more
honest comparisons, not a quota of favorable predictions.

## 11. Immediate first tasks for the next agent

1. Recheck checkout, instructions, data availability and this snapshot's hashes.
2. Inventory the existing raw TEST/other predicted-property records without
   modifying them. Inspect versions, model reports, endpoint semantics and AD.
3. Write the A/B schema and normalization/acquisition protocol; identify which
   current adapters can be reused and what is actually missing.
4. Begin source collection in staged batches, first TEST coverage expansion and
   documented additional sources, in parallel with measured-source recovery as
   useful. Keep separate data products from the start.
5. After a major collection pass, freeze A/B releases and proceed with the
   separate modeling/evaluation steps above. Decide about C only afterward.

Use locked environments from repository root:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project pipeline --locked --offline pytest pipeline/tests -q
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline pytest analysis/tests -q
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline ruff check analysis pipeline
```

These are existing verification commands, not new acquisition/modeling commands.
Network acquisition needs its own permitted access and immutable raw cache;
normal tests stay offline. Do not run the broad acquisition script merely to
inspect the existing cache. Latest merge validation was300 analysis tests and
1,076 pipeline tests; these are historical software checks, not biological proof.
