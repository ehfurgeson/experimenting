# Scaffold-preserving out-of-bag randomization

Use the existing seven-descriptor, 200-tree forest for a separate binary
diagnostic of low rat oral LD50 against the other two bins. It runs once on
ICE and once on OPERA CATMoS teacher targets. The statistic is positive-class
out-of-bag F1 with a 0.5 probability threshold. The main three-class
scaffold-held-out results and the logistic feature weights remain in the
[import results](import-results-2026-11-18.md).

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/oob_null_test.py --release "$run/public-cohorts-v2" --output "$run/oob-block-null" --repeats 49
```

The diagnostic uses the same transitive scaffold/connectivity blocks as the
held-out benchmark. It sorts structures by full InChIKey to establish a fixed
order, then exchanges whole target vectors between blocks of the same size.
Unique block-size strata stay fixed. Each refit preserves the overall class
count and within-block label pattern. The test assumes that blocks of equal
size are exchangeable under the null. Each permutation refits the same
model with a fixed seed and calculates its own OOB predictions.

The empirical one-sided p-value includes ties and counts the observed
arrangement as one draw. Across the two pathways the report applies a
Bonferroni correction. With 49 refits the raw resolution is 0.02 and the
smallest adjusted value is 0.04. The result concerns the global binary forest
within these cohorts and against this conditional null. It leaves
feature-specific significance, independent study transfer, and human toxicity
unresolved. Structures from the same block can appear in a tree's training
sample when it scores an out-of-bag observation. The earlier OOB variable
importance remains a separate descriptive feature analysis.

## Results

| Target | Structures | Structures in exchangeable size strata | Observed OOB F1 | Null mean | Null maximum | Adjusted p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ICE experimental A | 4,234 | 1,814 | 0.678 | 0.635 | 0.651 | 0.04 |
| OPERA CATMoS teacher B | 43,128 | 17,282 | 0.773 | 0.669 | 0.677 | 0.04 |

Each observed score exceeded all 49 null refits. The raw p-value was 0.02
for each cohort, the smallest available at this run size. Most structures
remain fixed in the null because their block size is unique. The estimates
therefore apply to this conditional comparison. The summary and 98 replicate
scores are in `experiments/import-expansion/oob-block-null/`.

References: [Random forests](https://doi.org/10.1023/A:1010933404324),
[whole-block permutation principles](https://pubmed.ncbi.nlm.nih.gov/26074200/),
and [Monte Carlo permutation p-values](https://pubmed.ncbi.nlm.nih.gov/21044043/).
