# Data-first sprint checkpoint — 17 November 2026

**AI experimental source audit.** This pass enriches cohort identity and identifies
reviewable evidence. New database links are not independently reviewed occurrence,
new accepted activity labels, study-independent LD50 measurements or safety claims.
Original A/B releases, curated inputs, Li 7b's identity hold and accepted policies persist.

## Catalog and occurrence yield

The unchanged baseline contains 4,234 measured A full structures, 43,128 CATMoS
teacher B structures and 176 prepared selection rows (116 selected natural products,
60 selected herbicides). Selection membership is independent of verified occurrence.

| Source / tier | A exact full-key matches | B exact full-key matches | Selection exact matches |
| --- | ---: | ---: | ---: |
| NPASS 3.0 catalog | 793 | 3,135 | 114 |
| COCONUT November 2026 catalog | 1,478 | 6,263 | 119 |

COCONUT matches **34.9% of A**; either catalog matches **1,617 / 4,234 (38.2%)**.
Both match 654, COCONUT alone 824, NPASS alone 139. Connectivity-only candidates
remain separate: A has 51 NPASS and 287 COCONUT candidates. No unmatched compound
receives a synthetic-origin label.

All 738,793 COCONUT structures were checked against their supplied keys:
734,522 valid records / 724,233 unique full keys, 4,247 multicomponent records,
20 provider-key conflicts and four invalid structures. NPASS has 203,390 structure
records / 203,389 source IDs; one exact repeated ID is logged. There are 189,549
valid unique full keys, 10,160 key conflicts, 2,167 multicomponent records,
1,418 invalid structures and one missing derived key. Conflicts are held rather
than choosing the provider or recomputed key. Unspecified stereochemistry persists.

Of 1,117,269 NPASS occurrence rows, 125,086 link to cohort keys, including held
identity candidates. There are 23,294 valid taxon/publication-linked rows covering
1,750 cohort structures, **476 in A**. Those links are database assertions awaiting
primary review. Six A structures map to the already adopted occurrence evidence;
all 19 previously adopted occurrence structures resolve in the prepared identity map.
Repeated source database/publication links are not independent corroborating studies.

## Toxicity eligibility and novelty

NPASS's 34,975 toxicity records include 8,898 LD50 rows, 4,179 explicitly rat LD50.
Its actual export lacks route, acute context and experimental/predicted status.
All remain review-only; the complete raw fields and exclusion reasons are retained.

Three bounded ToxValDB v9.7.0 workbooks contain 116,596 rows:

| Table | Rows | Endpoint-eligible exact | Endpoint-eligible censored |
| --- | ---: | ---: | ---: |
| TEST source | 1,077 | 663 | 303 |
| ChemIDplus | 44,277 | 0 | 0 |
| ECHA IUCLID | 71,242 | 4,138 | 7,094 |

Eligibility requires explicit experimental, rat, oral, acute, LD50, finite positive
mg/kg, supported qualifiers, record-level references and no QC failure.
ChemIDplus's experimental flag is `undetermined`, so it does not qualify. TEST
contains source-marked experimental rows; its source name alone does not make
these predictions or independent measured evidence.

Local unambiguous DTXSID links yield **445 candidate new exact-value structures**
and **884 additional censored-only structures** beyond A. Tested-material form
and original-study independence remain unresolved; these are not admitted labels.
**Confirmed net-new eligible structures: zero. Independent-study novelty: unknown.**
There are 753 possible mirror rows against A by reference or value/qualifier;
these flags do not adjudicate duplicates, and lack of a flag does not prove novelty.

## Plant evidence and three-axis overlap

The unchanged ECOTOX 2026-09-15 archive yields 73,317 non-algal growth, germination
or biomass result records in 25,333 discovery strata. Non-algal includes aquatic
vascular plants; habitat, test medium, formulation, effect direction, dose and
primary methods still need review. Complete native result/test/reference/species
JSON is retained in compressed output. NOEC, missing effects and omitted compounds
are not converted into tested-low labels.

NPASS's 1,048,756 activity rows yield 2,670 plant-organism records with unresolved
phenotype, 469 plant-protein mechanism records and 546 tissue/other records.
No row supplies enough explicit endpoint description for the narrow phenotype
text filter. This is a metadata limitation, not evidence that no plant phenotypes
exist. Target IDs are not assay IDs. Missing taxonomy IDs never join as plant hits.

The accepted policies were rerun through `activity_preflight.py`: K1998 5 high/0 low,
Okamoto 4/0, Li 11/10, He 29/21. The first two lack both-class support; Li and He
lack class-bearing scaffold support. No thresholds were lowered or policies pooled.
No new model was trained.

