# NPASS and NICE rat oral LD50 experiments

These two experiments reuse the five published ICE pathway A
scaffold/connectivity splits, the same low, medium and high rat oral
LD50 bins, and the same 200-tree forest. The CATMoS model remains a
separate teacher-model experiment. The paired intervals resample
chemical groups from fixed held-out predictions 2,000 times. They are
conditional on these fits and are exploratory.

## NPASS as a path to additional labels

The local NPASS export has 4,179 rat LD50 records. Of these, 1,716
records for 715 structures outside measured A had a valid identity,
positive finite convertible mass-per-body-mass dose, and a supported
point or censoring qualifier. By full InChIKey, normalized dose and
qualifier, 430 of those records across 162 structures linked to the
audited endpoint-eligible EPA ToxValDB records. The match is a provenance
lead. A ToxVal-derived NPASS value and its matched EPA row may come
from the same study and are counted once for training.

Of 69 structures with exact-value links from NPASS records that explicitly
cite ToxVal, 12 had eligible exact EPA points across more than one bin and
two had manual holds. Of the remaining 55, three named rat oral
results were checked against agency study summaries. Original study
material and independent replication are still incompletely documented.
The broader experiment uses one classification target per structure,
based on the median of distinct matched points. The three checked labels
use their reviewed point. An added structure is excluded from each fold
where its combined connectivity/scaffold group overlaps the held-out
set. Each fold used one to three checked or 30–52 total linked additions.

| Training profile | Held-out A | Macro-F1 | Low-LD50 recall |
| --- | ---: | ---: | ---: |
| Original structure-only | 4,234 | 0.431 | 52.2% |
| Plus three source-checked structures | 4,234 | 0.426 | 50.7% |
| Plus 55 source-linked structures in total | 4,234 | 0.422 | 52.7% |

