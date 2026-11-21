# Corrected compound-candidate audit — 17 November 2026

We have hypotheses with relatively high predicted LD50 and plant-response scores,
but no validated claim of selectivity for plants over humans or other animals.
This audit supersedes plant-derived results in the original accepted sprint.

## Corrected response interpretation

Candidate inspection exposed an ECOTOX normalization error: percentages of control
were treated as percentages of inhibition. For example, (Z)-3-hexen-1-ol,
`UFLHIIWVXFIJGU-UHFFFAOYSA-N`, has a Taxus biomass response of 70% of control
(DOI 10.3389/fpls.2018.00335). This means 30% inhibition, which is intermediate
under our policy, rather than a high-response label of 70% inhibition. We now
require an explicit response basis, convert control percentages as `100 − value`,
reverse inequality qualifiers, and leave undocumented scales unknown.

`plant-v5` contains 733 observations, 211 structures and 76 references:
335 ECOTOX, 24 ChEMBL, 294 flavonoid and 80 accepted categorical observations.
There are **207 high and 526 low** responses; 32 structures have outcomes in both bands.
`plant-v4` had labeled three bare percent-of-control INC rows as stimulation (204 high /
529 low). Those are high again: atrazine / Lemna gibba `ECOTOX:2170933` (8% of control,
inhibition 92) and `ECOTOX:2170996` (2.6% of control, inhibition 97.4), and Brassica
napus `ECOTOX:2543100` (6% of control, inhibition 94). CL-20 on ryegrass
(`ECOTOX:2063905`, comment “OF CONTROL, FROM GRAPH, SIGNIFICANT INCREASE OVER CONTROL”)
stays low. Helianthus `ECOTOX:2075225` (97% of control) and Malus `ECOTOX:2493439`
(87% of control) also stay low; signed inhibition is 3 and 13 rather than −97 and −87.
`plant-v3` and `plant-v4` are superseded. Frozen toxicity labels are unchanged.

`plant-models-v5` forest results, with equal total weight per structure:

| Training pool | Random-row macro-F1 | Publication-held-out | Chemical-group-held-out |
| --- | ---: | ---: | ---: |
| Quantitative only | 0.716 | 0.591 | 0.486 |
| Including accepted categories | 0.720 | 0.556 | 0.535 |

Quantitative chemical-holdout macro-F1 is 0.486, and 0.535 with accepted categories.
That is weak transfer. On the flavonoid root/germination series, quantitative forest
high-response F1 is 0.000 under random-row holdout and 0.088 under chemical-group
holdout. These scores do not validate the plant model and do not support a screening
claim beyond the holdout. The `plant-models-v4` table (0.729 / 0.585 / 0.565 and
0.708 / 0.564 / 0.553) is stale. Candidate scores are full fits and can include training compounds.
Seven descriptors also give identical scores to several stereoisomers.

`integrated-screen-v5` has 2,890 candidates, an **11-member mathematical prediction
front**, 2,619 catalog-plus-exact-toxicity structures, 69 plant-plus-exact-toxicity
structures, and **49 structures with all three axes**. Of those 49, 10 are selected
herbicides and 4 are selected natural products. This replaces the retracted 120-structure
`results-v2` run and the `integrated-screen-v3` counts (2,908 candidates, 13 on the
front). The front is not a safer-herbicide list and not a natural-product shortlist.
`exact_catalog_hit` is a valid catalog key with selected herbicides removed, not an
origin claim. Provider-key conflicts are excluded. Triasulfuron and pethoxamid remain
catalog-key collisions; they are synthetic herbicides and are not selected natural
products. Triasulfuron is not on this prediction front. Catalog-versus-other median LD50 is not an origin effect.

## Illustrative shortlist

These four were selected for interpretable names and joint model scores, rather
than by a newly validated threshold. They are not an exhaustive or validated ranking.

| Compound | Measured LD50 | Predicted LD50 (model) | High plant-response score | Labeled plant observations |
| --- | --- | --- | ---: | ---: |
| Butyl stearate (butyl octadecanoate) | >32,000 mg/kg. One ICE/HSDB limit figure (`acute_oral_1852`), stored qualifier `=`, repeated in later ToxVal and NPASS rows. Not three studies and not a new numeric LD50. | 6,761 mg/kg (log10 3.830) | 0.844 | 0 |
| Borneol, unspecified stereo | No exact LD50 on this key. Same connectivity: isoborneol 5,200 mg/kg (log10 3.716) and (1S)-endo-borneol 5,800 mg/kg (log10 3.763). | 3,081 mg/kg (log10 3.489) | 0.838 | 0 |
| Linoleic acid | No exact LD50 on this key or its connectivity. | 4,754 mg/kg (log10 3.677) | 0.783 | 0 |
| Citral (geranial selection key) | No exact LD50 on this key. Same connectivity: about 4,950 mg/kg (log10 3.695 and 3.696). | 2,972 mg/kg (log10 3.473) | 0.732 | 0 |

Predicted LD50 is the model number from `integrated-screen-v5`. It is not the
compound's LD50. The plant score is an uncalibrated response-band classifier output.

Citral has the strongest direct phytotoxic literature support among these checked
leads: [Dudai et al., Weed Science](https://www.cambridge.org/core/journals/weed-science/article/abs/phytotoxic-potential-of-the-terpenoid-citral-on-seedlings-and-adult-plants/283BD0C10FFCD575EE53A9535AFDA535)
report effects on seedlings and adult plants. That evidence is outside the current
labeled modeling pool and does not validate our exact structure/form prediction.
[Bundit et al.](https://doi.org/10.26651/allelo.j/2021-54-1-1345) report linoleic-acid
phytotoxicity in lettuce assays. Butyl stearate and borneol remain prediction-led
hypotheses in this audit. Butyl stearate's measured figure is the limit above,
not the model prediction, and source acceptance does not make it proof of human
safety. The unspecified-stereochemistry borneol row has no exact LD50 of its own;
the table shows the measured stereoisomers instead of substituting the prediction.

A high acute LD50 leaves chronic, developmental, reproductive and nonmammalian
hazards unanswered. DEHP illustrates the problem: it also scores favorably on this
screen, despite [ATSDR's documented reproductive and developmental concerns](https://wwwn.cdc.gov/TSp/ToxFAQs/ToxFAQsDetails.aspx?faqid=377&toxid=65).
Thus the supported outcome is a research shortlist. Establishing selectivity needs
plant dose-response evidence alongside relevant animal endpoints and exposure.

## Reproduction and artifacts

Run the documented plant builder and evaluator into fresh directories. Then:

```bash
uv run --project analysis --locked python analysis/accepted_screen.py \
  --accepted experiments/data_acquisition/2026-11-17-accepted-experiments \
  --sprint experiments/data_acquisition/2026-11-17-data-sprint \
  --output experiments/data_acquisition/NEW_RUN/integrated-screen
```

Defaults are `plant-v5`, `plant-models-v5`, `toxicity-v2`, `toxicity-models-v2`
and `uncertainty-v2`. Current local bundles: `plant-v5`, `plant-models-v5`,
`integrated-screen-v5`, `toxicity-v2`, `toxicity-models-v2`, `uncertainty-v2`,
and `results-v5`. The historical `results-v2` report is the
retracted 120-structure run. `results-v4` quoted the pre-refit forests.
`accepted_report.py` renders the corrected release and refuses 2,260 observations
or 120 three-axis structures.

Verification: the report builder hash-checks the corrected bundles and refuses
2,260 observations or 120 three-axis structures. Analysis tests: 390 passed.
Pipeline tests were not re-run.