Within A, **five** structures have catalog membership plus an already adopted
plant response. **One** has NPASS taxon/publication support plus that response,
and **one** has already adopted occurrence plus that response. These are distinct
evidence tiers. The small accepted intersection, sparse comparable controls and
unresolved tested forms remain the binding constraints.

## Targeted phenotype follow-up

Two ChEMBL searches returned 184 lettuce functional assays and 15 Arabidopsis
assays mentioning roots. Six selected complete snapshots contain **40 observations,
28 source compounds and five publications**, retaining every record, assay
description and qualifier. These remain review leads. The two podolactone assays
each include 12 tested materials, four inhibition bounds above 40%, three below
20%, and five without a resolved numerical bound. Cultivars remain separate.

The [primary paper](https://doi.org/10.1021/jf990321y), available as
[author-hosted parsed text](https://bibrepo.uca.es/articuloscientificos/31850200.pdf),
raises two holds. Its positive comparator is formulated Logran (terbutryn plus
triasulfuron), whereas ChEMBL maps it to one chemical. Its Table 1 summarizes
activity across tested concentrations without a single-dose heading, so assigning
every bound to the database's 0.1 mM description needs reconciliation. Excluding
the comparator leaves three over-40 and three under-20 bounds per cultivar, still
held. The methods describe buffered Petri dishes, darkness, 25 C, five days for
lettuce, parallel controls and 100 seeds per condition. Sample stereochemistry
requires review against original structures.

This review used web-parsed text. Direct PDF attempts returned 403 and screenshots
failed with a cache miss; visual verification is unavailable. All 24 podolactone
rows agree with molecule API keys computationally, but tested-product form and
dose attribution remain unresolved. The other 16 observations retain derived
keys without separate provider verification. No new label or model was adopted;
no provider-verified, form-unheld podolactone identity matches A.

## Local products and reproduction

Run root: `experiments/data_acquisition/2026-11-17-data-sprint/` (ignored).
Canonical products use `baseline/`, `npass-v3/`, `coconut-v2/`, `toxval-v2/`,
`plant-inventory-v2/`, `npass-context-v1/` and `accepted-preflight-v1/`.
`catalog-cross-v1/` completes the full NPASS-to-COCONUT overlay: 173,475 distinct
valid NPASS full keys match exactly, 15,814 have connectivity-only candidates,
and 260 have neither; 13,746 NPASS source IDs remain on identity holds.
The targeted source package is `chembl-assays-v1/` with `chembl-review-v1/`;
`reports-v3/` is the final synthesis including that review.
Preliminary and aborted attempts remain distinct. No historical manifest was rewritten.

The [workflow contract](data-sprint.md) owns commands, inclusion policy and output
schemas. The synthesis exports the full cohort overlap with missingness/tier fields,
the 176-row selection evidence queue, source waterfall, audit sample and two
scientific plots. Queue priority reflects evidence completeness, not safety or
predicted herbicidal efficacy. Source-selected LD50 distributions have no causal
or population interpretation. B contributes only teacher-derived screening coverage.

Sources: [NPASS downloads](https://bidd.group/NPASS/downloadnpass.html),
[COCONUT downloads](https://coconut.naturalproducts.net/download),
[EPA ToxValDB release](https://doi.org/10.23645/epacomptox.20394501).
Raw source URLs, UTC times, versions, license qualifications, failures, native and
stored hashes, output hashes and executed code snapshots remain local. Source text
is losslessly compressed because local disk space is limited. Byte-identical new
working products can share storage without changing bytes or manifest hashes.

## Verification and stop decision

The final locked suites pass: **352 analysis tests**, **1,078 pipeline tests**,
Ruff for both components and Git whitespace checks. Source qualification tests
cover unknown experimental status, censoring, ambiguous identifier links, stereo
and salt holds, missing taxonomy sentinels, source formulation and dose-summary
holds, malformed exports and changed upstream inputs. The two scientific plots
were rendered and visually inspected. Source PDF visual verification remains
unavailable; the review explicitly retains that limitation.

The independent local `verify_run.py` checks 53 canonical product hashes and their
upstream inputs, recomputes A catalog intersections and the 445/884 candidate
novelty counts, checks the endpoint contract in all 12,198 ToxValDB candidate rows,
reparses 23 sampled catalog identity pairs, and confirms unknown new plant labels.
It records `verification.json`. These checks verify arithmetic, identities and
provenance integrity, not original-study independence or biological validity.

Stop the broad ingestion pass under the sprint's evidence-yield rules. NPASS adds
catalog/occurrence links but cannot qualify toxicity context; the bounded ToxValDB
pass reaches tested-form/lineage holds; the selected primary plant series reaches
formulation, dose-attribution and source-access holds. No new model has sufficient
newly qualified evidence. The next work is the bounded review queue and primary
source reconciliation, rather than claiming more usable labels from bulk counts.
