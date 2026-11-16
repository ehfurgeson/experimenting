# Compound review — second pass

Date: 2026-10-29. **Everything remains scientifically unapproved.** This is an evidence audit and conditional screening package, not supervised ground truth. Read `research_findings_v2.md` and `policy_draft.md` first.

- `compound_by_compound_deep_audit.csv`: 154 one-row-per-molecule study-level audit, caveats, next tasks.
- `study_source_index.csv`: all 14 source publications and level of access.
- `conditional_assay_screen_NOT_FOR_TRAINING.csv`: 154 conditional cross-policy triage entries, not a seven-column label importer file.
- `PROVISIONAL_LI2006_NOT_FOR_TRAINING.csv`: 14 conditional active, 10 conditional inactive, one unapproved 2006 policy.
- `PROVISIONAL_HE2011_NOT_FOR_TRAINING.csv`: 29 conditional active, 21 conditional inactive, 8 source gray-zone, one unapproved 2011 policy.
- `PROVISIONAL_labels_NOT_FOR_TRAINING.csv`: inherited four original activity and four origin proposals.
- `reviewed_labels.csv`: 154-row authoritative working copy with all categorical labels UNKNOWN until accepted policies and source matching.
- `evidence_log.csv`: 157 source observation rows with annotated study-level evidence. Original source columns preserved.
- `policy_draft.md`: original plus two additional policies, all unapproved.
- `compound_index.csv`, `compound_evidence_packets.md`, `researcher_guide_source.md`: source navigation.
- `review_statistics.json`, `release_manifest.json`: statistics and hashes.

**Caveat**: Every frozen ID is individually listed and assessed in its source family, but 154 independently verified original compound structure/table checks have NOT been completed. Paper access and exact row verification are major constraints.
