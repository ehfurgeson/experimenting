# Joint plant activity and toxicity catalog screen

The exact InChIKey join covers **768,439 structures**. It carries the original
plant scores, rat oral LD50 results, and all 12 additional toxicity endpoints.
The exploratory high-response rule uses a pooled plant score of at least 0.50.
The high measured oral group uses the project ICE bin above 3,400 mg/kg. The
oral model overlap requires a high-class score of at least 0.50 from each of
the named classifiers and an absent exact ICE oral aggregate. Scores are
uncalibrated. The ICE and augmented models share training data.

| Result | Structures |
| --- | ---: |
| High measured ICE rat oral LD50 after record-level review | 415 |
| High measured oral LD50 and pooled plant score at least 0.50 | 166 |
| High scores for plant and both primary oral classifiers without a measured ICE aggregate | 12,352 |
| High scores for plant and all three oral classifiers without a measured ICE aggregate | 11,557 |
| At least 40% predicted radish or cress root inhibition at 100 µM and high measured oral LD50 | 0 |
| At least 40% predicted radish or cress root inhibition at 100 µM and high scores on all three oral classifiers without a measured ICE aggregate | 0 |

Of the 415 high ICE aggregates, 41 have at least one eligible exact oral report
at or below the cutoff. The per-compound export retains the report minimum,
maximum, count, and number at or below the cutoff. These are provider-reported
values. This release counts butyl stearate separately as a reviewed lower bound
above 32,000 mg/kg. The original `catalog-joint-screen-v1` counted that report
as exact, yielding 416 high aggregates and 167 overlaps. The input cohort and
previous model scores remain frozen for comparability. [Source audit](candidate-audit-2026-11-17.md#illustrative-shortlist) · [HSDB summary in PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/31278)

## Selected compounds with observed plant responses

- **(R)-(+)-Limonene.** ICE reports 4,400 mg/kg. The published stereospecific
  assay showed strong inhibition of *Avena ludoviciana* germination. The pooled
  plant score is 0.30. EPA reports irritation and dermal sensitization concerns.
  The previous catalog project review retains its tested form, plant conditions,
  and toxicity lineage. [Plant study](https://www.nature.com/articles/s41598-025-25935-z) · [Project evidence review](limonene-evidence.md)
- **7-Methylcoumarin.** ICE reports 3,800 mg/kg and the pooled plant score is
  0.87. A targeted source check found wheat root lengths of 17 mm versus 68 mm
  in control at 10 ppm, which gives 75% inhibition from Table 2. The paper
  used synthesized test material and some narrative statements disagree with
  its dose rows. Natural occurrence and crop selectivity are unresolved. Five
  additional binary assays flag model signals without cohort measurements.
  The human maximization cohort has a negative recorded result for its own
  protocol. [Primary study, Tables 1 and 2](https://medcraveonline.com/HIJ/HIJ-02-00021.pdf)
- **Dibutyl phthalate.** The ICE aggregate is 7,499 mg/kg. A primary study
  reported more than 70% seed germination inhibition in *Leptochloa chinensis*
  at 500 mg/L and effects on rice under some conditions. EPA's final evaluation
  found robust developmental-toxicity evidence. This is a documented hazard
  example despite the high acute oral LD50. [Plant study](https://doi.org/10.1071/CP13339) · [EPA final evaluation](https://www.epa.gov/assessing-and-managing-chemicals-under-tsca/risk-evaluation-dibutyl-phthalate-12-benzene)

The training-table quantitative matches were dibutyl phthalate and triforine.
Triforine's source concerns apple **pollen** germination. The raw source match
is retained in `quantitative_plant_evidence.csv`. The extra literature example
for 7-methylcoumarin is documented above and did not change the model or the
training-table count. [Apple pollen study](https://doi.org/10.1080/00221589.1977.11514772)

## Additional toxicity endpoints

Of the 166 measured-oral and pooled-plant matches, 14 had at least one
observed positive binary endpoint and 165 had an observed positive or an
unmeasured binary endpoint score at or above 0.50. The one with no binary
flags had zero measured outcomes across the seven binary endpoints. Of the
11,557 model-screen overlaps, 10,360 had one or more binary flags. A recorded
assay outcome takes precedence for that assay. Five continuous endpoints
retain their original scales and are interpreted individually. The counts
describe screening results. They leave human risk and field selectivity
unresolved. [Endpoint definitions and evaluation](other-toxicity-endpoints.md)

## Outputs and reproduction

- `joint_scores.parquet` contains all matched structures and every endpoint.
- `measured_high_oral.csv` includes the 415 high-oral structures, ICE ranges,
  and the flag `pooled_plant_score_ge_half` for the 166 overlaps.
- `model_only_overlap.parquet` contains 11,557 joint model-score overlaps.
- `quantitative_plant_evidence.csv` gives high-response records from the
  original plant training cohort. `reviewed_plant_evidence.csv` gives prior
  literature and ECOTOX review records, including tested-form holds.
- `endpoint_coverage.csv` contains score and observation counts by endpoint.

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/joint_catalog_screen.py `
  --root $run --training data_imports/plant-v5/plant_training_observations.csv `
  --output "$run/catalog-joint-screen-v2"
```
