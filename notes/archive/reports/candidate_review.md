# Seven-candidate PubChem coverage review

**Document status:** Historical seven-candidate evidence review, 2026-10-15. Reviewed for organization 2026-11-02.

Counts describe frozen PubChem snapshots and extraction rules, not safety. Current reproduction context is the pipeline live retrieval checkpoint.

Current guidance: [topic note](../../current/evidence-and-identities.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Contents of the historical record:

- [Which questions can this snapshot support?](#which-questions-can-this-snapshot-support)
- [Evidence to discuss ](#evidence-to-discuss-)
- [Local audit trail](#local-audit-trail)

Observed 2026-10-15 from the saved PubChem Toxicity sections. This is a review of
what this pipeline retrieved and could extract, not a literature-wide assessment
or a safety ranking. The best demonstrations of supported numeric evidence in
this selection are **vanillin** and **azadirachtin**. Solanine has substantial
narrative evidence that the current LD50/LC50/EC50 extraction does not capture as
eligible measurements.

The selection is `examples/candidates.csv`; the explicit availability policies
are `examples/endpoints.yaml`. All seven belong to the selected `natural_product`
group. Follow the [walkthrough](../../walkthrough.md) to reproduce and inspect them.

| Query and resolved PubChem CID | Toxicity section | Annotations | Complete | Partial | Current finding |
| --- | --- | ---: | ---: | ---: | --- |
| [Citrulline, 9750](https://pubchem.ncbi.nlm.nih.gov/compound/9750#section=Toxicity) | Found | 2 | 0 | 0 | Descriptive records; no extracted supported endpoint |
| [Solanine, 30185](https://pubchem.ncbi.nlm.nih.gov/compound/30185#section=Toxicity) | Found | 20 | 0 | 0 | Narrative toxicology; no extracted supported endpoint |
| [Tricolorin A, 10418553](https://pubchem.ncbi.nlm.nih.gov/compound/10418553#section=Toxicity) | Missing | 0 | 0 | 0 | Identity resolved; Toxicity request returned 404 |
| [Azadirachtin, 5281303](https://pubchem.ncbi.nlm.nih.gov/compound/5281303#section=Toxicity) | Found | 46 | 3 | 5 | Oral and dermal LD50 thresholds; extract/formulation evidence retained for review |
| [Vanillin, 1183](https://pubchem.ncbi.nlm.nih.gov/compound/1183#section=Toxicity) | Found | 83 | 8 | 0 | Mammalian LD50 and fish LC50/EC50 extractions |
| [Syringic acid, 10742](https://pubchem.ncbi.nlm.nih.gov/compound/10742#section=Toxicity) | Found | 4 | 0 | 0 | Descriptive hazard annotation and EFSA query pointers |
| [Ferulic acid, 445858](https://pubchem.ncbi.nlm.nih.gov/compound/445858#section=Toxicity) | Found | 42 | 0 | 0 | Narrative/interaction evidence; no extracted supported endpoint |

Totals: seven selected compounds, 197 annotations, 11 complete, five partial,
181 failed. Here `failed` describes extraction support; the saved annotation and
its provenance remain available. Annotations are not independent studies.

## Which questions can this snapshot support?

| Policy | Compounds with eligible evidence | Selected denominator |
| --- | --- | ---: |
| Mammalian oral LD50 | Vanillin, azadirachtin | 7 |
| Fish LC50, any recognized fish species/duration | Vanillin | 7 |
| Rainbow-trout LC50, explicit 96 hours | None | 7 |
| Daphnia magna EC50, explicit 48 hours | None | 7 |

These are broad availability policies for demonstration. They do not justify
pooling mammalian species or treating fish durations as interchangeable. All
seven selected compounds stay in every denominator, including tricolorin A with
its missing section. A zero means no saved row passed that policy, not that the
compound is safe or lacks published toxicity information.

## Evidence to discuss 

**Vanillin:** The saved HSDB-derived records include rat oral LD50 1580 mg/kg and
fathead-minnow LC50 results of 112 mg/L at 24 hours and 65 mg/L at 48 hours. These
pass broad oral/fish availability rules, respectively. The fish rows fail the
trout rule because both the species and exposure duration differ. Additional
complete rows cover nonoral mammalian routes and fish behavioral EC50 endpoints;
they do not add extra compounds to coverage. Original endpoint details and study
citations still need scientific review. [PubChem HSDB source](https://pubchem.ncbi.nlm.nih.gov/source/hsdb/1027).

**Azadirachtin:** Saved rat oral LD50 is greater than 5000 mg/kg; rabbit oral and
dermal LD50 are each greater than 2000 mg/kg. Oral thresholds pass availability
without becoming exact values. A mouse oral result attributed to neem extract
and amphibian LC50 results attributed to formulated products remain partial and
excluded. They cannot stand in for pure azadirachtin or fish evidence.
[PubChem HSDB source](https://pubchem.ncbi.nlm.nih.gov/source/hsdb/7372).

**Solanine:** The saved section includes human poisoning and glycoalkaloid risk
narratives, including material discussing multiple potato glycoalkaloids. These
are relevant to a manual toxicology review but do not provide a supported,
unambiguous LD50/LC50/EC50 extraction in this snapshot. Zero automated coverage
should prompt source review, not a conclusion of little biological toxicity.

**Citrulline, syringic acid, and ferulic acid:** The saved records offer little
directly usable evidence for the configured acute endpoints. Citrulline's two
records are descriptive. Syringic acid includes EFSA database query pointers;
the pipeline preserves those strings but does not execute those queries or
retrieve the linked database's underlying studies. Ferulic acid's section
contains narrative and interaction material that cannot be assigned an acute
endpoint solely from the occurrence of a numeric concentration. These are
candidates for targeted source/literature follow-up if the compounds remain of
interest.

**Tricolorin A:** The chemical identity resolved, but PubChem's Toxicity-section
request returned 404 and was saved as an explicit missing marker. This says
nothing about whether toxicity or phytotoxicity studies exist elsewhere.

Before comparing compounds, confirm the intended identities: the resolved
citrulline structure is the S stereoisomer, and the resolved ferulic acid is E.
Review the solanine and azadirachtin structures/components against the intended
material. Neem extracts and formulations need their own evidence attribution.

## Local audit trail

The ignored checkpoint is `.live-smoke/candidates-2026-10-15/`:

- `raw/pubchem/queries/` contains query-to-CID aliases; `raw/pubchem/<CID>/` contains
  properties, retrieval metadata, and original Toxicity JSON or a missing marker.
- `processed/annotations.parquet` retains source text and references;
  `compounds.parquet` retains selected identities and classifications;
  `measurements.parquet` retains normalized and review rows.
- `processed/coverage_matrix.parquet` and `coverage_groups.parquet` contain the
  coverage outputs. Each Parquet file has a `.metadata.json` sidecar recording
  input hashes, row count, timestamp, and package version.
- `observations.json` records per-compound counts, all 28 raw-file hashes, and
  successful offline cache reuse for all seven queries. Repeated tables and
  native Parquet round trips were equal, and raw hashes remained unchanged.

These local artifacts are available in the working checkout and are not part of
the committed example. Another computer can run the walkthrough to create its
own snapshots. PubChem content and counts may change; retain the retrieval
metadata and raw hashes when sharing a particular review.
