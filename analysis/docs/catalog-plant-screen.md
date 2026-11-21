# Plant response scores for the toxicity catalog

## NPASS and NICE label review

The NPASS 3.0 activities, targets, and species tables were joined by native ID
and taxon. The scan covered 1,048,756 activity rows and found 3,685 in the
plant-linked channels. These comprise 469 plant-protein records, 546 plant
tissue or other records, and 2,670 unresolved organism records. The latter
include reported percentages and potency values from phytotoxicity studies.
The source table exports the organism, a broad activity type, a value, a
unit, and a reference. A row may lack the tested dose, duration, named
growth or germination endpoint, or whether its percentage is inhibition or
growth relative to control. Trusting the supplied measurement preserves its
value and still leaves those fields unresolved. For example, the NPASS
guaianolide lead for garden cress uses a 96-hour assay. The existing cress
models use a 120-hour assay. The Kava lead also appears in the earlier ChEMBL
plant evidence expansion. No direct NPASS label was added in this run.
[NPASS downloads](https://bidd.group/NPASS/downloadnpass.html) · [Guaianolide study](https://bibrepo.uca.es/articuloscientificos/31849593.pdf) · [Earlier plant evidence expansion](plant-evidence-experiments-2026-11-17.md)

The local NICE inventory covers animal and cell-based toxicity, exposure,
chemical use, taxonomy, and cHTS assays. The cHTS assay-annotation workbook
yielded no plant-growth, radicle, seedling, germination, or phytotoxicity
terms. No NICE measurement qualified as a plant-growth label. [NICE datasets](https://ice.ntp.niehs.nih.gov/DATASETDESCRIPTION)

## Models and outputs

The same toxicity catalog keys were passed to the radish and garden cress
forest regressions for germination and root length at 1, 10, and 100 µM,
all at 120 hours. These are exploratory percent-inhibition estimates for
12 specific conditions. The run scores 768,439 structures in all 12
conditions for 9,221,268 model estimates. The 324 training observations come from the same
27-compound primary study as the earlier model. The source tables were
recovered from archived article XML. PubChem structures reproduce their
recorded full InChIKeys and remain provisional mappings to the study samples.
The recovered training export preserves table identifiers, source cells,
and derived inhibition percentages. [Primary assay study](https://pmc.ncbi.nlm.nih.gov/articles/PMC3382788/)

`plant_scores.parquet` joins to the toxicity catalog on `full_key`. Exact
training matches include the observed response and use the scaffold-group
held-out prediction. Other rows use the full fit. Each panel has a count
of descriptors outside the training range. All 27 study structures match
the catalog by full InChIKey. The range check flags 550,933 catalog structures
across all four panels, which use the same training chemistry. The count only detects
extrapolation beyond individual descriptor ranges. It does not quantify
distance within the ranges or validate activity for unfamiliar scaffolds.

The pooled forest also scored all 768,439 catalog structures after restoration
of the original `plant-v5` training table. The table matches the supplied
release fingerprint and contains 733 observations across 211 structures.
The `pooled_high_response_score` column has chemical-group-held-out scores for
98 exact training matches and full-fit scores for 768,341 other structures.
The `pooled_outside_descriptor_ranges` column flags 252,958 structures with at
least one descriptor beyond the pooled training range. The score is an
uncalibrated estimate of the high-response class across historical assays with
different species, doses, and durations. [Pooled model release](candidate-audit-2026-11-17.md)

## Reproduction

The tracked table XML and PubChem structures are in
`analysis/resources/joint-reproduction/`. The full catalog workflow also
runs this step through the [rebuild driver](joint-catalog-notebook.md).

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/plant_catalog_screen.py `
  --catalog "$run/catalog-bulk-public-v1/catalog_scores.parquet" `
  --xml analysis/resources/joint-reproduction/de-martino-2012-tables.xml `
  --compounds analysis/resources/joint-reproduction/flavonoid-pubchem.json `
  --pooled data_imports/plant-v5/plant_training_observations.csv `
  --output "$run/catalog-plant-activity-v3"
```
