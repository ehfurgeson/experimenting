# Review of low-LD50 catalog matches

The review covers the 702 exact COCONUT or NPASS matches in the integrated
screen's low ICE median bin. It exports the underlying ICE source identifiers and
qualifiers and keeps NPASS associations separate from adjudicated origin
evidence. The median-bin cohort is the same as in the
[import results](import-results-2026-11-18.md).

```powershell
$run = 'experiments/import-expansion'
uv run --project analysis --locked python -X utf8 analysis/catalog_hazard_review.py --root $run --integrated "$run/integrated-v5" --review analysis/resources/catalog_low_origin_review.csv --output "$run/catalog-hazard-review"
```

The 702 structures link to 1,221 eligible exact or censored ICE rows and
4,667 NPASS source associations. All eligible exact ICE reports fall in the
low bin for 656 structures. Exact reports cross the low-bin boundary for
46 structures. The review keeps all 702 outside the lower-acute-lethality
shortlist. Different ICE citation strings can still refer to the same
original study.

NPASS links 147 of the structures to a taxon and reference. A four-case
evidence review found primary biosynthesis support for caffeine and juglone.
The other two cases have documented pesticide uses and unresolved natural
origin in this review. The four cases were selected to examine the catalog
evidence and provide no estimate of natural-origin prevalence. Another 698
structures remain unreviewed. The
[review input](../resources/catalog_low_origin_review.csv) records structures,
conclusions and sources.

The three CSV files retain structure-level agreement, observation-level
toxicity context, and NPASS taxon and reference associations. Censored reports
remain separate from exact values. The run manifest hashes the inputs and
outputs.

## LOTUS adds study leads for 118 structures

The optional cross-reference uses the 20.6 MB core triplet file from the
13 April 2026 release. The runner checks the publisher MD5 before loading
the exact full InChIKey links, then preserves all matching raw triplets.
[LOTUS v11 archive](https://zenodo.org/records/19360665).

```powershell
$run = 'experiments/import-expansion'
curl.exe -fLsS -o "$run/raw/lotus-v11.csv.gz" 'https://zenodo.org/records/19360665/files/260413_frozen.csv.gz?download=1'
uv run --project analysis --locked python -X utf8 analysis/catalog_hazard_review.py --root $run --integrated "$run/integrated-v6" --review analysis/resources/catalog_low_origin_review.csv --lotus "$run/raw/lotus-v11.csv.gz" --output "$run/catalog-hazard-review-v2"
```

LOTUS matched 5,411 triplets for 233 of the 702 structures. Of those, 232
structures have a DOI-bearing LOTUS link. Comparing that criterion with
NPASS taxon/reference linkage gives 114 with both, 118 with LOTUS alone,
33 with NPASS alone and 437 with neither. The combined queues therefore have
265 structures with a source reference lead. Two LOTUS rows have the
provider's manual-validation flag. The review retains those flags without
treating them as confirmed biosynthesis. Both providers can cite the same
study. Repeated triplets and overlap between the providers leave scientific
independence unresolved.
