# Connecting the deeper compound review to candidate triage

Latest follow-up: the [5 November verification release](verification-release.md)
adds external identity checks and a critical Li 7b hold. The 47 conditional
actives below describe the preserved historical package, not its effective current status.

Reviewed **2026-11-05**. Source package:
`notes/compound_review_deeper_2026-10-29/` in the historical research archive.
This assessment preserves that directory unchanged. It reviews the package and
its lineage; it does not independently approve the original paper tables,
structure drawings, biological thresholds or labels.

## What this adds

The package deepens the **same 154 ChEMBL compounds / 157 observations / 14
publications** already present in the frozen assay-review exports. It is not
another independent 154-compound acquisition. It adds study-level interpretation,
policy proposals, exact-identity tasks and conditional response triage.

This is complementary to the [40-candidate dietary triage](dietary-triage.md):

| Material | Research question | Current usable conclusion |
| --- | --- | --- |
| Original 171-compound model cohort | Can features distinguish the selected herbicide and natural-product sources? | Exploratory source-selection scores; not biological activity |
| Dietary candidate review | Which food-use candidates deserve less/more dietary-context review? | 12 provisional, 26 priority, 2 presumed-plant-negative exclusions; no accepted safety or activity labels |
| Deeper ChEMBL review | Which measured plant responses could support a defined activity policy? | 47 conditional active, 31 conditional low-response, 8 gray-zone, 68 not assessed; all unapproved |

The ChEMBL set has **five exact structure overlaps** with the original selection:
atrazine, norflurazon, metolachlor, 2,4-D and glyphosate. There are **zero exact or
additional first-InChIKey-block overlaps** with the 40 dietary candidates. The two
review efforts therefore provide different evidence on different structures;
they cannot be joined by name or substituted for each other's negative labels.
Dietary tolerance does not establish plant inactivity, and low plant response
under one study does not establish human/non-target safety.

## File-by-file assessment

All 16 files were read or structurally audited, including every CSV row and every
compound packet's identifiers/structure against the frozen source. The 15 hashes
listed in `release_manifest.json` match. Hash agreement establishes package
integrity, not source accuracy or scientific approval.

| File | What is in it | Reuse / qualification |
| --- | --- | --- |
| `README.md` | Navigation and explicit unapproved status | Good entry point; its small source-specific counts concern selected rows within 154-row files |
| `research_findings_v2.md` | Study-level synthesis, conditional totals and access limits | Useful research context and priority list; not accepted findings about compound efficacy |
| `policy_draft.md` | Proposed Okamoto 1991, Li 2006, He 2011 rules and a separate occurrence definition | Useful starting policies to discuss; keep contexts separate and reconcile older wording with the later v0.2 additions before approval |
| `study_source_index.csv` | 14 studies, access levels, endpoint cautions, unresolved mapping/approval | Best source-acquisition queue; every study says structure crosswalk and scientific policy are unapproved |
| `compound_by_compound_deep_audit.csv` | 154 per-ID source families, flags, identity and next actions | Good work queue; study-level annotations are not 154 verified original structure/table mappings |
| `evidence_log.csv` | 157 original observations plus source-method/decision annotations | Most valuable reusable evidence table: all first 16 source columns match the original handoff, and snapshot hashes match the 14 local raw bundles |
| `conditional_assay_screen_NOT_FOR_TRAINING.csv` | 154 per-compound conditional outcomes spanning different policies | Use as a triage index only; repeated compounds can have several outcomes while the row names only one assay |
| `PROVISIONAL_LI2006_NOT_FOR_TRAINING.csv` | 154-row schema; 14 proposed active, 10 proposed low-response, 130 unknown | Promising assay-specific negative leads; source crosswalk/quality and policy approval remain outstanding |
| `PROVISIONAL_HE2011_NOT_FOR_TRAINING.csv` | 154-row schema; 29 proposed active, 21 proposed low-response, 104 unknown (including 8 in-study gray-zone) | Larger response-band pilot, with severe scaffold concentration; not exact response percentages |
| `PROVISIONAL_labels_NOT_FOR_TRAINING.csv` | 4 original activity proposals and 4 separate natural-occurrence proposals across 154 rows | Small positive/occurrence pilot; not a complete two-class dataset |
| `reviewed_labels.csv` | 154 unknown activity and 154 unknown origin labels; some context/citations already filled | Valid unresolved working copy; filename does not mean scientifically accepted labels exist |
| `compound_index.csv` | 154-ID navigation, structures, observation counts | Byte-identical to the original handoff index: reusable navigation, not additional evidence |
| `compound_evidence_packets.md` | 154 sections, all 157 source observation IDs and supplied SMILES | Byte-identical to the original handoff packet; its relative guide/JSON links break after copying into notes |
| `researcher_guide_source.md` | Escaped/formatted copy of the researcher instructions | Useful background, but prefer the maintained [label guide](label_review_guide.md); copied links/commands refer to other locations |
| `review_statistics.json` | Counts and explicit unapproved flags | Counts reconcile with the CSVs; useful audit metadata |
| `release_manifest.json` | Claimed release date/status and hashes of the other 15 files | Good integrity record; contains no original PDF/SI assets or proof of independent source-row verification |

