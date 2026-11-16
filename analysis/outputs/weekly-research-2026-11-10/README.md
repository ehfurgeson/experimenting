# Weekly research pilots — 10 November 2026

EPA rat oral pilot: 88 cached source chemicals; 34 compounds with exact medians; 25 censored records kept separate. Pooled exploratory cutoffs: 1080, 3400 mg/kg. Literature: 15 provisional structures from 4 publications versus 58 selected-herbicide structures. ECOTOX: 18,551 source chemicals, 725,635 tests, 1,250,611 results; 104 candidate selection overlaps.

Open `walkthrough.html` for figures, metrics, weights, sources and the cross-track overlap.

## Evidence gaps

- The three biological groups are not established. All literature origin/activity labels remain unknown pending source structure, isolation, assay-policy and scientific review. Dietary comparators cannot supply tested-negative labels.
- Source screening is AI-assisted. The 1998 phenolic paper was screened at publisher-abstract level; full methods/figures remain pending. For 2020/2024, PDF treatment tables were checked but compound-level source identities and response labels were not adjudicated.
- The LD50 pilot is restricted to the existing purposive EPA cache, not the ECOTOX discovery population. Qualifiers, heterogeneous acute contexts and possible cross-reference duplicate studies limit interpretation; lower LD50 means greater toxicity.
- ECOTOX preflight preserves raw source keys and samples. Full endpoint decoding, normalization, source-specific identity approval, origin annotation and cross-source study reconciliation remain follow-up work.
- Current models predict selection membership. Five-fold scaffold support remains required for a reviewed activity model; no biological model was fitted. OOB repeat SD is not a statistical significance test and OOB predictions do not provide scaffold independence.

## Next steps

1. Review the source structures and primary isolation references for the 15 leads; then review the 2024 low-response conditions and the 1998 full paper. Keep field performance separate from broad plant inactivity.
2. Agree one assay-specific activity policy and record human scientific approvals before transferring any labels. Preserve Li 7b identity hold and all earlier frozen worksheets.
3. Use the ECOTOX chemical inventory to prioritize DTXSID/source-identity review and natural occurrence searches. Implement conservative endpoint normalization as a separate increment.
4. Reassess both-class scaffold support after approved labels exist; reserve independent publication evidence before activity-model selection or candidate scoring.
