# Researcher handoff — 2026-10-29

Read the [comprehensive context and review guide](../../docs/label_review_guide.md) first.
Then open [the compound packets](compound_evidence_packets.md) or `compound_index.csv`.
Every one of the 154 worksheet IDs is included; 157 source observations are retained.

Edit `reviewed_labels.csv` as your working copy. It starts byte-identical to the frozen
unknown-label template. Record observation-level source checking and decisions in
`evidence_log.csv`; agree the written rules in `policy_draft.md`. Preserve source fields
and put proposed corrections in the review columns. Add log rows for newly found
assays or natural-occurrence evidence. No labels have been researched or assigned by
this handoff, and no primary-paper conclusion has been verified by its generation.

Keep the original review products and raw snapshots unchanged. The handoff manifest
records their hashes and hashes the initial supporting files. After manual annotation,
the initial handoff hashes will no longer describe the edited working files; save a
separate dated review release with reviewer/policy provenance rather than overwriting
the baseline manifest or claiming that the edited files match it.

This local pack and source data are ignored by Git. A complete researcher transfer
needs the guide, pack, frozen review files and raw bundles in the same relative layout.
