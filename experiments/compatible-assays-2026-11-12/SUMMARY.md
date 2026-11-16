# Compatible-assay expansion, 2026-11-12

Local, user-authorized AI experiments; frozen inputs, labels and results unchanged.

## Recovered evidence

Primary full text: 10.3390/ijms13055406, Tables 1/2 and methods 3.2/3.3/3.5.
27 named compounds (including catechol, which is not a flavonoid), two species,
three doses (1/10/100 µM), germination counts and radicle lengths at 120 h:
324 observations, not 324 compounds. Includes all table rows, not just significant
results. Raw means, SDs, significance symbols, controls, units, source cells and
derived mean inhibition retained. No antioxidant measurements treated as plant
activity. Three Petri dishes ×10 seeds are reported per determination; no per-seed
pseudo-replicates or propagated uncertainty were created.

Ratios use `100*(1-treated_mean/control_mean)`; negative inhibition denotes
stimulation. The source gives water or 0.5% acetone vehicle but not a vehicle per
compound, and reports no vehicle-control difference. A ratio of rounded means is
not an IC50, confidence interval or statistical significance result. 120 h is
explicit in the tables; spelling 'radical' in source is normalized to 'radicle'.

All 27 literal/normalized PubChem name queries returned one record. Full RDKit
InChIKeys agree with retrieved SMILES. Sample identity, stereochemistry and naming
remain provisional AI mappings; origin is unknown for every row. None is promoted
to an accepted natural-product occurrence or a generally inactive compound.

## Fixed policy experiment

Twelve separate species × endpoint × dose policies: high response >=50% mean
inhibition, low inhibition <=20%, intermediate unknown. Thresholds are analyst
choices after literature inspection, not preregistration, and were not tuned for
scores. Stimulation belongs in low inhibition for this narrow target, not general
biological inactivity. No endpoints/species/doses pooled; no fitting.

Both 100 µM root-growth policies independently have 2 high /18 low /7 intermediate.
The 20 labeled structures have 2 high-bearing and 9 low-bearing Murcko groups.
All four representations fail five-fold preflight: need at least three more high
compounds and three more high-bearing scaffold groups. Other policies have 0–1
high compound. This source adds chemically broader low-response evidence but does
not create a supported standalone classifier.

Six retrospective O-methylation pairs yield 36 descriptive comparisons across the
two species and three doses. Constitutional demethylation checks pass, ignoring
stereo explicitly. `analysis-v2/methylation_pairs.svg` shows 100 µM pairs.
Chrysin and pinocembrin dimethyl ethers have stronger mean root inhibition than
parents in both species. The 3-hydroxyflavone pair has a small opposite difference
in radish. Do not infer a universal methylation benefit, causation, mechanism,
field efficacy, selectivity or safety. Means have wide source SDs and uncertainty
of differences cannot be reconstructed without replicate-level data/covariance.

## Other leads and failures

- 10.1186/s12870-016-0875-4: cached primary full text and 22 named hit table rows.
  19 inhibitors and 3 stimulators are a selected subset of 1,040 screened chemicals,
  not evidence that all remaining library members were tested inactive in the
  secondary seedling assay. Values are percent of control, not percent inhibition.
  Seven-day wording versus 10–14-day final incubation needs reconciliation; no
  activity policy adopted here.
- 10.1016/j.isci.2025.112375: cached primary full text; 1,519 Prestwick molecules,
  mutant-specific growth screen. Full datasets and code available on request;
  library membership/hit omission is not a negative activity label. No outreach.
- 10.3390/agriculture12101746: 18-metabolite Cuscuta screen remains a useful lead,
  MDPI retrieval403 and web429. No table reconstructed from snippets.
- First local PubChem attempt failed because `inspect.py` shadowed Python stdlib
  inspect; renamed `inspect_tables.py`, retry succeeded. Initial `analysis-v1/`
  stopped during Altair tooltip type inference before manifest/figure; retained
  with exact `analysis_v1_failed_source.py`. It contains five exploratory pairs,
  superseded by the six-pair, correctly typed, complete `analysis-v2/`. Do not use
  the incomplete directory as a verified run.

## Reproduction and verification

From repo root, use `UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis
--locked --offline python SCRIPT`. Acquisition scripts `fetch.py` and
`fetch_identities.py` need network access. `inspect_tables.py` derives HTML text
and raw tables, `transcribe.py` makes `transcription-v1/`, `analyze.py` makes
`analysis-v2/`; choose new output versions before rerunning. `verify.py` verifies
the current versions offline. `verification.json`:324 source-cell and ratio
checks,12 policies,27 structures,36 paired comparisons,6 constitutional graph
checks and136 input/output/code hashes pass. Figure PNG rendered and inspected.
These are internal consistency checks, not independent source/chemistry review.
No production code changed; no analysis or pipeline test suite rerun in this unit.

## Fixed-model transfer after the evidence checkpoint

After committing the source-specific evidence, wrote `external_protocol.json`
before computing new transfer scores. Primary test is radish root growth at
100 µM/120 h (20 labeled compounds,2 high/18 low); other species/doses were not
used to select a better score. `external_transfer.py` makes `external-inputs-v1/`
and `analysis/outputs/experimental-flavonoid-transfer-2026-11-12/`.

The old 73 training compounds retain every feature/label value except the common
experimental policy name, extended explicitly to v2. Added27 structures,7 unknown
excluded from transfer. No canonical-structure overlap. Three fixed profiles,
threshold.5, same preprocessing and seed; no hyperparameter/model/threshold
selection. Main publication-only test trains on the original73 exclusively.

| Model | F1 | Precision | Recall | Balanced accuracy | AUROC | TN/FP/FN/TP |
|---|---:|---:|---:|---:|---:|---|
| Raw formula logistic |0|0|0|0.4444|0.5000|16/2/2/0|
| Morgan logistic |0|0|0|0.2778|0.3333|10/8/2/0|
| Morgan forest |0|0|0|0.2500|0.2778|9/9/2/0|

Training-majority predicts all high: F1.1818 and balanced accuracy.5. All fixed
models miss both high responses. Maximum radius2/2048 Morgan Tanimoto against
old training ranges0.1111–0.2388 for the20 test compounds. No universal
out-of-domain cutoff or calibrated applicability claim follows.

Scaffold sensitivity removes21 He2011 training compounds because their benzene
Murcko group is shared with test catechol. Not a chemical near-duplicate test!
Train52 (27high/25low), no shared Murcko group. Formula still misses bothhigh;
Morgan logistic predicts15/20high with2TP,13FP (F1.2353,precision.1333,recall1,
BA.6389,AUROC.4167). Forest predicts18/20high with2TP,16FP (F1.2,precision.1111,
recall1,BA.5556,AUROC.3333). Sensitivity is unstable, not a selected improvement.

All four publications are evaluated symmetrically in secondary diagnostics;
adding the low-response panel does not fix transfer. Publication-only He F1 is0
for formula/forest and.0645 for Morgan logistic, Li F1 is0/0.3333/0 respectively.
The expanded labeled pool is43high/50low, with source-dependent class balance.
Targets remain incompatible source-specific response extremes, so failure does
not isolate a molecular cause or estimate a universal herbicidal endpoint.
No retraining from the test outcome, tuning, safety claim or candidate scoring.

`verify_external.py` independently recomputes24 report/confusion/metric rows from
558 saved predictions, checks old73 rows unchanged (except policy name), actual
train/test IDs and scaffold disjointness, and94 input/output/code/lock hashes.
`external_verification.json` records success. No production code or tests changed.
