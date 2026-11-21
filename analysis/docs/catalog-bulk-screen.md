# Toxicity screen of bulk natural-product catalogs

The screen uses the November 2026 COCONUT lite release, LOTUS v11 structure
metadata, the October 19, 2026 LOTUS Wikidata SMILES snapshot, and the local
NPASS 3.0 structure export. RDKit must parse each entry as a single-component
structure and reproduce the provider's full InChIKey. The union has one row per
full InChIKey. Source identifiers remain available for exact matches, and LOTUS
v11 occurrence, DOI and manual-validation counts are joined by full key.
Structures within a catalog can have multiple identifiers. The output retains
the first qualifying identifier per source. [COCONUT release](https://coconut.s3.uni-jena.de/prod/downloads/2026-11/coconut_csv_lite-11-2026.zip) · [LOTUS v11](https://zenodo.org/records/19360665) · [LOTUS Wikidata snapshot](https://zenodo.org/records/23478723)

## Coverage

| Catalog | Valid unique structures | Structures added to the running union |
| --- | ---: | ---: |
| COCONUT | 724,233 | 724,233 |
| LOTUS v11 and October snapshot combined | 227,400 | 36,374 |
| NPASS 3.0 | 189,549 | 7,832 |
| **Total** | | **768,439** |

The union covers 227,285 of the 227,319 distinct InChIKeys in the LOTUS v11
occurrence file. The remaining 34 keys have conflicting, missing, invalid or
multicomponent structures under the matching rules. Each structure in the
union has a score for each of the 12 additional endpoints, giving 9,221,268
compound–endpoint scores. Both primary oral classifiers scored every
structure. The NPASS-augmented oral classifier scored 767,871 and left scores
blank for 568 training structures with no saved out-of-fold score.

The catalog union has 1,632 exact matches to experimental ICE rat oral LD50
aggregates. Of these, 707 fall in the project's low LD50 bin. This count uses
measured ICE values.

## Models and interpretation

The screen applies the rat oral LD50 classifiers trained on ICE, CATMoS and
ICE plus the trusted-assumption NPASS labels, together with 12 additional
assay-specific endpoints. For each additional endpoint, the screen uses the
forest with the higher prior scaffold-held-out macro-F1 for binary outcomes
or the lower prior log10 mean absolute error for quantitative outcomes.
The scores for exact training structures use saved scaffold-held-out
predictions. Other structures use full-cohort fits. The augmented oral model
leaves scores blank for structures used in training without held-out scores.
Binary `score` columns are uncalibrated positive-class scores. Quantitative
values use the endpoint units in `endpoint_summary.csv`. The descriptor-range
fields count how many of seven descriptors fall outside the training minima
and maxima. This check leaves structural and biological extrapolation partly
unmeasured. [Additional endpoint methods and validation](other-toxicity-endpoints.md)

`ice_oral_ld50_mg_kg` is the ICE aggregate of exact experimental rat oral
results. The project's low LD50 bin is at or below 1,080 mg/kg. This screening
bin places a compound at higher acute oral concern within the project and can
hide disagreement between individual reports. CATMoS teacher bins, NPASS
assumed labels, and model scores have separate columns. This run uses only
structure-based models at catalog scale. Consult the existing reviewed panel
for assay-assisted oral results and compound-level plant evidence. Catalog
membership and these toxicity estimates leave human exposure risk and plant
growth inhibition unresolved. [Per-study ICE audit](catalog-hazard-review.md) · [Reviewed panel](natural-product-rescreen.md)

## Reproduction

Run from the repository root. The commands below retain the original staged
scoring method. The [catalog rebuild](joint-catalog-notebook.md) downloads the
same pinned public inputs and fits and scores the catalog directly. Each stage writes to a fresh
directory with a fingerprint manifest. The second scoring stage verifies
and reuses COCONUT scores, then evaluates the additional exact keys.

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/catalog_screen_inventory.py `
  --source coconut --path "$run/catalog/raw/coconut-lite" --output "$run/coconut-full-features-v1"
uv run --project analysis --locked python -X utf8 analysis/catalog_screen_inventory.py `
  --source lotus --path "$run/raw/lotus-v11-metadata.csv.gz" --output "$run/lotus-v11-features-v1"
uv run --project analysis --locked python -X utf8 analysis/catalog_screen_inventory.py `
  --source lotus-wikidata --path "$run/raw/lotus-wikidata-smiles-20261019.tar.gz" `
  --output "$run/lotus-october-features-v1"
uv run --project analysis --locked python -X utf8 analysis/catalog_screen_inventory.py `
  --source npass --path "$run/npass/npass_identity.csv.gz" --output "$run/npass-full-features-v1"
uv run --project analysis --locked python -X utf8 analysis/catalog_bulk_screen.py `
  --root $run --nice data_imports/NICE --coconut "$run/coconut-full-features-v1" `
  --lotus-triplets "$run/raw/lotus-v11.csv.gz" --output "$run/catalog-bulk-coconut-v1"
uv run --project analysis --locked python -X utf8 analysis/catalog_bulk_screen.py `
  --root $run --nice data_imports/NICE --coconut "$run/coconut-full-features-v1" `
  --lotus "$run/lotus-v11-features-v1" "$run/lotus-october-features-v1" `
  --lotus-triplets "$run/raw/lotus-v11.csv.gz" --npass-catalog "$run/npass-full-features-v1" `
  --existing "$run/catalog-bulk-coconut-v1" --output "$run/catalog-bulk-public-v1"
```

## Outputs

- `catalog_scores.parquet` contains structure identifiers, individual model scores,
  available cohort measurements and LOTUS occurrence counts.
- `measured_ice_catalog.csv` and `measured_low_ld50.csv` give the ICE matches
  and low-LD50 subset for review in a tabular viewer.
- `endpoint_summary.csv` and `oral_summary.csv` give model evaluation modes,
  coverage counts and the previous endpoint validation metrics.
- `lotus_core_unscored.csv` gives unmatched exact keys from the LOTUS v11 triplets
  and the structure hold reasons when available.
- `manifest.json` captures the input and output fingerprints. Each feature
  inventory has its own `identity_holds.csv` and manifest.