Macro-F1 differences were −0.0045 (95% interval −0.0125 to +0.0027)
and −0.0085 (−0.0226 to +0.0041). The source-linked expansion did
not demonstrate improved performance on the fixed measured holdout.
The [source review ledger](../resources/npass_ld50_source_review.csv) includes
the three endpoint matches and exclusions for conflicting doses,
unclear stereochemistry and an unresolved study citation. For example,
the source paper confirmed isoferulic acid's rat oral endpoint, while
the matched database key leaves alkene geometry unspecified.
[Isoferulic acid primary study](https://www.jstage.jst.go.jp/article/yakushi1947/95/5/95_5_539/_pdf).

## NICE curated assay calls

The ICE 5.1 cHTS download adds no acute oral labels. The feature experiment
linked the archive to measured A by unambiguous DTXSID-to-full-InChIKey
mappings. It retained only unambiguous Active or Inactive calls after
excluding QC-Omit, Flag-Omit and identified technical interference.
Of the 1,945 structures with raw archive overlap, 1,423 had usable calls
under this filter. Among them are 11 original natural-product and 22
original herbicide entries, counting only the overlap verified in this
experiment. The pipeline retained 260,253 usable structure–assay pairs.
It does not infer inactivity from missing values or use AC50, concentration
or cytotoxicity-burst adjustment in this experiment.

Assay selection used only training-fold data, retaining 40–45 assays per
fold with coverage of at least 70% and at least ten active and ten
inactive results. The coverage-only control encodes whether a call passed
the filter. The assay-call model encodes inactive, missing and active as
0, 0.5 and 1. All three matched models train and test on the same
1,423 structures across the published splits.

| Matched profile | Macro-F1 | Low-LD50 recall |
| --- | ---: | ---: |
| Structure only | 0.454 | 50.0% |
| Structure and assay availability | 0.437 | 50.6% |
| Structure and assay calls | 0.464 | 58.2% |

Paired differences for assay calls versus structure only were +0.0098
macro-F1 (95% interval −0.0293 to +0.0369) and +8.2 percentage points in
low-LD50 recall (+0.9 to +12.3). The latter is 51 additional correct
low-bin calls among the 622 low-bin structures. High-bin recall fell
from 43.7% to 37.8% in the matched comparison.

A separate retrospective comparison used the assay model where usable
and the published structure-only predictions elsewhere in all 4,234
held-out cases. Macro-F1 moved from 0.431 to 0.444 (difference +0.0129,
95% interval −0.0056 to +0.0210) and low-LD50 recall from 52.2% to 53.9%
(+1.8 percentage points, conditional interval +0.04 to +3.81). These
results support further evaluation of assay calls where available. The
test reuses an existing measured cohort and does not establish transfer
to natural-product scaffolds with sparse assay coverage.

## Expansion under the trusted-source assumption

The broader NPASS run uses the provider's rat LD50 results without requiring
an EPA link or an original study report. Missing route, acute context and
experimental status are assumed compatible with measured ICE. An oral
benchmark still tests whether that assumption helps predict observed oral
outcomes. The run deduplicates equal value/qualifier pairs per structure and
uses the median on the log10 scale for exact doses. A bounds-only structure
contributes a class when its reported bounds identify one bin. The source
values and disagreements remain visible in the decision ledger.

Of the 715 structures considered, 361 supply exact targets and 207 supply
classification-only bounds. Another 107 have ambiguous or conflicting
bounds and 40 have structural conflicts or multiple components. Among the
361 exact targets, 28 span more than one bin before aggregation and 21
have bounds incompatible with the assigned bin. The broadest arm adds
314–540 structures in individual folds after group exclusion.

| Training on the fixed 4,234-structure ICE holdout | Macro-F1 | Low-LD50 recall | High-LD50 recall |
| --- | ---: | ---: | ---: |
| Original structure-only | 0.431 | 52.2% | 43.0% |
| Plus 361 NPASS exact targets | 0.422 | 54.4% | 38.0% |
| Plus 568 NPASS exact or single-bin targets | 0.422 | 54.3% | 38.3% |

With all 568 targets, the paired low-LD50 recall gain was 2.1 percentage
points (conditional 95% interval +0.6 to +4.6). The macro-F1 difference
was −0.0083 (−0.0189 to +0.0061). The broader labels helped low-bin recall
at the expense of high-bin recall in this holdout.

The NICE expansion added positive finite AC50 measurements for 33,152
quality-filtered active structure–assay pairs. It joined potency by the
same substance, assay and record ID as the active call. The added features
were negative log10 molar AC50 and whether that value was present. Binary
calls plus AC50 achieved **0.460 macro-F1 and 57.1% low-LD50 recall** on
the 1,423 matched structures. Calls alone gave **0.464 and 58.2%**. The
paired uncertainty intervals for the incremental effects both include zero.

The original provenance checks also addressed target comparability and
duplicate evidence. An LD50 can be experimental and still describe
injection, dermal exposure, or another protocol. A database can also
re-export a result already present in another source. Endpoint and form
checks affect what a model learns, and group-held-out evaluation reduces
the chance of overstating performance through shared chemistry.

The [separate toxicity endpoint models](other-toxicity-endpoints.md) use
the provider's reported measurements to screen the same compound panel
for endpoints beyond rat oral LD50.

## Reproduction

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/npass_label_model.py `
  --release "$run/public-cohorts-v2" --models "$run/public-models-v2" `
  --npass "$run/npass" --toxval "$run/toxval" --toxval "$run/toxval-more" `
  --review analysis/resources/npass_ld50_source_review.csv --output "$run/npass-label-model-v1"
uv run --project analysis --locked python -X utf8 analysis/nice_assay_model.py `
  --archive data_imports/NICE/cHTS_AllDownloadFiles.zip `
  --release "$run/public-cohorts-v2" --models "$run/public-models-v2" `
  --output "$run/nice-assay-model-v2"
uv run --project analysis --locked python -X utf8 analysis/npass_label_model.py `
  --release "$run/public-cohorts-v2" --models "$run/public-models-v2" `
  --npass "$run/npass" --trust-provider --output "$run/npass-label-trusted-v2"
uv run --project analysis --locked python -X utf8 analysis/nice_assay_model.py `
  --archive data_imports/NICE/cHTS_AllDownloadFiles.zip `
  --release "$run/public-cohorts-v2" --models "$run/public-models-v2" `
  --include-potency --output "$run/nice-assay-potency-v1"
```

The output directories contain metrics, paired intervals, per-structure
predictions and input/product hashes. NPASS additionally exports the source
crosswalk, candidate labels and dispositions.
