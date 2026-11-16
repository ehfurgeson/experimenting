# Experimental source-linked rat LD50 review — 2026-11-12

Two pending ECOTOX rat cases now have primary-source mappings and four priority
overlap decisions. These are **AI experimental** decisions authorized for this
local branch. The historical baseline, native fields and accepted biological
labels remain unchanged. This is not a harmonized natural-product/herbicide
hazard comparison or a general rat eligibility importer.

## Primary evidence and dose basis

[Gorzinski et al. (1987)](https://doi.org/10.1016/0272-0590(87)90025-X),
*Fundamental and Applied Toxicology* 9:423–435, reports acute, pharmacokinetic and
subchronic studies in distinct sections. The scanned full paper was retrieved
from an accessible [PDF mirror](https://24d.info/wp-content/uploads/2020/08/Toxicological_Study_Gorzinski_1987_Exposure_24D.pdf);
first-page bibliographic identity agrees with the native reference. It is primary
authored work hosted by a third party, not a publisher download. Authors are Dow
laboratory investigators and the paper reports industry-task-force support.
Correction/retraction history is not exhaustively verified.

The PDF has no native text. All 13 pages were rendered with PyMuPDF because
Poppler was unavailable; printed pages 423–427 and an enlarged Table 1 were
visually inspected. No successful OCR or independent human review is claimed.
Table 1 on printed page 426 yields 14 material/sex cells: 13 uncensored
material-tested LD50s with reported 95% confidence limits, plus a noncalculable
female isooctyl result `>720–<864`, preserved without a midpoint or scalar.
Salts/esters retain their named forms, without automatic canonical-acid mapping.

The two pending acid records map as follows; stable full IDs remain in the local
CSV, with result numbers abbreviated here for readability:

| ECOTOX result | Sex | Source acid-equivalent LD50, mg/kg body weight | Material-tested LD50, mg/kg | Material-tested 95% confidence limits |
|---|---|---:|---:|---|
| 1055251 | Male | 607 | 639 | 555–736 |
| 1147683 | Female | 726 | 764 | 663–879 |

The acid test material is **95% active**. Its reported acid-equivalent values
agree with that adjustment within rounding. Material and acid-equivalent columns
remain separate, and no confidence limits are invented for the latter. An
uncensored reported estimate is not an estimate without statistical uncertainty.

Printed page 424's acute methods specify single-dose oral studies in young-adult
male/female Fischer 344 rats, five rats per sex per dose, approximately 18 hours
fasting, corn-oil suspension and two weeks observation. Five animals per dose is
not five total animals. The acute subsection does not explicitly name gavage or
capsule administration. Gavage appears in the separate pharmacokinetic methods
and is not imported into these records. Acute control performance is not supplied
by the subchronic protocol or database control metadata.

Under a distinct experimental **single-dose oral, source-reported acid-equivalent**
policy, the two cases are provisionally eligible. Under the existing conservative
explicit-gavage/capsule rule, technique remains unresolved. Neither is added to
the historical baseline. The primary source conflicts with native dietary (`DT`)
and two-week exposure fields; those fields are preserved with a contradiction
note, not overwritten. Two weeks observation is independently supported.

## Displayed conversion discrepancies

Table 1 footnote c defines acid-equivalent dose using the displayed molecular-
weight ratio, active percentage and material-tested dose. An arithmetic audit
flags **two other female ester cells**:

| Material | Reported acid-equivalent mg/kg | Computed from displayed inputs, mg/kg |
|---|---:|---:|
| Butoxyethanol ester | 565 | 529.327056 |
| Butyl ester | 519 | 472.0968 |

The enlarged original table confirms these transcriptions. Reported values remain
unchanged and flagged; no cause, typographical correction, new normalized dose or
scientific adoption is inferred. The other 11 computable cells agree within
1 mg/kg, allowing for displayed precision. The noncalculable cell stays unknown.
The two acid rows under review are not these discrepant cells.

## Four different-observation decisions

Each acute record has candidate pairs with two EPA records from the same DOI.
Those EPA records describe **15 mg/kg-day, 91-day dietary LOELs**, with female
thyroxine and male relative-organ-weight effects. The primary methods distinguish
acute single dosing from the 13-week dietary experiment. These are different
observations, not repeated reports of the acute LD50. Equal DOI alone does not
establish duplication.

Four six-column importer decisions explicitly name the reviewer
`Codex_AI_experimental` and retain source locators/PDF hash. The new reconciliation
run adopts all four `different_observation` states, excludes no measurements and
preserves the 18,992-pair queue. The other 22 priority pairs remain unreviewed.
This does not prove the absence of other reporting-chain duplication.

## Deliberately relaxed sensitivity calculations

The historical pilot has **43 exact and 25 censored observations**, 49 compound
summaries, and 34 compounds with exact medians; 15 have censored-only support.
Its retained 2,4-D value is 375 mg/kg from a WHO summary with unknown primary
lineage, sex, tested material and dose basis. The primary source's sex-specific
acid-equivalent results cannot establish compatibility with that summary.

Separate source-only strata retain the new material-tested versus acid-equivalent
points. Additional, explicitly **mixed-basis experimental arithmetic** compares
record pooling and paper-level aggregation:

| Scenario | 2,4-D descriptive median, mg/kg | Exact rows or input aggregates |
|---|---:|---:|
| Historical retained values | 375 | 43 |
| Add 607 and 726 as separate records | 607 | 45 |
| Aggregate those two to 666.5 first, then combine with 375 | 520.75 | 44 |

The last two scenarios expose source/sex weighting assumptions. They do not
resolve the unknown basis or make estimates independent. No meta-analysis or
confidence interval is claimed. All 34 exact-median compound bins and the
1,080/3,400 mg/kg tertiles remain unchanged in both scenarios; the 25 censored
observations remain intact. No new harmonized compound comparison, natural-
product hazard rank, activity label or model follows.

## Reproduction and verification

The ignored local root `experiments/rat-source-review-2026-11-12/` contains
`fetch.py`, cached PDF/retrieval hash, rendered pages, `curate.py`, `curation-v1/`,
`conversion_audit.py`, `conversion-audit-v1/`, `sensitivity.py`, `sensitivity-v1/`,
`verify.py`, `verification.json` and `SUMMARY.md`. Acquisition requires network;
analysis/verification are offline. Scripts require fresh output versions when
rerunning; original outputs are never rewritten. From repository root:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python experiments/rat-source-review-2026-11-12/verify.py
```

The existing importer propagates the four decisions in a separate result:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/expansion_toxicity.py \
  --baseline analysis/outputs/weekly-toxicity-2026-11-10 \
  --ecotox analysis/outputs/ecotox-selected-approved-2026-11-11 \
  --crosswalk analysis/outputs/ecotox-identities-approved-2026-11-11/approved_crosswalk.csv \
  --decisions experiments/rat-source-review-2026-11-12/curation-v1/duplicate_decisions.csv \
  --output analysis/outputs/NEW_RAT_SOURCE_RECONCILIATION
```

The verified concrete run is
`analysis/outputs/rat-source-reconciliation-2026-11-12/`. The source-specific
eligibility CSV is a research result, not an automatically consumed rat overlay.
Internal checks cover 14 source cells, two discrepancies, two case/sex mappings,
four adopted decisions, three arithmetic scenarios, 25 preserved bounds and
**45 hashes**. A failed early assertion exposed the distinction between the
49-row compound summary and 34 exact medians; it was fixed before creating the
sensitivity output. The source-formula audit's failed assertion was retained as
two explicit discrepancy flags after visual reinspection, not erased by
correcting printed data.

The separate [elapsed-week conversion](../../pipeline/docs/normalization.md#units-and-durations)
now preserves dictionary-validated ECOTOX `2 wk` as 336 hours. Native exposure
and observation fields remain separate; conversion alone establishes neither
continuous exposure nor acute eligibility. Regression checks include age,
follow-up periods, conflicting/range times, dictionary support and overflow.
**1,076 pipeline tests, 299 analysis tests and pipeline Ruff pass** for that change.
Frozen exports were not rebuilt. Independent review, 14 other rat cases,
22 remaining priority pairs and historical-source lineage remain open.
