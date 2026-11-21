# Screening toxicity endpoints beyond rat oral LD50

The endpoint models retain each provider's reported assay, species, route,
duration and units where applicable. They use supplied measurements and calls
without individual study verification. Binary cohorts use explicit
positive and negative source calls. Opposite calls for the same full
structure remain in the conflict export. Numeric cohorts use the median of
distinct exact results on the log10 scale. The endpoint-specific filters and
source locators are available in the workflow and observation export.

For rat inhalation the target is an exact 4-hour LC50 in mg/L. Rat dermal
LD50 uses EPA ToxValDB because the local NICE acute dermal workbook labels
all 895 LD50 records as mixtures. The ToxValDB dermal pilot includes 451
qualified records. The provider explicitly marks 108 as experimental and
leaves experimental status undetermined for 343, which this run admits
under the trusted-source assumption. No gas, vapor or aerosol category is
inferred. Mouse LLNA EC3 estimates sensitization potency among the records
with an exact point. The fetal malformation LOEL cohorts use oral critical
effect values in mg/kg/day, separately for rats and rabbits. They concern
reported effect doses and do not label compounds without such a result.
The DART workbook does not provide a mixture flag. Its pilot requires a
provider substance identifier and a valid single-component structure.

For rabbit eye irritation, the target is GHS Category 1 or 2 versus the
record's unclassified outcome in the Draize dataset. The skin irritation
target is an EpiDerm assay call. The human maximization and repeat patch
tests are modeled as distinct sensitization protocols. Bacterial
mutagenicity uses unambiguous positive or negative calls. The NTP rat
feed bioassay uses some or clear evidence versus no evidence. A structure
with discordant binary results stays out of the target cohort. The
rat oral Hershberger model predicts its reported antagonist assay call.
The in vitro AR agonist endpoint had 104 usable structures but only 14
positive labels and was excluded from the grouped model screen.

## Scaffold-held-out results

Each model was tested in five folds that group both connectivity and
scaffold. The two forests use seven structure descriptors, with one adding
a radius-2 Morgan fingerprint. Both are compared to a simple reference
that predicts the training-fold class prior or median. The stronger
observed forest for each endpoint is shown for readability. Per-profile
results remain in the metrics export. Selecting the higher observed score
here does not constitute independent model validation.

| Binary target | Structures | Forest | Macro-F1 | AUROC |
| --- | ---: | --- | ---: | ---: |
| Bacterial mutagenicity | 1,495 | Descriptors + Morgan | 0.716 | 0.742 |
| Human repeat patch sensitization | 237 | Descriptors + Morgan | 0.661 | 0.759 |
| Rabbit eye irritation | 134 | Descriptors | 0.646 | 0.748 |
| Rat feed carcinogenic activity | 109 | Descriptors + Morgan | 0.626 | 0.652 |
| Rat oral Hershberger antagonism | 110 | Descriptors + Morgan | 0.598 | 0.702 |
| EpiDerm skin irritation | 62 | Descriptors + Morgan | 0.597 | 0.810 |
| Human maximization sensitization | 854 | Descriptors + Morgan | 0.561 | 0.729 |

| Numeric target | Structures | Forest | Log10 MAE | Median-only MAE |
| --- | ---: | --- | ---: | ---: |
| Rat acute inhalation LC50, 4 hours | 591 | Descriptors | 0.840 | 0.907 |
| Rat acute dermal LD50 | 381 | Descriptors + Morgan | 0.616 | 0.645 |
| Mouse LLNA EC3 | 315 | Descriptors | 0.713 | 0.744 |
| Rat fetal malformation LOEL | 180 | Descriptors + Morgan | 0.589 | 0.588 |
| Rabbit fetal malformation LOEL | 89 | Descriptors + Morgan | 0.509 | 0.516 |

The LC50 and LD50 regressions have substantial uncertainty at the
individual-compound level. The fetal LOEL models showed little ranking
signal and performed close to their median-only baselines. The binary
scores are uncalibrated model scores
for their stated assay or evidence class. They do not establish human
exposure risk across routes or endpoints.

## Compound screens

The full export retains all 553 source rows across the original selection,
public HRAC list, and plant literature panels. Each of the 12 modeled
endpoints scores the 409 distinct valid structures. This gives 4,908
distinct compound–endpoint scores, including 2,088 for the 174 scorable
original selection entries. Rows with an endpoint target use
held-out results, while other rows use exploratory full-data fits. The
screen includes two forest scores, measured targets where applicable, and
the maximum fingerprint similarity to the model's training chemistry.
For example, azelaic acid scores 0.69 and 0.59 for the positive human
repeat patch call, with maximum training similarity 0.71. Both are
exploratory model estimates. The panel has only three original natural
products with measured holdout outcomes for that assay.

## Reproduction

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/nice_endpoint_models.py `
  --nice data_imports/NICE --release "$run/public-cohorts-v2" `
  --panel "$run/public-panel-reviewed-v1" --toxval "$run/toxval" `
  --toxval "$run/toxval-more" --output "$run/other-toxicity-endpoints-v2"
```

The run exports per-endpoint coverage, observations, derived targets,
held-out predictions and metrics. The full and reviewed-only panel screens
are included alongside the manifest.

The [catalog rebuild](joint-catalog-notebook.md) fits the same targets with
the tracked dermal observations and the NICE imports. It omits `--panel`
because catalog scoring uses the fitted endpoint cohorts and held-out
predictions directly. The commands above preserve the original raw-workbook
audit and named-panel outputs.
The [natural-product rescreen](natural-product-rescreen.md) extends the
same endpoint models to the previously toxicity-linked catalog structures
and adds the oral-model and plant-evidence overlays.