## The most promising activity leads

| Proposed source-specific policy | In-study compounds | Conditional active | Conditional low response | Gray zone | Scaffold limitation of the hypothetical known subset |
| --- | ---: | ---: | ---: | ---: | --- |
| Li 2006, post-emergence 150 g ai/ha, 15 days | 24 | 14 | 10 | 0 | 6 total scaffolds; low-response class spans only 2 |
| He 2011, post-emergence 1500 g ai/ha, 20 days | 58 | 29 | 21 | 8 | 50 conditionally known compounds span only 2 total scaffolds; each class spans 2 |
| Okamoto 1991, pre-emergence 10 g ai/are, 2 weeks | 4 | 4 | 0 | 0 | 1 scaffold and no proposed negative class |

The **31 low-response candidates** are more directly relevant to a plant-activity
model than presumed inactivity of dietary compounds. They are still low-response
examples only within their proposed species, exposure and threshold rules. A
response below 50% is not equivalent to no biological effect. Li and He use a
**tenfold difference in application rate**, and the Okamoto assay uses a different
stage/species and ordinal endpoint. Do not pool these into one generic target.

A schema-only check and the existing split-support helper were run without fitting
any classifier. All three provisional CSVs are **syntactically importable** under
the current seven-column contract. The importer checks required fields and policy
consistency; it does not verify scientific approval or recognize `NOT_FOR_TRAINING`
filenames. **Do not pass these files to `screen.py --labels`.** The Li and He
subsets both fail current three-/five-fold scaffold support; the four Okamoto
positives fail class support. This audit did not manufacture a favorable split,
merge policies, fit a model or promote a label.

