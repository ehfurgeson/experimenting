# Local NICE and NPASS import audit

The subsequently supplied `data_imports/structural_features.parquet` adds a
28th file. The [original panel rerun](reviewed-selection-results.md) records
its fingerprint, row coverage, both model scores and analogue search.

The inventory covers 27 files, including two source descriptions, 12 NICE
workbooks, two NICE archives and 11 NPASS tables. File hashes, workbook tab
counts, and nested archive member names and row counts are in the generated
`experiments/import-expansion/inventory.jsonl`. Input archives stayed intact.

## NICE

Workbook counts below assume one heading row per data tab. The inventory also
counts notes and metadata. Archive record counts exclude headers.

| Source | Data rows | Previous use and role |
| --- | ---: | --- |
| Acute oral | 16,721 | ICE 4.1, created 2024-07-29. The local workbook's SHA-256 matches the public copy fetched for this audit. Release metadata and count agree with the original A source. Provisional rat acute oral target input. |
| Acute dermal | 2,692 | No prior local ingestion found. Separate acute dermal evidence. |
| Acute inhalation | 5,505 | No prior local ingestion found. Preserve duration and concentration-based endpoint. |
| ADME parameters | 4,037 | No prior local ingestion found. Measured binding and clearance by species, with sparse compound coverage. |
| Cancer | 10,351 | No prior local ingestion found. Preserve source classifications and bioassay contexts. The local data-tab count differs by one from the source description. |
| DART | 138,326 | No prior local ingestion found. Developmental and reproductive endpoints across study and dose contexts. |
| Endocrine | 16,623 in vitro / 2,270 in vivo / 16,416 integrated | No prior local ingestion found. Preserve the three evidence types and avoid counting an integrated call as an independent experiment. |
| Eye irritation | 3,028 | No prior local ingestion found. Separate local-effect evidence. |
| Skin irritation | 6,259 in vitro / 2,058 in vivo | No prior local ingestion found. Separate model/test-system evidence. |
| Skin sensitization | 8,837 in vitro / 13,945 in vivo | No prior local ingestion found. Retain assay system and sensitization context. |
| Exposure predictions | 479,584 | No prior local ingestion found. Tab rows are wide records, distinct from the provider's long-format endpoint count. SEEM3 predictions depend on exposure assumptions. |
| Functional use | 264,847 | No prior local ingestion found. Preserve curated and predicted use categories independently. Neither establishes biological origin or plant efficacy. |
| ChemicalTaxonomies | 1,125,205 | No prior local ingestion found. ClassyFire provides predicted structural taxonomy. |
| cHTS | 13,018,233 assay/chemical rows | The repository already consumes EPA ToxCast through CTX, but no use of this NICE archive was found. Shared invitrodb lineage means directional agreement cannot count as independent confirmation. |

The cHTS import includes 350,664 flag-omit rows, 1,865,056 technological
interference records, chemical QC, annotation maps, 1,388 cytotoxicity
mappings and 9,614 chemical-specific cytotoxicity-burst estimates. The core
workbook/readme identifies ICE 5.1, created 2026-10-30. Its assay/QC files belong
together when interpreting results. No cHTS call, exposure prediction, chemical
taxonomy or functional-use category was used as an oral LD50 or plant response.

Prior evidence: [ICE cohort checkpoint](modeled-evidence-2026-11-12.md),
[EPA and ChEMBL adapters](../../pipeline/docs/epa-chembl.md).
Provider: [NICE dataset descriptions](https://ice.ntp.niehs.nih.gov/DATASETDESCRIPTION).

## NPASS

| Source | Data rows | Previous use and role |
| --- | ---: | --- |
| Natural-product structure | 203,390 | Prior full-key validation, catalog overlay and identity holds. |
| General information | 204,022 | Prior identifier and source-name context. One delimiter-only row is excluded. |
| Compound–species pairs | 1,117,269 | Prior occurrence-link audit. Taxon and reference links require interpretation in the original study. |
| Species information | 48,940 | Prior taxon lookup and occurrence context. |
| Activities | 1,048,756 | Prior assay and plant-organism inventory, including binding-evidence review. |
| Targets | 8,764 | Prior target ID and target organism context. |
| Toxicity | 34,975 | Prior toxicity audit and permissive expansion with explicit missing-context assumptions. |
| Coculture | 869 | No prior ingestion found. Preserve producer and inducer roles. |
| Elicitation | 382 | No prior ingestion found. Preserve organism, elicitor and source reference. |
| Engineered organism | 811 | No prior ingestion found. Distinguish engineered production from wild-type occurrence. |
| Symbiont | 491 | No prior ingestion found. Host association and producer attribution need separate review. |

The overlapping NPASS release and reported cardinalities agree with the prior
sprint. The old raw files and historical manifests are unavailable in this
checkout, so the audit cannot attest that the original and local hashes match.
The four production-context tables identify how compounds were obtained. By
themselves they say nothing about plant inhibition, acute oral toxicity, or
independent replication of another catalog's organism link.

Prior evidence: [November data sprint](data-sprint-2026-11-17.md),
[accepted experiments](accepted-sprint-2026-11-17.md).
Provider: [NPASS downloads](https://bidd.group/NPASS/downloadnpass.html).
