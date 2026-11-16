# AI-assisted agrochemical compound verification — 2026-11-05

This release is **not for training or validated scientific labels**. It preserves the original 154-compound / 157-observation ChEMBL review and adds external structure matching, a primary 2006 study crosswalk, natural isolation evidence, new natural-product leads and a critical source-identity discrepancy.

Start with **verification_report.md**. Use **all_154_compound_verification_matrix.csv** for full row-by-row status; **independent_structure_origin_crosschecks.csv** for exact structural matching; **li_2006_24_compound_source_crosswalk.csv** for source-number and band comparisons; and **evidence_log_with_verification.csv** for the full 157-row record-level history.

Approved activity and origin labels remain `unknown` in `reviewed_labels.csv` while the policy is unapproved. All provisional origin candidates reside in a separate file. The `CHEMBL2253255` source match is especially concerning; verify original figure and SI before training.

Report generated 2026-11-05. RDKit 2025.09.4.