The four ophiobolin occurrence candidates are valuable natural-active leads for a
separate origin/activity review. The [2006 primary abstract](https://pubmed.ncbi.nlm.nih.gov/16506833/)
documents the four named fungal metabolites and detached-leaf phytotoxicity;
the [2026 primary publication](https://pubs.acs.org/doi/10.1021/acs.jnatprod.5c01414)
provides additional isolation/characterization context. These bibliographic/name
checks do not resolve frozen-SMILES stereochemistry, supply whole-plant percentage
labels, establish environmental allelopathy, or demonstrate safety. “Natural
active” is a useful evidence role; it does not imply an ordinal middle position.

## Cautions the integration must preserve

- **Response representation:** Li's `>80%`/`<50%` inequalities and He A/B/C/D
  grade boundaries are not precise continuous outcomes. Okamoto's cached 80/100
  percentages are reported as conversions from ordinal 4/5 and 5/5 in the package.
  Preserve the original source representation and verify it against original tables.
- **Source access:** there are no original PDFs/SI in this 16-file directory.
  Several method interpretations rely on text mirrors or abstracts. Current
  publisher access to Li/He full text was restricted, so this review does not
  newly certify their table cells, control details or source-structure mappings.
  [Li's bibliographic record](https://pubmed.ncbi.nlm.nih.gov/17117801/) and
  [He's record](https://pubmed.ncbi.nlm.nih.gov/21452831/) support the study identities.
- **Units/endpoints:** the package flags g/ha-versus-kg/ha conflicts, pre-/post-
  emergence differences, two missing numeric leaf-necrosis records and two mm
  responses. Do not convert leaf-lesion diameter into whole-plant inhibition.
  Not every kg/ha entry is erroneous: the per-compound unit flag also includes
  the legitimate cached 1 kg/ha glasshouse context. Inspect the study-specific note.
- **Missingness/repeated compounds:** Norflurazon is `Not Determined`, not inactive.
  CHEMBL452197 has 100%, 0% and 73.3% across three studies; CHEMBL95764 has matching
  90% values under distinct pre-/post-emergence contexts. Use all observation-level
  rows, not the first assay ID in a compound summary.
- **Internal editorial drift:** the deep-audit table still calls the He 2011
  family abstract-level, while the study index describes full-text-mirror access.
  Use the source index and explicit access notes, then confirm the original PDF.
  The policy file also retains older “not a second labeling policy” wording above
  later separate proposals. These are review-package inconsistencies, not approval.
- **Origin/target evidence:** missing occurrence is not proof of synthetic origin.
  AHAS/PDHc/PPO-related studies can seed a functional target-evidence review, but
  an enzyme-inhibition or plant-response result alone does not establish direct binding.

## Highest-value next steps

1. Obtain original PDF/SI and build a source-compound-number → exact structure →
   frozen ChEMBL ID crosswalk for Li and He (82 in-study compounds), prioritizing
   the 31 low-response cases along with enough positive comparators. Verify source
   columns, dose, response bands, controls and replication. Save evidence/decisions
   separately from this frozen package.
2. Have the research lead accept or revise **one explicit activity policy per
   compatible dataset**. Keep dietary safety, occurrence, natural-active and
   source-selection roles separate. Do not transfer proposed labels merely because
   they parse successfully.
3. Add independently sourced negative-bearing chemistry/publications. The scaffold
   support audit shows why reviewing the same analogue series is not enough for
   the current validation design. Do not solve that by silently choosing random
   splits or treating dietary candidates as tested negatives.
4. Verify the four ophiobolin identities/occurrence claims independently. Their
   detached-leaf study can remain a separate assay-specific pilot.
5. Extend automated review with **assay-quality triage** (source access, exact
   mapping, units, endpoint, policy eligibility and scaffold diversity). Reuse this
   package's logs/index as inputs; do not run the dietary hazard rules on it as
   though they answer the same question.

## Audit evidence and reproduction

The local ignored bundle
`analysis/outputs/deeper-review-connection-2026-11-05/` retains a file inventory,
14-study inventory, identity crosswalk, hypothetical split-support table, broken-
link inventory, audit counts, the executed standalone `audit.py` and input/code/
product hashes. Re-run its assertions in a fresh directory using the existing
analysis environment (no acquisition, fitting, synchronization or label writes):

```bash
analysis/.venv/bin/python analysis/outputs/deeper-review-connection-2026-11-05/audit.py --root . --output analysis/outputs/deeper-review-connection-new
```

The audit verifies the complete package, original 16-column lineage, raw snapshot
hashes, all packet identities/structures, working-label schema, proposed counts,
scaffold-support guards and cross-cohort exact/connectivity overlaps. It does not
replace chemistry/publication review. No full model/test rebuild is needed for
this documentation/integrity assessment; existing model performance was not rerun.

Copied packet links should be read via the maintained
[label guide](label_review_guide.md) and actual snapshots at
`analysis/outputs/chembl-2026-10-28/raw/chembl/<assay_id>.json`. Do not edit the
frozen packet just to repair links; that would invalidate its release hash.

For the exact next actions, use the [human verification checklist](verification-checklist.md).
An editable local working pack now separates 24 Li and 58 He source-matching rows,
reference drawings, unknown working labels and the 40 dietary review rows. It is
preparation for human decisions, not an approved label/result bundle.
