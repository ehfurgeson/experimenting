# Verification release: identities, holds and model readiness

[Analysis](../README.md) · [Human verification steps](verification-checklist.md) ·
[Earlier review](deeper-assay-review.md)

## Findings from the 5 November 2026 release

The local `notes/compound_verification_release_2026-11-05/` advances identity and
source review of the **same 154 compounds / 157 observations / 14 publications**.
It is explicitly AI-assisted and unapproved. It supplies no original paper PDFs/SI
and no accepted activity or origin labels. It does not replace the 40-compound
dietary review or establish benign controls.

`verification_release.py` checks the entire inventory and all **15 listed file
hashes**, unchanged original observation fields, cohort IDs, structures, band
crosswalks and approval flags. RDKit 2026.09.1 reproduces all **154 unique full
InChIKeys** reported using RDKit 2025.09.4. The frozen inputs are unchanged.

| Release files | Assessment and use |
| --- | --- |
| `README.md`, `verification_report.md`, `metrics.json`, `release_manifest.json` | Scope, reported counts and integrity; explicitly not scientist sign-off |
| `all_154_compound_verification_matrix.csv` | Row-by-row status and outstanding work; all approved labels unknown |
| `evidence_log_with_verification.csv` | All 157 observations retain their original 16 source fields; appended review information is provisional |
| `independent_structure_origin_crosschecks.csv` | 16 database comparisons; independently re-fetched and reproduced: 15 full-key matches, one connectivity-only |
| `li_2006_24_compound_source_crosswalk.csv` | 21 substituent-consistency leads, one critical conflict, 7w unresolved and one comparator with unspecified reference stereo; matching all 24 biological bands is insufficient to establish structures |
| `PROPOSED_ORIGIN_FULL_STRUCTURE_MATCHES_NOT_FOR_TRAINING.csv` | Four fungal-occurrence and 11 manufacturing-provenance proposals; policy unresolved, not accepted origin labels |
| `new_primary_study_provenance.csv` | Six useful literature leads; isolate identity, endpoint and ecological role still need source-specific review |
| `new_out_of_worksheet_compound_leads.csv` | 11 new names, not labeled observations; five name-lookup identity candidates and six unresolved names |
| `reviewed_labels.csv`, `conditional_assay_screen_NOT_FOR_TRAINING.csv`, `PROVISIONAL_labels_NOT_FOR_TRAINING.csv`, `compound_index.csv`, `study_source_index.csv` | Historical tables retained byte-for-byte from the deeper package; old conditional activity is superseded by the new identity hold, not promoted to ground truth |

The report mentions `policy_draft.md`, `researcher_guide_source.md` and
`compound_evidence_packets.md`, but these are **absent from this release**. They
remain in the earlier `notes/compound_review_deeper_2026-10-29/` package. This
release is therefore not a self-contained original-source verification packet.

## Highest priority: Li 7b / CHEMBL2253255

The release reports an **N-allyl** source substituent and supporting NMR text for
7b, while the frozen ChEMBL structure is **N-cyclopropyl**. They can have the same
formula, **C18H18N4O4**, while being different molecules. Original source drawings
and SI were not independently visually verified in this audit; this is an
unresolved source-identity conflict, not an adjudicated database correction.

The fresh audit overlay changes this row's historical conditional `active` status
to **`identity_hold`**. Effective scenarios are **46 active / 31 low response /
8 gray zone / 68 unassessed / 1 identity hold**, all unapproved. The original
historical CSV still contains 47 conditional actives and is preserved unchanged.
Never transfer 7b's response to the frozen structure until the source mapping is
resolved. If confirmed, retain both identities and observation lineage in a new
versioned correction; do not silently edit frozen SMILES or reuse old fingerprints.

An explicitly hypothetical structural illustration shows why formulas cannot
catch this error: the two representations have different full InChIKeys and differ
at **21 Morgan bits** (Tanimoto **0.638**). The allyl drawing is a constructed
hypothesis, not a verified source reconstruction or new training example.
CHEMBL2253255 is absent from the original selection-model cohort; this hold does
not require changing its previously reported selection-classification metrics.

## What the external checks establish

Re-fetching the four PubChem and 12 University of Hertfordshire PPDB references
reproduced **15 full-key matches**: four ophiobolins and 11 pesticide records.
Pyriminobac-methyl / KIH-6127, CHEMBL2253237, matches only the connectivity block;
the frozen key specifies geometry that the PPDB reference leaves unspecified.
Full-key agreement is agreement with that database representation, including its
specified stereochemistry; it does not verify a paper's isolate drawing or result
mapping. PPDB's synthetic provenance is manufacturing evidence, not proof of
impossible natural occurrence. The proposed `synthetic_provenance_documented`
category is not a supported canonical origin label and must not be auto-converted.

