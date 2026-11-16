# Cached point of departure analysis

Verified 2026-10-22 using the existing `experiments/data` raw caches, the approved
EPA crosswalk, and `pipeline/examples/endpoints.yaml`. This is a manual evidence
checkpoint, not a test fixture or an expectation that future data must match.
No API request or new source retrieval was needed.

From the repository root:

```bash
uv run --project pipeline python pipeline/examples/analyze_epa_hazards.py \
  --data experiments/data --input experiments/data/compounds.csv \
  --output pipeline/.live-smoke/chronic-endpoints
```

The selection contains 176 resolved compounds: 60 herbicides and 116 natural
products. EPA identities are approved for 136; the other 40 remain in coverage
denominators with explicit identity audit states. Raw caches and generated
Parquet/metadata products remain uncommitted.

## Current coverage

Counts are compounds with at least one eligible result, not numbers of studies.
Each source has its own evidence; the two columns must not be added together.
The broad oral mammalian policies do not imply a rat-only potency comparison.

| Definition | PubChem herbicides | PubChem natural products | EPA herbicides | EPA natural products |
| --- | ---: | ---: | ---: | ---: |
| `mammal_oral_ld50` | 39 | 30 | 36 | 14 |
| `fish_lc50` | 4 | 4 | 0 | 0 |
| `trout_lc50_96h` | 4 | 0 | 0 | 0 |
| `daphnia_ec50_48h` | 0 | 0 | 0 | 0 |
| `mammal_oral_noael_daily` | 0 | 0 | 34 | 16 |
| `mammal_oral_loael_daily` | 0 | 0 | 32 | 8 |
| `mammal_oral_bmd_daily` | 0 | 0 | 0 | 0 |
| `mammal_oral_bmdl_daily` | 0 | 0 | 2 | 0 |

NOAEL/LOAEL/BMD/BMDL extraction is implemented through structured EPA hazard
records. PubChem text extraction still supports LD50/LC50/EC50 only. Zero
PubChem chronic coverage here describes extraction support, not proven absence
of chronic evidence in PubChem.

The eight definitions cover seven endpoint types because fish LC50 has both a
broad and a trout-specific policy. They are not the four highest-priority
research comparisons: an algal EC50 policy is still absent.

## Normalization and review

The 5,814 EPA records produce 1,438 complete, 522 partial, and 3,854 failed
normalized annotations. Every row remains inspectable. The 4,376 partial/failed
rows form the review queue, including endpoints outside the seven-type scope,
uncertain experimental status, unsupported units, and invalid results.

Raw evidence includes 845 NOAEL records, 660 LOAEL records, one unsupported
`LOAEL (HEC)` variant, and three `BMDL (10)` records. Of these, 684 NOAEL,
645 LOAEL, and all three BMDL rows normalize completely. There are no BMD
records in these caches; synthetic tests establish code support for BMD.

The BMDL labels retain their response token without inventing a confidence
level, response-risk interpretation, model, or paired BMD. The four daily-dose
availability policies produce 92 compound summary rows, all with null potency
medians. No daily doses are converted to total doses. Meaningful potency
summaries require the explicit context documented in the README.

## Previously saved comparison products

`experiments/data/epa_endpoint_coverage.csv` reports 76 compounds with EPA oral
LD50 coverage (40 herbicides, 36 natural products). That saved comparison
product is stale under the current experimental-only admission policy.
Rebuilding from raw caches gives 50 (36 herbicides, 14 natural products).

As a regression check, the pre-branch adapter from commit `b1f8fd4` was evaluated
against the same hazard records and acute definitions. Its complete acute
coverage table is identical to the new workflow's table. The difference from
76 therefore does not come from the point of departure extension. Existing
processed experiment tables were left untouched; use the rebuilt products or
regenerate downstream analyses before citing current counts.

## Verification

The synthetic offline integration exercises all seven endpoint types with the
network blocked. It checks selected denominators, source provenance, absence of
chronic medians by default, exclusion of stale processed hazard products,
missing/mismatched cache errors, read-only inputs, deterministic tables, and
exported dependency sidecars. Real cached counts above are kept out of tests.
