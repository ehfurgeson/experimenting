# ECOTOX ingestion implementation plan

Prepared 2026-11-05. **Status update 2026-11-10: source-inventory preflight
implemented and verified; full measurement adapter remains proposed.**
The official archive and dictionary were inspected; counts/core relationships and
archive CRCs pass. See the [tracked findings](../../analysis/FINDINGS.md#weekly-two-track-pilots--2026-11-10)
and [inventory contract](../../pipeline/docs/epa-chembl.md#ecotox-bulk-inventory-preflight).
The original detailed plan below records the pre-implementation assumptions; its
statements that the archive had not been inspected describe that earlier planning
stage. Normalization, approved source identity links and biological grouping remain
future work. This local, Git-ignored plan implements the
user's request to plan pipeline expansion. It does not authorize changes to
reviewed labels, historical caches, endpoint policies or model results.

## Purpose and research fit

Add reproducible ECOTOX ingestion to the maintained `pipeline/` package so that
the project can start with chemicals having ecological toxicology evidence,
reconcile their identities, and later identify natural compounds. Preserve plant
response evidence for the complementary literature-led track toward discovering
natural compounds with herbicidal properties.

The eventual comparisons distinguish natural tested low-response compounds,
natural plant-active compounds and conventional herbicide comparators. Ingestion
must retain evidence for these decisions without assigning those groups. Natural
occurrence, manufacturing origin, recognized herbicide use, measured plant
activity and non-target toxicity remain separate attributes.

ECOTOX ingestion is one dependency of Track 1, not completion of its LD50 analysis.
An ecological endpoint or plant-growth result must not become mammalian oral
LD50. The availability of eligible LD50 records must be measured after import;
CompTox/PubChem remain complementary sources. LD50 bins, natural-occurrence
integration, activity adjudication and model training are subsequent work.

## Starting point and verified source information

Repository capabilities to reuse:

- `agrotox.tables`: explicit Polars schemas, typed empty tables and strict readers.
- `agrotox.storage`: explicit paths, atomic JSON writing and table dependency hashes.
- `agrotox.normalize`, `units`, `coverage`, `analysis`: conservative values/units,
  policy matching, comparison records, summaries and review queues.
- `agrotox.epa_identity`: candidate/crosswalk/review pattern, while avoiding an
  assumption that every ECOTOX chemical already has a CID or approved DTXSID.
- `agrotox.epa_workflow`: offline evidence-to-analysis pattern. Its selected
  PubChem-cache prerequisite is inappropriate for discovering ECOTOX chemicals.
- Existing offline network-blocked tests and separate pipeline/analysis environments.

Official sources inspected on 2026-11-05:

1. [EPA resource hub](https://www.epa.gov/comptox-tools/ecotoxicology-ecotox-knowledgebase-resource-hub):
   describes literature-derived ecological effects and links the current guidance.
2. [ECOTOX home/download page](https://cfpub.epa.gov/ecotox/): advertises a ZIP
   containing pipe-delimited relational tables, field descriptions and relationship
   documentation. Its download information displays September 15, 2026. Verify the
   actual selected archive's release metadata rather than assuming this is its version.
3. [EPA ECOTOX 5.6 User Guide landing page](https://epa.figshare.com/articles/online_resource/ECOTOX_5_6_User_Guide/26764645/1?file=48991039).
4. [Terms Appendix entry point](https://cfpub.epa.gov/ecotox/help.cfm?sub=term-appendix).

The archive, actual table schemas and dictionary contents have **not** been
downloaded or inspected for this plan. Names below are proposed internal products,
not claims about exact EPA filenames or column names. Phase 0 must establish the
mapping from real source fields. No dedicated REST interface to the full ECOTOX
Knowledgebase has been established in this review. CTX does document an ecological
hazard endpoint; see the access assessment below. Do not equate its scope with
the bulk Knowledgebase or build against guessed website endpoints.

## Scope and architectural decisions

**First release:** import a local official bulk ZIP or an explicitly identified
extracted copy, inventory it, preserve source observations, reconcile identities,
normalize a bounded endpoint subset, and export audited offline products.
Manual download is a supported acquisition path. Website search CSVs and Explore
plot exports are different formats and are outside the first release; an arbitrary
CSV must not be accepted as a complete bulk snapshot.

**Later acquisition increment:** optionally download an explicit official archive
with bounded streaming, timeouts, retries and validated publication. Do not make
offline analysis depend on website availability or a CompTox API key.

**Identity independence:** retain a namespaced source key for every ECOTOX chemical,
including unresolved ones. Treat it as an external/source identity, not a CID.
The current canonical pipeline compound identity remains unchanged. Only approved
crosswalk matches attach observations to existing compound IDs. Source-level
inventory and evidence discovery must work without a pre-existing compound list.

**Separate source adapter:** ECOTOX lives under its own namespace, not under
`raw/comptox/`. Do not inject bulk rows into `epa_hazard.parse_toxval` or invent
CompTox response envelopes/experimental flags.

**Preserve unsupported evidence:** concentrations, dose-response estimates,
observed response percentages, biomass changes and lesion measurements are distinct.
Keep original fields even when the shared comparison schema cannot represent them.
Avoid a broad shared-schema refactor to make the first import possible.

## Planned storage and products

Proposed layout, finalized after schema inspection:

```text
<data-root>/raw/ecotox/<snapshot-id>/
  source.zip                 # or manifest referencing preserved extracted files
  manifest.json              # version, URLs, scope, hashes, sizes, file inventory
  tables/                    # validated extraction; retain original member names
<new-output-root>/
  manifest.json
  chemicals.parquet
  identity_candidates.parquet
  identity_crosswalk.parquet
  observations.parquet
  measurements.parquet
  coverage.parquet
  audit.parquet
  review_queue.parquet
  comparison_records.parquet # only admitted, mapped observations
  compound_summary.parquet
  group_summary.parquet
```

Persist dictionary/reference/species tables or their normalized equivalents as
required to reconstruct observations. Every derived table gets the existing hash
sidecar. A final manifest identifies the successfully completed bundle; individual
table/sidecar writes are not assumed to form a transaction. Use fresh output roots,
reject input/output overlap and never rewrite a frozen bundle to refresh a source.

Source observations retain the native chemical/test/result/reference identifiers
where available, original codes and decoded labels, raw row or reconstructable
source locator, species/life stage, effect/endpoint, exposure medium and method,
formulation, duration, values/bounds/qualifiers/units, quality comments, references,
and snapshot identity. Keep exposure duration distinct from observation time.
Unknown optional fields remain null; preserve source sentinel text separately.

Use source IDs plus snapshot identity to identify immutable source occurrences.
Do not hash only compound/value/context: distinct experiments can have equal values.
Any cross-release lineage key is separate and requires verified source-ID stability.

## Implementation sequence and acceptance gates

### Phase 0 — Freeze a representative source and specify its contract

0. Complete the CTX access/overlap preflight below. A CTX ecological-hazard response
   is a complementary source, not a substitute for inspecting the full export.
1. Obtain an official ZIP into a new local evidence directory; retain the exact
   URL, retrieval time, advertised release, SHA-256, size and supplied documentation.
2. Inventory actual table names, encodings, headers, delimiters, quoting rules,
   null/sentinel codes, identifiers, dictionary relationships and field types.
3. Identify result grain and verify join cardinalities among chemicals, species,
   tests, results, references and any bridge tables. Do not flatten one-to-many
   joins in a way that multiplies experimental observations.
4. Select a small real-record smoke subset spanning aquatic and terrestrial/plant
   evidence, qualified values, missing context and unsupported endpoints/units.
   Record any unavailable case instead of inventing measured evidence.
5. Write a source-field mapping, supported-release rule and row-count reconciliation.
   Design small synthetic fixtures from the documented format for tracked tests.

**Gate:** actual schema and result identity are documented; representative joins
reconcile; source-versus-derived fields are explicit. Resolve format uncertainty
here before committing to an adapter interface.

### Phase 1 — Import, validate and publish local snapshots

Proposed home: `pipeline/src/agrotox/sources/ecotox.py`, with narrowly scoped
storage helpers in `storage.py` if useful.

- Import local ZIPs/extracted bundles without network calls or source mutation.
- Validate required tables/headers and file hashes before declaring a snapshot complete.
- Reject malformed archives, unsafe extraction paths, symlinks, duplicate/conflicting
  members, missing relations, corrupt content and unsupported required schemas.
- Bound expanded bytes/member counts; stream or use lazy scans instead of loading
  the full relational export into Python lists. Keep identifiers as strings.
- Separate incomplete staging from a validated snapshot; interrupted imports must
  be resumable or fail clearly, never appear as an empty successful dataset.
- Allow harmless extra columns while preserving them; missing required fields or
  incompatible release changes fail explicitly.

**Gate:** a valid local bundle imports deterministically; invalid/incomplete input
cannot publish a completed manifest; original bytes and hashes remain unchanged.

### Phase 2 — Parse native evidence and reconcile chemicals

Proposed homes: `parsers/ecotox.py`, `ecotox_identity.py`; explicit schemas in
`tables.py` following existing ownership.

- Produce typed chemical and observation tables at the verified source grain.
- Keep one-to-many references as nested/bridge evidence rather than duplicate results.
- Preserve unknown dictionary codes with review reasons; never silently drop a row.
- Validate primary/foreign keys. Distinguish documented optional missing relations
  from corrupt/dangling required references.
- Build candidates and crosswalks to supplied canonical identities. Names and CAS
  are retrieval/matching clues; neither alone establishes exact structure.
- Separate exact-structure, connectivity-only, identifier-only and name-only evidence;
  retain conflicts, mixtures, salts/esters and unspecified stereochemistry for review.
- Preserve unresolved source chemistry in inventory; require affirmative identity
  approval before transferring results onto a canonical compound.
- Keep any live PubChem/CompTox enrichment as a separate cached acquisition action.

**Gate:** every source result is accounted for; unresolved identities remain visible;
ambiguous mappings cannot attach measurements to the wrong existing compound.

### Phase 3 — Normalize a bounded endpoint subset

Proposed home: `ecotox.py` for source-specific normalization and compatibility mapping.

- Decode endpoint/effect/species/unit codes using the frozen dictionaries.
- Initially map only genuinely compatible LD50/LC50/EC50 measurements with sufficient
  context. Keep other endpoints in native evidence pending explicit extensions.
- Distinguish EC50 effect types; a growth EC50 and an immobilization EC50 cannot
  silently become interchangeable potency observations.
- Preserve measured versus nominal exposure basis when supplied. Convert only
  explicit compatible units through existing helpers; do not infer aqueous ppm,
  molecular weight, application-rate conversion or exposure duration.
- Preserve inequality/range semantics; missing or unsupported values remain reviewable.
- Separate observed response, fitted effect estimates and model predictions using
  the verified source documentation. Literature extraction is provenance, not proof
  of uniform study quality or a license to tag every estimate as directly observed.
- Produce complete/partial/failed statuses with specific reasons. Admission to
  shared analysis also requires approved identity and eligible formulation/context.
- Use source-specific companion fields/tables for context absent from the shared
  schema. Default to availability-only summaries if essential potency context
  cannot be retained and constrained safely; extend matching/schema only in a
  separately tested change. No metadata-stripping shortcut to potency summaries.

**Gate:** unit/qualifier/context round-trips are auditable; unsupported responses
remain visible; plant activity and natural-origin labels are never inferred.

### Phase 4 — Add an offline workflow and explicit examples

Proposed homes: `ecotox_workflow.py`, `examples/import_ecotox.py` and
`examples/analyze_ecotox.py`. These names and command interfaces are proposals.

- Provide source-first inventory across the snapshot and an optional selected-cohort
  mode. Record the selection/query scope and include selected compounds with no hits.
- Build native evidence, normalized measurements, coverage, comparisons, audit and
  review products from validated raw inputs and an explicit crosswalk/policy.
- Record denominators at source-chemical, resolved-compound, result and eligible-result
  levels. Retain imported rows that cannot enter canonical analysis.
- Distinguish unassessed/unresolved/incomplete scope from an assessed absence of
  eligible matches. Zero coverage never means zero toxicity or tested inactivity.
- Start with source-specific coverage; leave existing PubChem/EPA union flags and
  historical notebook outputs unchanged. Any later three-source union must implement
  explicit assessed-scope and null semantics.
- Use fresh, explicit ECOTOX policy examples. Prioritize existing trout/Daphnia
  contexts if available; add plant/algal policies only after effect, duration and
  unit mappings can express the intended claim. Do not broaden defaults silently.
- Keep ECOTOX separate in summaries until cross-source duplicate-study handling is
  specified. Existing equal-value consolidation does not establish study independence.
  Export possible publication/test overlaps with CompTox/PubChem for review and retain
  all provenance. Uncertain duplicate matches do not justify deleting observations.

**Gate:** both source-first discovery and selected-cohort reporting work offline;
results trace to raw records and approved mappings; existing workflows regress cleanly.

### Phase 5 — Verify, document and freeze the first real-data checkpoint

Add focused tests beside the existing pipeline tests:

| Test area | Required cases |
| --- | --- |
| Snapshot import | Valid ZIP/extracted input, corruption, unsupported schema, missing members, extraction bounds, unsafe paths, interruption, no overwrite |
| Relational parser | Typed empty tables, repeated equal results, multiple references, join fan-out, duplicate keys, optional/required missing relations, unknown codes |
| Identity | Approved exact match, name/CAS-only ambiguity, stereochemical conflict, mixture, unresolved source ID, multiple mappings, no network |
| Normalization | Unit factors, aqueous-context requirement, bounds/inequalities, missing duration, effect distinctions, nominal/measured basis, unsupported plant response |
| Workflow | Source-first inventory, selected zero-hit rows, null assessment, excluded identity, stable IDs/hashes, policy exclusion, preserved source bytes |
| Compatibility | Existing EPA/PubChem outputs and label behavior unchanged; shared-schema extensions covered if introduced |

Run focused tests first, then `uv run --project pipeline pytest pipeline/tests -q`
and `uv run --project pipeline ruff check pipeline`. Run the analysis suite and
analysis Ruff when analysis/shared contracts are affected. Keep tests offline in
the existing pipeline environment; do not combine lockfiles or depend on live EPA.

Separately run the real-record smoke subset, manually compare results against its
source tables, reconcile counts through every join/filter and verify product hashes.
Record the command, release, inputs, exclusions, limitations and completion status.
Do not treat synthetic fixtures as measured research data.

Update the owning tracked documentation in the same implementation increment:
`pipeline/docs/ecotox.md` (new source contract), `pipeline/docs/decisions.md`,
pipeline quickstart/index links and `docs/data.md`. Add a dated findings/result
inventory entry only when a real-data checkpoint exists. Update local evidence
and next-step notes as implementation status changes.

**Gate:** reproducible frozen smoke products, passing relevant offline checks,
explicit limitations and a usable clean-clone guide for importing an acquired bundle.

### Phase 6 — Optional explicit-download client

After local ingestion is stable, add a documented official-download action with
streaming, connection/read timeouts, bounded retries and byte limits. Preserve the
requested/final URL, retrieval metadata and content hash; validate redirect hosts,
archive content and completion before publishing. Test with mocked responses.
Refresh into a new snapshot ID. Import and analysis continue to work without it.

## Definition of done and handoff

The first release is complete after Phases 0–5 when an official local snapshot can
produce traceable native evidence and conservatively mapped measurements offline,
including unresolved chemicals and unsupported results, with explicit identity,
coverage and review states. Phase 6 is optional and does not block that release.

The first bounded development increment is **Phase 0 plus the local snapshot
import contract**. Avoid implementing all phases as one large change.

Follow-on research uses the chemical inventory for natural-occurrence matching and
the evidence exports for endpoint feasibility. It must still define LD50 bins,
review plant-activity controls, resolve duplicated studies and establish the three
comparison groups. No classifier performance, safety claim or universal inactive
label is an acceptance criterion for ingestion.

## API access assessment and complementary CTX opportunities

Added 2026-11-05 following the user's API-key question. This section compares the
documented CTX capabilities with the maintained client's methods, not with every
field that might appear in historical raw JSON. Benefits are project-specific
judgments; availability of a domain does not guarantee data for every compound.

### Does the current key cover ECOTOX?

The repository's `COMPTOX_API_KEY` is sent as `x-api-key` to
`https://comptox.epa.gov/ctx-api`. EPA describes an individual key for the CTX API
family, whose four domains are Chemical, Hazard, Bioactivity and Exposure.
The current key is therefore expected to authenticate those CTX domains, subject
to its validity and service permissions. This planning task has **not** sent
authenticated requests or tested this particular key. Do not describe its current
entitlements or endpoint availability as live-verified.

There are two different access routes:

| Route | Authentication and meaning |
| --- | --- |
| CTX ecological-toxicity hazard endpoint | The official ctxR Hazard guide documents `get_ecotox_hazard_by_dtxsid()`, alongside a general hazard function returning human and ecological data. Use CTX authentication; verify deployed route/schema before implementing. The word ecotox in a function name does not establish full Knowledgebase coverage. |
| Full ECOTOX Knowledgebase download | The public official site advertises a bulk archive without a CTX-key requirement. The planned local import requires no key. The downloader should not send a CTX credential to the download host. |

The pipeline already calls `/hazard/toxval/search/by-dtxsid/{dtxsid}`. Consequently,
ecological records may already be present in raw ToxVal caches even if the current
analysis cannot normalize or admit them. A dedicated ecological endpoint could be
a filtered/alternative view rather than new evidence. Inspect source provenance,
record IDs and contexts before counting incremental coverage.

Sources: [EPA CTX access overview](https://www.epa.gov/comptox-tools/computational-toxicology-and-exposure-apis),
[EPA domains](https://www.epa.gov/comptox-tools/computational-toxicology-and-exposure-apis-data-domains),
[official ctxR Hazard guide](https://usepa.github.io/ctxR/articles/Hazard.html),
[ECOTOX download page](https://cfpub.epa.gov/ecotox/).

### Required access/overlap preflight

Before expanding the client:

1. Save the relevant deployed API documentation/schema and its date/hash. Distinguish
   deployed operations from development-branch code and older client examples.
2. Inspect existing raw hazard and property caches for ecological/fate records and
   source-specific fields that the parser or policies currently exclude.
3. In an explicit bounded live check, reuse the key only in headers to the approved
   CTX host. Test a few already approved DTXSIDs with known evidence. Log endpoint,
   status and counts without request headers, credential values or secret-bearing
   exception output. Do not add a key to any source/download URL.
4. Record 401/403, rate limits, missing data and service failure as separate states.
   Authentication failure is not no evidence. Offline tests use mocked responses.
5. Compare current ToxVal, CTX ecological-hazard and bulk ECOTOX records by source
   identifiers and publication/test context. Report overlap, metadata richness,
   unmatched records and uncertainty; equal counts do not prove equivalence.
6. Keep bulk ingestion as the source-first discovery route. Add a CTX ecological
   adapter only if it supplies useful access or metadata beyond existing retrieval.

**Preflight deliverable:** a small frozen capability/overlap report and sanitized
response snapshots, with actual supported endpoints and a decision about whether
an additional CTX adapter is warranted. This is implementation work, not a check
already performed during planning.

### What CTX exposes beyond current collection

The maintained `ComptoxClient` currently implements exact search, chemical details,
per-substance ToxCast data, individual assay annotations, ToxVal hazard values and
experimental/predicted properties. TEST extraction filters the saved predicted
properties. No Exposure-domain client or dedicated fate/list/genotoxicity client
is present. The following are candidate additions, not promised new coverage.

| Resource not separately collected | Current gap / overlap to check | Benefit to this project | Priority |
| --- | --- | --- | --- |
| Environmental fate and transport | No dedicated fate operation; some related properties may already be in property responses | Compare persistence, mobility and accumulation evidence where supplied; useful for evaluating natural herbicide candidates beyond acute mammalian hazard | High after core ingestion |
| Chemical lists and list membership | No list discovery/member retrieval | Expand traceable comparator cohorts and locate relevant curated collections; inspect list purpose/version rather than converting membership into an origin/activity label | High for cohort building |
| Genotoxicity summaries and detailed reports | No dedicated genetox acquisition | Identify safety concerns not represented by LD50; preserve conflicting and assay-specific findings rather than a single safe/unsafe flag | High for candidate review |
| Cancer and skin/eye hazard resources | No dedicated operations; some related evidence may exist in ToxVal | Add longer-term hazard context and handling concerns, especially for contact-active candidates; use endpoint-specific evidence | Medium–high for prioritization |
| ToxRefDB study/dose-response data | Current hazard acquisition reads ToxVal, which includes ToxRef summaries; richer study access needs deployed-schema verification | Improve species, dose, duration and effect review; potentially support more defensible chronic comparisons | High if richer data are exposed |
| IRIS, PPRTV and HAWC assessment links | No dedicated link retrieval | Find primary assessments and study context; links are research leads, not automatically ingested study results | Medium–high |
| CPDat product/use categories, ingredient fractions and recorded functional uses | Entire Exposure domain absent | Document real-use/formulation context and prioritize exposure review; product use does not establish herbicidal efficacy or natural occurrence | Medium |
| Predicted functional uses (QSUR) | Not collected | Generate search leads for possible pesticidal/related uses; predictions must not supply training labels | Low–medium |
| Exposure/toxicokinetic resources (MMDB, SEEM, httk-related data) | EPA's Exposure repository lists these sources; verify currently deployed operations and fields | Environmental monitoring can add occurrence context; modeled exposure/internal-dose information can later help hazard interpretation. These do not directly distinguish plant actives from negatives | Later; hypothesis-dependent |
| Full assay inventory and assay-centered/batch bioactivity retrieval | Existing retrieval is compound-centered with annotations for encountered assays | Find relevant assay panels, improve coverage diagnostics and targeted mechanistic review; ToxCast activity does not prove plant efficacy or direct binding | Medium |
| Synonyms, structure files, MS-ready lookup and broader/batch searches | Exact search/details exist; specialized routes absent | Resolve literature names and support future analytical identification; keep MS-ready/standardized structures separate from exact tested identities | Synonyms: medium; MS-ready: later |

The scope statements above are supported by the
[official Chemical guide](https://usepa.github.io/ctxR/articles/Chemical.html),
[Hazard guide](https://usepa.github.io/ctxR/articles/Hazard.html),
[ctxR function inventory](https://usepa.github.io/ctxR/reference/index.html),
[EPA Hazard API repository](https://github.com/USEPA/ccte-api-hazard),
[EPA Exposure API repository](https://github.com/USEPA/ccte-api-exposure) and
[EPA domain catalog](https://www.epa.gov/comptox-tools/computational-toxicology-and-exposure-apis-data-domains).
The Exposure repository lists a broader source inventory than older client pages;
verify deployment rather than assuming all operations exist on the public service.

### Sequencing recommendation

Complete the ECOTOX contract and access/overlap preflight first. Next prioritize
chemical-list discovery, a dedicated fate audit/adapter and richer hazard evidence
that materially improve cohort definition or candidate assessment. Add Exposure
resources only for a stated exposure question. Synonym/structure enrichment can be
added when concrete identity failures justify it.

These are separate follow-ups, not requirements to implement every CTX domain as
part of ECOTOX ingestion. None replaces literature review of natural occurrence
or experimentally supported plant-active/low-response groups.


## Bounded selected-cohort checkpoint — 2026-11-11

Source-first inventory now supports complete selected-cohort native/slot import
and explicit source-context normalization policies for LD50/LC50/EC50. The frozen
104-source cohort has 79,171 native results, and the strict aquatic policies yield
28 trout and 13 Daphnia source-context matches. Canonical source identities remain
unapproved. This is a bounded implemented increment; broader ingestion, approved
canonical mappings and biological grouping still depend on the source/scientific
review gates above. See the [tracked checkpoint](../../analysis/FINDINGS.md#evidence-and-comparable-toxicity-expansion--2026-11-11).
