# Natural-product toxicity rescreen

The rescreen covers 7,964 distinct structures. It includes the original
116 natural-product entries, the newly reviewed literature structures,
7,636 exact COCONUT or NPASS matches to the ICE or CATMoS cohorts, and
the 568 trusted-assumption NPASS toxicity structures. There are 258
NPASS additions outside the exact catalog–cohort matches and 70
reviewed or literature structures outside both larger groups. The
reviewed and literature panel has 119 distinct resolved structures.
Seven literature rows retain identity holds. The catalog part of the
screen uses the previously toxicity-linked subset. Catalog membership
alone leaves biological origin unresolved.

All twelve previously evaluated toxicity endpoints were applied. Exact
structures already in an endpoint cohort use their saved scaffold-held-out
predictions. Other structures use a full fit to that endpoint's cohort.
Both forest scores, source units, observed outcomes where available and
the nearest training-structure Morgan similarity are exported. The
endpoint metrics include the earlier held-out performance. Low
similarity highlights extrapolation but does not give a validated
applicability-domain cutoff.

For binary endpoints the summary reports observed positive outcomes
independently from positive model agreement. When neither an observed
positive nor an observed negative is available, two scores at or above
0.5 are flagged for review. Opposite sides of the threshold are reported
as disagreement. Agreement below a nearest-training similarity of 0.30
has a separate flag. The threshold is descriptive and the scores are
uncalibrated. Numeric outcomes such as inhalation LC50, dermal LD50 and
developmental effect doses remain in their source-specific units. This
prevents a single score from hiding tradeoffs between endpoints.

The oral export includes the frozen ICE experimental forest, the
CATMoS teacher forest, the trusted-assumption NPASS expansion and the
NICE assay-call model. Measured ICE targets and NPASS assumed labels
retain separate fields. The augmented forest leaves scores blank for
structures used as NPASS additions because there is no held-out
prediction for them. NICE assay results are reused only for compounds
with saved held-out predictions. Exact ICE results retain the range and
report-level bins, including disagreements masked by a median.

Plant evidence includes selected previously reviewed studies, retained
high-inhibition Parthenium dose points and ECOTOX review leads. Each
keeps its experimental context. ECOTOX entries retain their
tested-form and identity review status. The screen keeps known
hazard concerns for cyanogenic dhurrin and industrial plasticizer
DEHP alongside the model results.

## What changed for the original selection

Eleven of the 116 original compounds have a recorded positive outcome
in at least one modeled binary assay. Examples include bacterial
mutagenicity for quercetin and juglone, EpiDerm skin irritation for
eugenol, and human repeat-patch sensitization for coumarin. These are
outcomes of the stated assays. The two structure forests also flagged
at least one unmeasured endpoint for 114 original compounds, most often
rabbit eye irritation or human skin sensitization. Agreement at the
0.5 threshold is too common to use as an exclusion rule on its own.

Five original entries have trusted-assumption NPASS oral labels. On the
other 111, the augmented forest changed the original ICE prediction for
23 compounds. Eleven original compounds have NICE assay-assisted
held-out oral predictions, which changed three ICE class calls.

## Plant-active follow-up

The follow-up table includes 15 structures. Seven have reviewed
individual-compound plant studies, three have high-inhibition Parthenium
dose points and five have ECOTOX-only review leads. Some ECOTOX leads
involve formulations or compounds with unresolved natural origin and
need source review before any candidate inference.

| Compound | Existing plant and oral evidence | What the wider screen adds |
| --- | --- | --- |
| (R)-(+)-Limonene | Wild oat germination inhibition and a measured ICE rat oral LD50 of 4,400 mg/kg. | Both forests flag EpiDerm skin irritation. Existing EPA irritation and dermal sensitization evidence carries more weight than the exploratory skin and eye predictions. [Existing evidence](limonene-evidence.md). |
| Azelaic acid | Arabidopsis primary-root IC50 of 44 µM. The rat oral evidence is provisional and no exact ICE point is available. | Both forests flag repeat-patch sensitization and rabbit eye irritation. Their respective score pairs are 0.69/0.59 and 0.78/0.53. These are follow-up signals. [Existing evidence](reviewed-selection-results.md#plant-and-rat-toxicity-evidence). |
| Scopoletin | Species-dependent root inhibition. The 3,800 mg/kg ICE point has unresolved study lineage. | Both forests flag bacterial mutagenicity (0.81/0.55) with maximum training similarity 0.46. The screen has no measured bacterial result for this structure. [Existing evidence](parthenium-evidence.md#follow-up-results). |
| Phloroglucinol | Laboratory seedling growth inhibition and one ICE rat oral point of 4,000 mg/kg. | Eye irritation and repeat-patch sensitization agreement both have nearest-training similarity below 0.30. The estimates carry substantial extrapolation uncertainty. [Existing evidence](reviewed-selection-results.md#plant-and-rat-toxicity-evidence). |

The resulting follow-up list identifies measurements worth checking.
Field selectivity and human exposure risk remain unresolved.

## Reproduction and outputs

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/natural_rescreen.py `
  --root $run --nice data_imports/NICE --review analysis/resources/natural_rescreen_evidence.csv `
  --output "$run/natural-rescreen-v1"
```

- `reviewed_natural_products.csv` gives the 116 original entries and their evidence summaries.
- `compound_summary.csv` gives one row per distinct screened structure.
- `endpoint_screen.csv` and `oral_scores.csv` retain the individual model scores and evaluation modes.
- `plant_evidence_followup.csv` and `plant_and_other_evidence.csv` give the follow-up subset and source-level records.
- `identity_holds.csv`, `endpoint_metrics.csv` and `manifest.json` retain the holds, model benchmarks and file fingerprints.
