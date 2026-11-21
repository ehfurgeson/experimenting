# Joint catalog review notebook

Run from the repository root with the locked analysis environment.

```powershell
uv run --project analysis --locked marimo run analysis/joint_catalog_notebook.py
```

The live notebook has a plant-score cutoff control, a measured-compound search,
validation tabs, and model selectors for logistic coefficients and forest feature
importance. The HTML export shows the default view. The Python notebook runs
the controls using the local input files.

## Rebuild the data and diagnostics

From a fresh checkout, place the supplied data in `data_imports/`. The driver
uses the following source files.

- `NICE/acute_oral.xlsx`, `acute_inhalation.xlsx`, `cancer.xlsx`, `dart.xlsx`,
  `endocrine.xlsx`, `eye_irritation.xlsx`, `skin_irritation.xlsx`, and
  `skin_sensitization.xlsx`.
- `NPASS/NPASS3.0_naturalproducts_structure.txt` and `NPASS/NPASS3.0_toxicity.txt`.
- `plant-v5/plant_training_observations.csv` and `plant-v5/manifest.json`.

The driver downloads checksum-pinned OPERA, COCONUT and both LOTUS releases.
Use `--public-cache <previous-run>` to reuse a complete public download cache
with the same layout and hashes. The repository tracks compact exports for the
assay-specific plant tables, exact structure mappings, dermal observations, and
reviewed context. Older notebook and panel analyses may use separate historical
research archives. [Tracked inputs](../resources/joint-reproduction/README.md)

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/rebuild_joint_catalog.py --root $run
uv run --project analysis --locked marimo export html analysis/joint_catalog_notebook.py `
  --no-include-code -o "$run/joint_catalog_review.html"
```

Use a fresh `--root` for independent rebuilds. Finished stages are verified
if the command is run again. Set `AGROTOX_JOINT_ROOT` to the output root when
using a nondefault directory. The catalog feature inventories and scoring
stages require several minutes and can run longer on slower hardware. The
historical source and processing choices remain in the individual guides.
[Toxicity catalog](catalog-bulk-screen.md) · [Plant catalog](catalog-plant-screen.md) · [Joint screen](joint-catalog-screen.md)

## Diagnostic details

- **Validation.** The notebook uses existing grouped toxicity results. The
  diagnostic run reproduces the pooled plant splits and fixed assay-specific
  forest splits. It reports the actual regressor errors and the median baseline
  errors. Assay-band F1 is secondary and omitted for panels with zero high labels.
- **Logistic coefficients.** Oral weights come from the saved standardized
  A and B benchmark fits. Plant weights come from the reconstructed standardized
  logistic benchmark. The export retains the raw fold values. These models
  serve as comparisons to the screening forests.
- **Out-of-bag permutation.** The diagnostic refits all 20 screening forests
  with their original task, features and training settings. Within each tree's
  unsampled rows, it shuffles one descriptor, the dose, or the whole Morgan
  fingerprint block. It aggregates the changed votes and reports the mean
  macro-F1 decrease for classifications or mean MAE increase for regressions
  over three shuffles. Rows without any unsampled votes are omitted and the
  coverage count is displayed. The shuffle SD describes variation across
  the three shuffles. Chemical-group and publication holdouts are the separate
  validation results shown in the notebook.

The generated CSVs and manifest live in `catalog-joint-diagnostics-v2`.
The full joined Parquet is read lazily for the cutoff control. All artifact inputs
stay local.
