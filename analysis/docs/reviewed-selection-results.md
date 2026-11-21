# Original compound panel rerun

The supplied `data_imports/structural_features.parquet` contains 176 distinct
compound IDs across 116 natural-product and 60 herbicide rows. This reconciles
the historical counts with the project objective's reference to 120. The
SHA-256 is `46d3035986b86955403bf3f235255bb818cc1f0dc00cf028d55066de6fd8ce46`.
Origin and herbicidal activity labels are empty. The group names describe
membership in the recovered selection.

Both forests scored 174 rows. Glufosinate-ammonium and MSMA remain visible
as multicomponent holds. The separate glufosinate row has a valid structure
and scores. The counts below are in low / medium / high order using the
project's rat oral LD50 cutoffs of 1,080 and 3,400 mg/kg.

| Selection | Scored / supplied | ICE forest A | CATMoS forest B | Measured ICE medians | CATMoS teacher targets |
| --- | ---: | ---: | ---: | ---: | ---: |
| Natural products | 116 / 116 | 33 / 29 / 54 | 42 / 58 / 16 | 6 / 6 / 6 | 9 / 24 / 2 |
| Herbicides | 58 / 60 | 19 / 18 / 21 | 37 / 17 / 4 | 9 / 12 / 7 | 13 / 16 / 0 |

A uses group-held-out scores for 18 natural-product and 28 herbicide rows.
B uses group-held-out scores for 35 and 29. The remaining scores are
exploratory full-fit predictions outside the respective target cohort.
The forests agreed on 62 of 116 natural-product rows and 22 of 58 herbicide
rows. Sixteen natural-product rows scored high in both models. Fifteen had
no measured ICE median. The remaining row is DEHP, an industrial plasticizer
with unresolved natural origin and an EPA risk evaluation. Dhurrin also scored
high in both forests and is excluded from the shortlist because it is cyanogenic.
[EPA DEHP evaluation](https://www.epa.gov/assessing-and-managing-chemicals-under-tsca/risk-evaluation-di-ethylhexyl-phthalate-12-benzene)
and [primary dhurrin study](https://pmc.ncbi.nlm.nih.gov/articles/PMC166516/).

Among valid structures, 37 of 58 herbicides and 1 of 116 natural-product
entries contain F, Cl, Br or I. Median molecular weights are 279.1 and
174.7 Da, and median polar surface areas are 62.73 and 49.55 Å².
These are descriptive differences between the selections. No original panel
structure joined to the 14 qualified ECOTOX point responses in this run.
The recovered file and the available high-specificity plant observations
leave a three-way comparison with an evidence-defined benign group unresolved.

## Plant and rat toxicity evidence

| Entry | Plant and origin evidence | Rat oral evidence |
| --- | --- | --- |
| Azelaic acid | Detected in *Arabidopsis* in an immunity study. A separate laboratory study estimated a 44 µM primary-root IC50 in *Arabidopsis* and reported experimental and modeling evidence for interference with auxin signaling. [Occurrence study](https://pubmed.ncbi.nlm.nih.gov/19342588/) and [root study](https://doi.org/10.1016/j.plaphy.2024.108592). | Both forests predict high. No exact ICE median. A two-animal study reported LD50 above 5,000 mg/kg. A separate study reported a minimum lethal dose of 5,000 mg/kg in male rats. The high-bin inference remains provisional. [Australian assessment](https://www.industrialchemicals.gov.au/sites/default/files/2021-09/EVA00010%20-%20Evaluation%20Statement%20-%2014%20September%202021%20%5B702%20KB%5D.pdf). |
| Phloroglucinol | Primary enzyme work supports microbial biosynthesis. The compound reduced wild-type *Arabidopsis* seedling growth as concentration increased in liquid culture. [Biosynthesis](https://doi.org/10.1021/ja042340g) and [plant experiment](https://pmc.ncbi.nlm.nih.gov/articles/PMC5141504/). | One ICE point at 4,000 mg/kg (`acute_oral_766`) with unresolved original study lineage. Forest A predicts high and B predicts low. |
| p-Cymene | Detected in *Thymus proximus* oil. The individual compound had root IC50s of 3.89 mg/mL in *Poa annua* and 4.52 mg/mL in *Amaranthus retroflexus*. [Plant study](https://doi.org/10.3389/fpls.2021.689875). | ICE has 4,750 mg/kg (`acute_oral_12067`). EPA also summarizes a 3,200 mg/kg study. The estimates cross the medium/high boundary. [EPA characterization](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P101HFM4.txt). |
| Scopoletin | Primary studies support plant biosynthesis and species-dependent root effects. | The sole ICE point of 3,800 mg/kg has unresolved lineage and a separate 2,000 mg/kg lower bound leaves the high cutoff unresolved. [Source review](parthenium-evidence.md#follow-up-results). |
| Propionic acid and α-pinene | The file provides selection membership and structures. | Propionic acid's exact ICE points of 2,600 and 4,300 mg/kg cross the medium/high boundary. The α-pinene ICE value of 3,700 mg/kg has unspecified stereochemistry. An Australian assessment reports a lower rat oral interval for a commercial α-pinene test substance, so the source and form need review. [Australian assessment](https://www.industrialchemicals.gov.au/sites/default/files/Alpha-pinene_Human%20health%20tier%20II%20assessment.pdf). |

Separately, [(R)-(+)-limonene](limonene-evidence.md) has enantiomer-specific
plant inhibition evidence and an exact measured high-bin ICE value. The
lab and animal evidence leaves field selectivity and human risk unresolved.

## Analogue screen

Five matches per natural-product query give 580 pairs in each ranking.
Thirteen pairs from six queries meet Morgan Tanimoto ≥0.60 in the high-median
pool. Ten pairs from five queries meet that threshold when all eligible exact
ICE reports must be high. Azelaic acid's leading matches are sebacic acid and
pimelic acid. Each scores 1.000 because this radius-2 bit fingerprint gives
the same local features for the chain homologues. Their full structures
differ. One provisional ICE point supports each match at 14,375 and
7,000 mg/kg respectively. Their origin and plant-growth evidence remain
under review.

## Reproduction and local outputs

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/public_panel.py `
  --release "$run/public-cohorts-v2" --models "$run/public-models-v2" `
  --hrac "$run/raw/hrac-2026.xlsx" --literature analysis/resources/annona_primary_review_2026-11-18.csv `
  --extra-literature "$run/parthenium-review-v2/panel.csv" `
  --extra-literature analysis/resources/limonene_primary_review_2026-11-18.csv `
  --selection data_imports/structural_features.parquet --output "$run/public-panel-reviewed-v1"
uv run --project analysis --locked python -X utf8 analysis/import_screen.py `
  --root $run --panel "$run/public-panel-reviewed-v1" `
  --toxval-extra "$run/toxval-more" --output "$run/integrated-reviewed-v1"
```

`public-panel-reviewed-v1/panel.csv` includes the reviewed rows, public HRAC
benchmark and literature rows. `integrated-reviewed-v1/` retains both
rankings and their dose support. `reviewed-selection-exports/` contains
the scores and analogue pairs filtered to the original selection.
