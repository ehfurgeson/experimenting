# Accepted-data experiments — 17 November 2026

**The 120-structure run is retracted.** `plant-v1`, `plant-models-v2`,
`integrated-screen-v2`, and `results-v2` treated ECOTOX percent of control as
percent inhibition, required 2,260 plant observations and 120 three-axis
structures, and are not the current result. `plant-v3` corrected that scale
(733 observations, 208 high / 525 low). `plant-v4` then scored every
percent-of-control value at or below 100 with direction INC as stimulation / low
unless the comment recorded a decrease (204 high / 529 low). That over-correction
is superseded: stimulation applies only when the comment documents an increase or
stimulation. A comment that only names percent of control keeps inhibition =
100 − response. An unresolved contradiction stays unlabeled. Current bundles are
`plant-v5`, `plant-models-v5`, `integrated-screen-v5`, `toxicity-v2`,
`toxicity-models-v2`, `uncertainty-v2`, and `results-v5`. The
[candidate audit](candidate-audit-2026-11-17.md) records the shortlist.

This continuation follows the user's explicit instruction to assume all acquired
data is accepted and work with full experimental freedom. It advances beyond the
[earlier source audit](data-sprint-2026-11-17.md) without modifying that audit,
frozen A/B targets, historical source bytes or curated decisions. The
[workflow contract](accepted-sprint.md) owns commands and assumption policies.

## Expanded outcomes

| Accepted cohort | Exact toxicity structures | Classification structures |
| --- | ---: | ---: |
| Original A | 4,234 | 4,234 |
| Source-asserted experimental expansion | 4,678 (+444) | 5,003 |
| All-accepted experimental expansion | 8,375 (+4,141) | 9,520 |

The broad scenario accepts ChemIDplus's experimental status and NPASS's missing
acute/oral/experimental context as assumptions. Source fields and assumptions
remain distinct. These counts are the corrected `toxicity-v2` aggregation. The
pre-median `toxicity-v1` cohort was 4,679 (+445) and 8,381 (+4,147) exact
structures, with classification pools of 5,004 and 9,526. That cohort is not
current. Regression uses exact doses only; the additional 1,145 censored
classification structures have bounds wholly within a fixed LD50 bin. Volume/kg,
daily doses, unavailable structures and absent outcomes remain computationally
incompatible rather than receiving invented values. Existing A targets never change.
No CATMoS teacher values enter experimental targets.

The corrected plant pool (`plant-v5`) has **733 observations / 211 structures /
76 references**: 335 ECOTOX, 24 ChEMBL, 294 flavonoid and 80 prior accepted
categorical responses. There are **207 high and 526 low** response labels.
The retracted pool was 2,260 / 365 / 342 with 1,099 high and 1,161 low.
Numerical labels use at least 40% inhibition versus at most 20%. Stimulation
counts as low inhibition, not universal inactivity. Thirty-two structures keep
both outcomes in separate contexts.

## Fixed comparative models

Toxicity models use seven RDKit descriptors and the same five transitive
scaffold/connectivity partitions across all three training cohorts. The following
forest results use the **same unchanged 4,234 A outcomes**:

| Training cohort | Macro-F1 | Low-LD50 recall | MAE, log10 dose |
| --- | ---: | ---: | ---: |
| Original A | 0.4167 | 0.4965 | 0.6336 |
| Source-asserted expansion | 0.4311 | 0.5335 | 0.6295 |
| All-accepted expansion | 0.4387 | 0.5187 | 0.6254 |

These forests are `toxicity-models-v2`, refit on `toxicity-v2`. A paired
2,000-draw bootstrap over 1,096 chemical clusters gives an all-accepted macro-F1
difference of +0.0220 with conditional 95% interval +0.0030 to +0.0430; its MAE
difference is −0.0083 with interval −0.0181 to −0.0009. Neither interval includes
zero. These intervals condition on the fixed folds and predictions in
`uncertainty-v2`. The bootstrap does not refit the forests or support a safety
claim. The log10-median aggregation changes the tertile of 10 retained new
structures, withholds 4 new structures whose exact doses span more than 100-fold,
and withholds 2 lone assumed doses below 0.05 mg/kg. Corrected all-accepted exact
structures are 8,375, of which 3,934 new rows still carry an experimental-status,
route, or acute-context assumption. The 8,381 figure is the superseded
`toxicity-v1` cohort, not the current training set and not 4,141 newly verified
oral LD50s. The 1,080 and 3,400 mg/kg bins are project tertiles, not EPA or GHS
categories.

