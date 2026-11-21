# Accepted-data sprint experiments

**Retracted run:** `plant-v1/`, `plant-models-v2/`, `integrated-screen-v2/` and
`results-v2/` interpreted ECOTOX percent of control as percent inhibition and
reported 120 three-axis structures. That run is not current. `plant-v3/` corrected
the scale. `plant-v4/` then scored every percent-of-control value at or below 100
with direction INC as stimulation unless the comment recorded a decrease. That is
superseded by `plant-v5/`: stimulation (−response, low) applies only when the
comment documents an increase or stimulation. A comment that only names percent of
control keeps inhibition = 100 − response. An unresolved contradiction is unlabeled.
Values above 100 stay `100 − response`. Use `plant-v5/`, `plant-models-v5/`,
`integrated-screen-v5/`, `toxicity-v2/`, `toxicity-models-v2/`, `uncertainty-v2/`
and `results-v5/`. The [candidate audit](candidate-audit-2026-11-17.md) owns the
shortlist. `toxicity-models-v1/` and `uncertainty-v1/` are the pre-median forests.

On 17 November 2026 the user explicitly authorized treating all acquired data as
accepted and working with full experimental freedom. This continuation implements
that instruction. The [earlier audit](data-sprint-2026-11-17.md), source records,
review decisions and frozen A/B cohorts remain available unchanged.

Build the accepted toxicity releases from the existing local sprint:

```bash
uv run --project analysis --locked python analysis/accepted_sprint.py \
  --sprint experiments/data_acquisition/2026-11-17-data-sprint \
  --release analysis/outputs/separate-evidence-2026-11-12-v2 \
  --output experiments/data_acquisition/NEW_ACCEPTED_RUN/toxicity
```

`acceptance.json` records the user's declaration. Two cohorts expose its effect:
`source_asserted` admits rat acute oral LD50 data with an explicit experimental
flag; `all_accepted` additionally treats ChemIDplus's undetermined experimental
flag and NPASS's missing route/acute/experimental context as accepted experimental
assumptions. The missing source fields remain missing in original records, and
the applied assumptions remain named in every normalized row.

The exact cohorts preserve all frozen A targets and add new full structures using
the median of distinct reported doses on the log10 scale. An even count is not the
arithmetic mean of the mg/kg values. Spans greater than 100-fold, and a lone assumed
dose below 0.05 mg/kg, are withheld instead of collapsed to one exact target.
Repeated identical values cannot increase their weight and are not multiple studies.
The 1,080 and 3,400 mg/kg bins are project tertiles, not EPA or GHS categories. Explicit g/kg and ug/kg convert to mg/kg; volume/kg and
daily dose units do not. Unparsable identities remain computationally unavailable;
source disagreements do not justify inventing a structure or stripping salts.
Existing B structures can resolve identities, while teacher predictions never
become measured labels.

Classification cohorts additionally use censored-only compounds whose complete
bound lies inside one fixed 1,080/3,400 mg/kg class. Cross-bin bounds stay unknown;
conflicting bound classes remain in the conflict ledger. Censors never become
regression targets. Existing A labels remain unchanged when new sources disagree;
those disagreements are retained in a separate ledger. All source records, prior
holds, acceptance assumptions, runtime code and input/output hashes persist.

