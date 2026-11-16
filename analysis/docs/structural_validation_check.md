# Structural validation and plant-assay checkpoint

Checked **2026-10-28**, using acquisition code at `4725d51`, stress diagnostics
at `e65e1c2`, and end-to-end screening coverage at `af9b84d`. This records an
exploratory run, not a model acceptance decision. All products remain ignored
under `analysis/outputs/`; the original selection and source caches are unchanged.

## Common-cohort selection diagnostics

All four representations use the same 171 formula-eligible structures from the
176-compound cached selection: 55 selected herbicides and 116 natural products.
Canonical structure ordering reproduces the prior baseline metrics. The shared
cohort is necessary because the earlier Morgan/descriptor results included three
charged structures that the formula model excluded.

Balanced accuracy, in percent:

| Representation | Five folds | Three folds | Ten folds | Largest scaffold omitted, five folds |
|---|---:|---:|---:|---:|
| Formula | 91.9 | 89.3 | 92.3 | 90.3 |
| Descriptors | 72.4 | 69.2 | 71.9 | 74.1 |
| Morgan | 76.4 | 80.0 | 78.2 | 71.6 |
| Combined | 85.5 | 86.8 | 85.5 | 77.0 |

The omitted benzene scaffold (`c1ccccc1`) contains 49 compounds, leaving 122.
This changes the population being evaluated; it does not test generalization
onto benzene compounds. Fold-count sensitivity also changes training sizes.

Twenty shuffled-label controls per representation retain class counts and refit
every learned transform. All 80 controls evaluated successfully. Balanced accuracy:

| Representation | Mean | Minimum | Maximum |
|---|---:|---:|---:|
| Formula | 49.6% | 37.4% | 60.3% |
| Descriptors | 49.2% | 39.1% | 58.5% |
| Morgan | 49.8% | 43.5% | 59.1% |
| Combined | 50.2% | 44.4% | 57.6% |

These controls are consistent with useful **selection-membership** signal rather
than a classifier that always scores well on arbitrary labels. They do not
establish herbicidal activity, remove curation bias, or provide external validation.
No representation or seed was selected from the sensitivity runs.

Reproduce from the root, choosing fresh output directories on subsequent runs:

```bash
analysis/.venv/bin/python analysis/screen.py --compounds analysis/data/compound_traits.parquet --output analysis/outputs/structure-2026-10-28-stress-baseline
analysis/.venv/bin/python analysis/stress.py --features analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet --output analysis/outputs/stress-2026-10-28 --permutations 20
```

`stress_models.csv` contains all 96 diagnostic rows. Both directories include
manifests with verified input, source, dependency-lock and output hashes.

## Retrieved plant-assay evidence

The new pipeline adapter retrieved 14 explicit assays from **ChEMBL_37**, each
from a separate source publication. Thirteen concern *Amaranthus retroflexus*;
one concerns *Amaranthus blitum* subsp. *oleraceus*. Discovery used a bounded
100-result catalog query for `description__icontains=herbicidal` and
`assay_organism=Amaranthus retroflexus` (144 total matches reported). Selection
took one lead per distinct publication, plus the independently checked
`CHEMBL3079324` lead. This is a purposive acquisition, not a complete assay census.

| Assay | Activity records | Valid structure IDs | Scaffold groups |
|---|---:|---:|---:|
| CHEMBL3047330 | 9 | 9 | 3 |
| CHEMBL3047983 | 5 | 5 | 3 |
| CHEMBL3048455 | 8 | 8 | 5 |
| CHEMBL3049732 | 2 | 2 | 2 |
| CHEMBL3050086 | 4 | 4 | 3 |
| CHEMBL3050227 | 8 | 8 | 1 |
| CHEMBL3050362 | 58 | 58 | 2 |
| CHEMBL3050580 | 1 | 1 | 1 |
| CHEMBL3051568 | 3 | 3 | 1 |
| CHEMBL3053086 | 4 | 4 | 2 |
| CHEMBL3066645 | 24 | 24 | 6 |
| CHEMBL3066743 | 2 | 2 | 2 |
| CHEMBL3079324 | 4 | 4 | 1 |
| CHEMBL970505 | 25 | 25 | 3 |

The 157 activity records cover **154 unique canonical structures and 28 scaffold
groups**; five structures overlap the existing selection, leaving **149 additional
structures**. All 154 parse successfully in RDKit. Raw assay/document records,
activity pages, database version, request parameters and retrieval times are in
`analysis/outputs/chembl-2026-10-28/raw/chembl/`. Its acquisition manifest hashes
raw inputs and derived review exports. `activity_review.csv` retains measured
values, relations, units, comments, publication DOI and source-snapshot hashes;
`candidates.csv` contains deduplicated structure IDs/SMILES without activity labels.
The original raw bundles preserve additional fields beyond that review view.

Data quality requires review: 109 records have exact-value relations, 45 have
inequalities and three have no numeric relation/value. Two measurements use mm
rather than percent. One record explicitly says "Not Determined". Source dose,
application timing, species and endpoint descriptions vary; dose transcription
and publication methods still require checking. Null validity comments do not
establish assay comparability. For example, the largest assay has 58 compounds
but only two scaffold groups. More rows alone do not support independent folds.