The additional name searches resolved ophiobolin B, J, E, 8-epi-ophiobolin J and
maydispenoid A to single PubChem identity candidates. Their returned SMILES and
keys agree with RDKit; **five fingerprints** were generated separately, with all
targets null and source-structure matching marked not reviewed. The remaining six
names returned 404 and remain present with missing structures. A failed name query
does not establish that the compound does not exist; use paper/SI structures and
synonyms. Neither the five matches nor the six missing rows enter model training.

A fresh read of the accessible [2021 primary paper](https://www.jstage.jst.go.jp/article/mycosci/62/1/62_MYC515/_html/-char/en)
adds an important bounded-negative lead. Its detached green-foxtail leaf tests
separate punctured/intact leaves and report lesion diameter, not percent weed-growth
inhibition. Ophiobolin I has weak punctured-leaf activity at the highest tested
concentration and no intact-leaf lesions in Table 1; two other congeners show no
lesions under the tested conditions. Mixture synergy is a separate result. These
are endpoint-specific observations to transcribe, not universal inactive labels.
Anticancer results for new gigobolins likewise cannot supply herbicidal labels.

## Why no new activity classifier was fitted

Approved activity labels and approved origin labels remain **zero**. Even ignoring
that approval requirement, the current scaffold guards reject all three Li
scenarios: historical 24 compounds; 23 after excluding the identity hold; and the
21 consistency leads. Each has only **two negative-bearing scaffolds**. The 15
hypothetical occurrence/manufacturing-provenance examples also fail support
(two natural-bearing scaffolds). Removing a suspicious structure does not solve
the independent-chemistry problem. Changing to random splits would obscure it.

The existing formula/Morgan selection models still answer selection membership.
Do not rebrand them as herbicide-versus-benign activity models. Obtain accepted,
endpoint-specific labels and broader independent negative chemistry before fitting
new logistic/forest models. The professor's three-group comparison remains pending.

## Reproduce and inspect

Commands run from the repository root in the existing analysis environment. These
local data bundles are ignored and absent from a fresh clone. Use a **new empty**
output directory; the audit is offline and never edits source or working labels.

```bash
analysis/.venv/bin/python analysis/verification_release.py \
  --release notes/compound_verification_release_2026-11-05 \
  --prior-log notes/compound_review_deeper_2026-10-29/evidence_log.csv \
  --features analysis/outputs/chembl-review-screen-2026-10-29-final/structural_features.parquet \
  --snapshots analysis/outputs/verification-release-sources-2026-11-05 \
  --output analysis/outputs/verification-release-audit-NEW
```

`analysis/outputs/verification-release-audit-2026-11-05-final/` contains:
`audit.json`, independent `reference_checks.csv`, `review_priority.csv`,
`effective_conditional_screen.csv`, `identity_holds.csv`, hypothetical
`model_readiness.csv`, illustrated `identity_case.json`/`.svg`,
`new_lead_identities.csv`, `new_lead_features.parquet` and a hash/version manifest.
The source acquisition bundle retains **28 request snapshots**, including six
404s, request URLs, bodies, timestamps, status codes, acquisition code and hashes.
This documents what was retrieved, not exhaustive literature coverage.

Check a separately versioned proposed seven-column label file against the frozen
hold before any training:

```bash
analysis/.venv/bin/python analysis/validate_activity_proposal.py \
  --labels analysis/outputs/manual-verification-2026-11-05/assays/reviewed_labels.csv \
  --features analysis/outputs/chembl-review-screen-2026-10-29-final/structural_features.parquet \
  --audit analysis/outputs/verification-release-audit-2026-11-05-final
```

This checks label schema/cohort/conflicts and rejects any active/inactive assignment
to a held ID. Passing **does not verify scientific approval**, exposure claims or
assay comparability. Existing `screen.py` importers and the old working-pack
validator do not automatically enforce this new hold. Preserve the current frozen
hold audit; a resolution requires a new reviewed source decision and audit version.

Next: obtain Li PDF/SI, adjudicate 7b first, resolve 7w and comparator geometry,
visually validate the 21 remaining source assignments, review He separately,
approve bounded policies and expand independent negative-bearing families.
Existing editable human worksheets were not overwritten.