This accepted experimental scope allows comparative models and exploratory plant
pooling without a further approval step. Such analyses retain their actual
endpoints, split definitions and source context; acceptance does not imply that
one study became an independent external validation or that absent values became
measured outcomes. See [analysis decisions](decisions.md#accepted-data-experiments).

## Matched toxicity experiment

```bash
uv run --project analysis --locked python analysis/accepted_toxicity_models.py \
  --release experiments/data_acquisition/NEW_ACCEPTED_RUN/toxicity \
  --output experiments/data_acquisition/NEW_ACCEPTED_RUN/toxicity-models
```

The three training cohorts (frozen A, source-asserted expansion, all-accepted
expansion) use the same five held-out partitions on the widest cohort. Transitive
scaffold/connectivity groups never cross folds. Regression uses exact targets;
classification additionally uses unambiguous censored classes. Evaluation strata
separate unchanged A, new source-asserted structures and additional accepted
structures. External evaluation targets use the all-accepted aggregation; this can
differ from narrower training targets. These comparisons do not reuse historical
scores from differently partitioned cohorts.

Fixed median/majority, ridge/logistic and forest profiles use the existing seven
RDKit descriptors. Outputs include pooled per-stratum/per-class metrics, actual
held-out predictions, split membership, standardized logistic weights and binary
low-LD50 OOB permutation diagnostics. Five OOB repeats measure stability, not
statistical significance or held-out publication performance.

`toxicity-models-v2` was refit on `toxicity-v2`. That cohort has 4,678
source-asserted exact structures (+444) and 8,375 all-accepted exact structures
(+4,141). Those additions are not 4,141 newly verified oral LD50s; 3,934 of the
new exact rows still carry an experimental-status, route, or acute-context
assumption. The pre-median `toxicity-v1` cohort (4,679 / 8,381 exact structures)
is not the current training set. On the same 4,234 unchanged A outcomes, forest
macro-F1 is 0.4167, 0.4311 and 0.4387. Forest log10-dose MAE is 0.6336, 0.6295
and 0.6254. The all-accepted macro-F1 difference is +0.0220, conditional 95%
interval +0.0030 to +0.0430. The MAE difference is −0.0083, interval −0.0181 to
−0.0009. Neither interval includes zero. They condition on the refit predictions
and do not refit inside the bootstrap. Ten retained new structures change tertile
relative to the arithmetic mean of mg/kg. Four wide exact-dose spans and two lone
assumed doses below 0.05 mg/kg are withheld. The 1,080 and 3,400 mg/kg cuts are
project tertiles, not EPA or GHS categories.

## Accepted plant-response experiments

```bash
uv run --project analysis --locked python analysis/accepted_plant.py \
  --sprint experiments/data_acquisition/2026-11-17-data-sprint \
  --frozen analysis/outputs/separate-evidence-2026-11-12-v2 \
  --adoption analysis/outputs/human-review-adopted-2026-11-11-final \
  --flavonoids experiments/compatible-assays-2026-11-12 \
  --output experiments/data_acquisition/NEW_ACCEPTED_RUN/plant
uv run --project analysis --locked python analysis/accepted_plant_models.py \
  --release experiments/data_acquisition/NEW_ACCEPTED_RUN/plant \
  --output experiments/data_acquisition/NEW_ACCEPTED_RUN/plant-models
```

The retrospective numerical policy uses inhibition at least 40% for high response,
at most 20% for low inhibition and intermediate/absent results as unknown. Complete
bound intervals can establish a class; approximate numerical responses are accepted
as reported points. ECOTOX DEC/INC represent inhibition/stimulation when the
comment documents a percent change. A comment that only names percent of control
keeps inhibition = 100 − response even if direction is INC. Stimulation is low
inhibition, not a claim of general inactivity. NOEC and NEF do
not create numerical zero values when reported responses are missing. The accepted
ChEMBL source dose and identity mappings, including the previous Logran and
podolactone holds, are usable under the user's assumption. Original fields persist.
The prior flavonoid mean-ratio responses and original accepted categorical policies
are included, with the latter retaining their own thresholds.

`plant-v5` has 733 observations, 211 full structures and 76 references:
335 ECOTOX, 24 ChEMBL, 294 flavonoid and 80 accepted categorical responses.
There are 207 high and 526 low responses; 32 structures have both outcomes in
different contexts. The `plant-v4` counts of 204 high and 529 low are stale.
Observations remain distinct rather than assigning one universal
activity to each compound. The audit retains every screened native source record
with explicit missing-response and unresolved-identity counts.

The pooled model is an authorized experimental response-band classifier. It compares
numeric-only versus numeric-plus-categorical cohorts, and random rows versus
reference-held-out versus scaffold/connectivity-held-out partitions. Repeated
chemicals receive inverse-frequency training weights. Source-specific and pooled
metrics are shown both per observation and with equal total weight per structure.
Chemical and reference overlap are counted for every fold. Random-row and OOB
performance can contain repeated chemistry/study context and must be read alongside
the protected split results. Logistic coefficients and OOB feature diagnostics are
descriptive, without causal or statistical-significance interpretation.
The OOB diagnostic fits a separate forest without inverse-frequency sample
weights: weighted bootstrap sampling can otherwise include rare observations in
every tree and leave them without any OOB vote. Its observation-weighted result
is distinct from the chemically balanced held-out fits.

## Integrated evidence and experimental screen

```bash
uv run --project analysis --locked python analysis/accepted_screen.py \
  --accepted experiments/data_acquisition/2026-11-17-accepted-experiments \
  --sprint experiments/data_acquisition/2026-11-17-data-sprint \
  --output experiments/data_acquisition/NEW_ACCEPTED_RUN/integrated-screen
```

Defaults are `plant-v5`, `plant-models-v5` and `toxicity-v2`. The screen covers
selected compounds, exact catalog hits and measured plant-response structures.
Catalog membership is a valid COCONUT or NPASS full key. Provider-key conflicts
are not hits. Selected herbicides are excluded from `exact_catalog_hit`. That
column is not an origin claim. Missing catalog membership stays unknown origin.
It exports 469 plant-protein evidence records from 181 source references; 40 Kd/Ki
records remain separately tagged as affinity endpoints, while enzyme/other activity
records retain their own endpoints rather than becoming direct binding affinities.

`integrated-screen-v5` has 2,890 candidate structures, 2,619 with an exact catalog
hit and exact toxicity, 69 with exact toxicity and plant responses, and
**49 with all three**. Of those 49, 10 are selected herbicides and 4 are selected
natural products. The 11-member set is a mathematical prediction front, not a
safer-herbicide or natural-product shortlist. Predicted log10 LD50 is a model
number. A measured LD50 is shown from the same full key or the same connectivity
key. These are full-data fits, including in-sample compounds, separate from held-out
scores. Catalog-versus-other median LD50 is not an origin effect.
Descriptor-space nearest distances describe coverage and are not chemical similarity
or calibrated uncertainty. Original selection names/IDs and unscorable input rows
remain recoverable. The queue is an experimental research screen, not a validated
efficacy or safety ranking.

## Conditional uncertainty and final report

```bash
uv run --project analysis --locked python analysis/accepted_uncertainty.py \
  --models experiments/data_acquisition/NEW_ACCEPTED_RUN/toxicity-models \
  --output experiments/data_acquisition/NEW_ACCEPTED_RUN/uncertainty
uv run --project analysis --locked python analysis/accepted_report.py \
  --accepted experiments/data_acquisition/2026-11-17-accepted-experiments \
  --output experiments/data_acquisition/NEW_ACCEPTED_RUN/results
```

Uncertainty uses 2,000 paired bootstrap draws over 1,096 scaffold/connectivity
clusters in unchanged A, retaining paired held-out predictions from
`toxicity-models-v2`. The bootstrap does not refit the forests or account for
source-study independence. The all-accepted expansion's macro-F1 difference is
+0.0220 with conditional 95% interval +0.0030 to +0.0430; MAE difference −0.0083
has interval −0.0181 to −0.0009. Neither interval includes zero. That is a
conditional statement about these fixed predictions, not a safety claim.

`accepted_report.py` reads `plant-v5`, `plant-models-v5`, `integrated-screen-v5`,
`toxicity-v2`, and the refit `toxicity-models-v2` / `uncertainty-v2` metrics.
It refuses the retracted 2,260-observation / 120-structure release. The banner
counts come from the manifests. `results-v5/` is the current reading package.
`results-v2/` is the retracted plant report. `results-v3/` is the plant-v4 report.
`results-v4/` quoted the pre-refit forests.