Acquisition used `max_activities=500` and `page_size=100`, with failures surfaced
rather than converted to empty data. A second live retrieval of `CHEMBL970505`
with `page_size=7` returned 25 identical activity records over four pages.

```bash
pipeline/.venv/bin/python pipeline/examples/fetch_chembl_assay.py CHEMBL970505 --data analysis/outputs/chembl-pagination-check-2026-10-28 --page-size 7 --max-activities 100
analysis/.venv/bin/python analysis/screen.py --compounds analysis/data/compound_traits.parquet --candidates analysis/outputs/chembl-2026-10-28/candidates.csv --output analysis/outputs/chembl-screen-2026-10-28
```

The candidate run exports all 154 structures. Its 616 candidate/representation
rows retain `activity_model_unavailable` with null probabilities. No occurrence,
selection membership or unreviewed assay outcome was inserted into the production
`activity_target` or `origin_target` fields.

## Source-reported response-band pilot

[ChEMBL assay CHEMBL3066645](https://www.ebi.ac.uk/chembl/explore/assay/CHEMBL3066645)
reports greenhouse post-emergence growth inhibition in *A. retroflexus*,
150 g active ingredient/ha, measured after 15 days. Its source is
[the phthalazinone study](https://doi.org/10.1021/jf061976j).
The 24 records already use two reported bins: 14 are `>80%` and ten are `<50%`.
An exploratory target reproduced those source bins directly, without converting
them into reviewed general herbicidal-activity labels or pooling other assays.

Only two scaffold groups contain the low-response class. Five- and three-fold
evaluation therefore return `insufficient_scaffold_support` for all four models.
A deliberately separate two-fold diagnostic can evaluate; balanced accuracy is
50.0% formula, 44.3% descriptors, 37.1% Morgan and 42.9% combined. This tiny,
imbalanced scaffold sample supplies no evidence of useful predictive performance.
It is not candidate-screening approval and does not relax production validation.
The reports and source context are saved in `reported_response_diagnostics.json`.

The exact exploratory target can be reproduced from this frozen assay bundle:

```python
activities = [a for p in bundle["activity_pages"] for a in p["activities"]]
rows = prepare([{"compound_id": a["molecule_chembl_id"],
                 "smiles": a["canonical_smiles"]} for a in activities])
for row, activity in zip(rows, activities, strict = True):
    assert activity["standard_type"] == "GI" and activity["standard_units"] == "%"
    band = (activity["standard_relation"], activity["standard_value"])
    assert band in {(">", "80.0"), ("<", "50.0")}
    row["reported_response_band"] = int(band == (">", "80.0"))
reports = [evaluate(rows, "reported_response_band", representation, folds = folds)["report"]
           for folds in (5, 3, 2) for representation in REPRESENTATIONS]
```

Here `prepare` comes from `screen`, and `evaluate`/`REPRESENTATIONS` from
`structure_models`; the `bundle` is the saved `CHEMBL3066645.json` object.
These labels are confined to the diagnostic and are not a reviewed-label file.

## Verification and remaining work

- ChEMBL acquisition checks: 37 passed, using injected synthetic HTTP responses.
- Stress diagnostics: 10 passed, including common cohorts, deterministic controls,
  failed-support retention and immutable source exports.
- Screening checks: eight passed, including RDKit-derived features and fully
  synthetic reviewed outcomes through exported candidate predictions.
- Full analysis suite: 87 passed. Full pipeline suite: 1,043 passed.
- Both Ruff checks and `git diff --check` pass. Live pagination records and
  acquisition/screening/stress manifest hashes were verified.

The next useful scientific step is publication-level review of comparable assays
and explicit response thresholds, retaining tested low-response compounds and
ambiguous outcomes separately. Additional independent negative-bearing scaffolds
are especially needed. Natural-origin evidence is still independent and absent.
The new raw data is a curation starting point, not a validated activity model.

## Frozen review rebuild — 2026-10-29

The tracked `review_assays.py` command replaces the scratch-script dependency
for review/candidate preparation. It rebuilt all 14 frozen snapshots into
`analysis/outputs/chembl-review-2026-10-29-final/`, preserving all 157 activity
IDs and every field in the earlier review export. The 154 source molecule IDs
and their structures match the earlier candidate list exactly. Source hashes
are unchanged; every new manifest input/code/lock/product hash was verified.
The expanded review view includes complete raw activity JSON and generates a
full unknown-label worksheet without inferring activity or natural origin.

```bash
analysis/.venv/bin/python analysis/review_assays.py --snapshots analysis/outputs/chembl-2026-10-28 --output analysis/outputs/chembl-review-2026-10-29-final
analysis/.venv/bin/python analysis/screen.py --compounds analysis/outputs/chembl-review-2026-10-29-final/candidates.csv --labels analysis/outputs/chembl-review-2026-10-29-final/label_review_template.csv --output analysis/outputs/chembl-review-screen-2026-10-29-final
```

The worksheet roundtrip retains all 154 compounds, null activity/origin targets
and explicit unsupported-model reports. No model was trained on unreviewed
outcomes. Verification: 30 focused review-export tests, 117 analysis tests,
1,043 pipeline tests and both Ruff checks pass. Cached rebuild and worksheet
consumption use no network access and do not change the original review products.
