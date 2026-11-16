# Researcher label handoff delivery — 2026-10-29

**Document status:** Historical handoff delivery report, 2026-10-29. Reviewed for organization 2026-11-02.

Working materials exist; the inspected worksheet remains all unknown and the policy draft is not an approved biological policy.

Current guidance: [topic note](../../current/structure-and-activity.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Branch: fix/reproducible-structure-folds
Base for this round: 9fbc272 (feat: rebuild assay review files from frozen snapshots)
Initial/final tracked worktrees clean. Nothing pushed or merged; no pre-existing
commit rewritten; no pre-existing uncommitted work modified or discarded.
Original label template, evidence files and frozen manifests remain unchanged.

1. 586b04f chore: document compound label research workflow
   Files: analysis/docs/label_review_guide.md, analysis/README.md.
   Purpose: Explain the evidence, identity, assay-policy and schema requirements
   for a researcher reviewing each worksheet ID. This is a documentation-only
   change; no model, parser, source data or scientific label was changed.

Guide coverage: project/model context; 154-ID/157-observation dataset provenance;
all seven fields and accepted values; per-compound workflow; natural occurrence
versus synthesis; active/inactive/unknown evidence; source citation requirements;
qualifier handling; conflicting and missing outcomes; known dataset examples;
policy worksheet; schema-only validation; later modeling commands; acceptance
criteria and biological/model-validation limits.

Local supporting artifacts, intentionally ignored:
analysis/outputs/chembl-researcher-handoff-2026-10-29/
- compound_evidence_packets.md — all 154 IDs, structures, source outcomes and links
- compound_index.csv — worksheet-order navigation and evidence flags
- reviewed_labels.csv — byte-identical working copy of original unknown labels
- evidence_log.csv — 157 source observations, all decisions blank/unreviewed
- policy_draft.md — unapproved activity/origin definitions to complete
- README.md and handoff_manifest.json — transfer instructions and source/output hashes

Verification:
- Matched all 154 IDs in order, with one evidence packet per worksheet row.
- Matched all 157 source activity IDs in the review log.
- Verified source/output hashes, original/working-label byte equality and local links.
- Executed the exact guide section 9 validation command using the analysis
  environment: 154 rows; all activity/origin targets null; schema checks passed.
- git diff --check: clean.
- No implementation changes: unrelated full model/pipeline suites were not rerun.

Remaining scientific work: choose and justify a coherent activity policy, confirm
compound-to-publication identity, review original methods/results, research exact
natural occurrence, and annotate supported labels or explicit unknowns. No
primary paper was scientifically verified and no activity/origin label assigned
by generation of this context package. The researcher must receive the local
working pack and frozen data/snapshots as well as the maintained guide; generated
artifacts are not included in a Git clone.