The pooled plant forest (`plant-models-v5`) uses inverse observation-frequency
training weights. Results below give equal total evaluation weight to each structure:

| Holdout | Quantitative-only macro-F1 | Including accepted categorical labels |
| --- | ---: | ---: |
| Random rows | 0.7158 | 0.7202 |
| Publication/reference | 0.5912 | 0.5561 |
| Joint scaffold/connectivity | 0.4861 | 0.5347 |

Quantitative chemical-holdout macro-F1 is 0.4861, and 0.5347 with accepted
categories. That is weak transfer. On the flavonoid root/germination series,
quantitative forest high-response F1 is 0.0000 under random-row holdout and 0.0884
under chemical-group holdout. That does not validate
the plant model and does not support a screening claim beyond the holdout.
The earlier plant-v1 table (about 0.68 / 0.52 / 0.52) belonged to the retracted
2,260-observation run. Random splitting shares repeated chemistry and studies.
Standardized logistic coefficients and five-repeat OOB permutation importance
are descriptive. OOB is a separate observation-weighted diagnostic forest because
inverse-frequency bootstrap sampling can leave rare observations without OOB votes.
OOB repeat SD is stability, not significance.

## Three-axis evidence and screening

`integrated-screen-v5` has **2,890 candidates**, **2,619** structures with an exact
catalog hit and an exact LD50, **69** with exact toxicity and a plant label, and
**49 with all three**. Of those 49, **10 are selected herbicides** and **4 are
selected natural products**. The earlier 120 three-axis count is retracted. An
exact catalog hit is a valid COCONUT or NPASS full key. Provider-key conflicts are
excluded. The project's selected herbicides are removed from `exact_catalog_hit`;
glufosinate and trifluralin stay unmatched. A catalog hit is not an origin claim.
Catalog-versus-other median LD50 is not an origin effect and is not cited as one.

The **11-member set is a mathematical prediction front**. It is not a
safer-herbicide shortlist and not a natural-product shortlist. Triasulfuron is a
catalog-key collision and is not a selected natural product. It is not on this front.
Predicted log10 LD50 is labeled as a prediction. A measured LD50 is shown from the
same full key or the same connectivity key. Butyl stearate's 32,000 mg/kg is one
ICE/HSDB limit figure (stored qualifier `=`, displayed `>`) repeated in later
ToxVal and NPASS rows, not three studies, and not the model prediction.

The table also retains **469 plant-protein records / 181 source references**,
including 40 Kd/Ki records. IC50 and other bioactivities stay in their own channel.
The 1,080 and 3,400 mg/kg bins are project tertiles, not EPA or GHS categories.

## Local reading package

Work root: `experiments/data_acquisition/2026-11-17-accepted-experiments/`.
Current bundles are `toxicity-v2/` (corrected aggregation), `toxicity-models-v2/`
and `uncertainty-v2/` (the refit forests and paired intervals), `plant-v5/`,
`plant-models-v5/`, `integrated-screen-v5/`, and `results-v5/`. `toxicity-v1/`,
`toxicity-models-v1/`, and `uncertainty-v1/` predate the log10-median refit.
`plant-v1/`, `plant-models-v2/`, `integrated-screen-v2/`, and `results-v2/` are
the retracted 120-structure run. `plant-v3/` corrected the percent-of-control
scale. `plant-v4/` is the INC-as-stimulation release and is superseded by
`plant-v5/`. `results-v4/` quoted the pre-refit forests.

## Verification

Focused regressions cover the log10 dose median, wide dose spans, the CL-20
percent-of-control comment, screen defaults, the report guard (733 and 49, not
2,260 and 120), and NPASS provider-key conflicts. Frozen A targets were checked
unchanged after the aggregation rebuild and again after the forest refit: 4,234
keys, no label changes. `toxicity-models-v2` and `uncertainty-v2` are that refit.
`verification.json` from the retracted run is not a check of this release.
