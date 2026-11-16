# Frozen result and export inventory

Inventory inspected **2026-11-02**. Paths below `analysis/outputs/` are local,
ignored and absent from a clone. Dates in folder names are run identifiers;
only manifest timestamps establish actual generation times. Exact inputs/settings,
code/lock versions and output hashes live in the listed manifests. These entries
record provenance and workflow ownership, not a new scientific acceptance review.

For label review the maintained guide explicitly designates
`chembl-review-2026-10-29-final/` and `chembl-researcher-handoff-2026-10-29/`.
The feature-combination checkpoint and local delivery report point to the two
`ablations-*-2026-10-29-final/` bundles. This identifies the intended references;
no earlier bundle is declared obsolete. No activity model is accepted by this index.

## Structural, acquisition and review bundles

Run IDs below are paths relative to `analysis/outputs/`. Reproduction commands and
required flags are in the [screening guide](../analysis/docs/structural-screening.md)
and [diagnostic/review guide](../analysis/docs/diagnostics-review.md); use a fresh
output directory. The local handoff/audit generators are not present in a clone.
Historical discovery, manual curation and exact API responses cannot be inferred
from a generic acquisition command. Inspect each manifest before claiming equivalence.

| Run ID / path | Date in ID | Question / reproduction tool | Input bundle / product | Manifest | Status / supersession | Report / context |
| --- | --- | --- | --- | --- | --- | --- |
| `ablations-fixed-2026-10-29/` | 2026-10-29 | Compare feature profiles / regularization; `analysis/ablations.py` | `analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet` | `manifest.json` | Exploratory earlier export; superseding run unconfirmed | [feature combinations](../analysis/docs/feature_combination_check.md) |
| `ablations-fixed-2026-10-29-final/` | 2026-10-29 | Compare feature profiles / regularization; `analysis/ablations.py` | `analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet` | `manifest.json` | Exploratory; final variants cited by feature checkpoint; superseding run unconfirmed | [feature combinations](../analysis/docs/feature_combination_check.md) |
| `ablations-nested-2026-10-29/` | 2026-10-29 | Compare feature profiles / regularization; `analysis/ablations.py` | `analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet` | `manifest.json` | Exploratory earlier export; superseding run unconfirmed | [feature combinations](../analysis/docs/feature_combination_check.md) |
| `ablations-nested-2026-10-29-final/` | 2026-10-29 | Compare feature profiles / regularization; `analysis/ablations.py` | `analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet` | `manifest.json` | Exploratory; final variants cited by feature checkpoint; superseding run unconfirmed | [feature combinations](../analysis/docs/feature_combination_check.md) |
| `chembl-2026-10-28/` | 2026-10-28 | Bounded plant-assay acquisition; `pipeline/examples/fetch_chembl_assay.py` (per assay); historical discovery bundle needs its recorded selection | `analysis/outputs/chembl-2026-10-28/discovery.json`<br>`analysis/outputs/chembl-2026-10-28/raw/` | `manifest.json` | Frozen raw evidence; not reviewed labels; superseding run unconfirmed | [structural validation](../analysis/docs/structural_validation_check.md) |
| `chembl-pagination-check-2026-10-28/` | 2026-10-28 | Acquisition pagination check; Acquisition diagnostic; no exact command established | Not established in a root manifest; raw pagination diagnostic | None at bundle root | Diagnostic; preserve raw snapshots; superseding run unconfirmed | [structural validation](../analysis/docs/structural_validation_check.md) |
| `chembl-researcher-handoff-2026-10-29/` | 2026-10-29 | Human label adjudication working pack; Local `notes/build_label_research_handoff.py` | `analysis/outputs/chembl-review-2026-10-29-final/label_review_template.csv`<br>`analysis/outputs/chembl-review-2026-10-29-final/candidates.csv`<br>`analysis/outputs/chembl-review-2026-10-29-final/activity_review.csv`<br>`analysis/outputs/chembl-review-2026-10-29-final/manifest.json`<br>`analysis/outputs/chembl-2026-10-28/raw/` | `handoff_manifest.json` | Guide-designated working pack; policy unapproved, labels require review; superseding run unconfirmed | [label review guide](../analysis/docs/label_review_guide.md) |
| `chembl-review-2026-10-29/` | 2026-10-29 | Export frozen measurements and label worksheet; `analysis/review_assays.py` | `analysis/outputs/chembl-2026-10-28/raw/` | `manifest.json` | Earlier review export; supersession not established; superseding run unconfirmed | [label review guide](../analysis/docs/label_review_guide.md) |
| `chembl-review-2026-10-29-final/` | 2026-10-29 | Export frozen measurements and label worksheet; `analysis/review_assays.py` | `analysis/outputs/chembl-2026-10-28/raw/` | `manifest.json` | Guide-designated frozen template; superseding run unconfirmed | [label review guide](../analysis/docs/label_review_guide.md) |
| `chembl-review-2026-10-29-verified/` | 2026-10-29 | Export frozen measurements and label worksheet; `analysis/review_assays.py` | `analysis/outputs/chembl-2026-10-28/raw/` | `manifest.json` | Earlier review export; supersession not established; superseding run unconfirmed | [label review guide](../analysis/docs/label_review_guide.md) |
| `chembl-review-screen-2026-10-29/` | 2026-10-29 | Check unknown-label candidate screening; `analysis/screen.py` | `analysis/outputs/chembl-review-2026-10-29-verified/candidates.csv`<br>`analysis/outputs/chembl-review-2026-10-29-verified/label_review_template.csv` | `manifest.json` | Diagnostic; unknown-label worksheet is not training truth; superseding run unconfirmed | [label review guide](../analysis/docs/label_review_guide.md) |
| `chembl-review-screen-2026-10-29-final/` | 2026-10-29 | Check unknown-label candidate screening; `analysis/screen.py` | `analysis/outputs/chembl-review-2026-10-29-final/candidates.csv`<br>`analysis/outputs/chembl-review-2026-10-29-final/label_review_template.csv` | `manifest.json` | Diagnostic; unknown-label worksheet is not training truth; superseding run unconfirmed | [label review guide](../analysis/docs/label_review_guide.md) |
| `chembl-screen-2026-10-28/` | 2026-10-28 | Exploratory assay candidate screening; `analysis/screen.py` | `analysis/data/compound_traits.parquet`<br>`analysis/outputs/chembl-2026-10-28/candidates.csv` | `manifest.json` | Exploratory; no accepted activity model; superseding run unconfirmed | [structural validation](../analysis/docs/structural_validation_check.md) |
| `chembl-screen-2026-10-28-initial/` | 2026-10-28 | Exploratory assay candidate screening; `analysis/screen.py` | `analysis/data/compound_traits.parquet`<br>`analysis/outputs/chembl-2026-10-28/candidates.csv` | `manifest.json` | Exploratory; no accepted activity model; superseding run unconfirmed | [structural validation](../analysis/docs/structural_validation_check.md) |
| `imputation-audit-2026-10-29/` | 2026-10-29 | Audit missing-feature handling; Local `notes/audit_model_imputation.py` | Inspect `audit.json` and bundle README; no root manifest | None at bundle root | Diagnostic; not a production replacement; superseding run unconfirmed | [findings](../analysis/FINDINGS.md) |
| `stress-2026-10-28/` | 2026-10-28 | Scaffold sensitivity and shuffled labels; `analysis/stress.py` | `analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet` | `manifest.json` | Exploratory diagnostic; superseding run unconfirmed | [structural validation](../analysis/docs/structural_validation_check.md) |
| `structure-2026-10-27/` | 2026-10-27 | Structural selection discrimination; `analysis/screen.py` | `analysis/data/compound_traits.parquet` | `manifest.json` | Baseline / diagnostic; no accepted activity model; superseding run unconfirmed | [findings](../analysis/FINDINGS.md) |
| `structure-2026-10-27-verified/` | 2026-10-27 | Structural selection discrimination; `analysis/screen.py` | `analysis/data/compound_traits.parquet` | `manifest.json` | Baseline / diagnostic; no accepted activity model; superseding run unconfirmed | [findings](../analysis/FINDINGS.md) |
| `structure-2026-10-28-stress-baseline/` | 2026-10-28 | Structural selection discrimination; `analysis/screen.py` | `analysis/data/compound_traits.parquet` | `manifest.json` | Baseline / diagnostic; no accepted activity model; superseding run unconfirmed | [structural validation](../analysis/docs/structural_validation_check.md) |

## Cached presentation and pipeline checkpoints

| Path from root | Date / workflow | Inputs / provenance | Status / reproduction route |
| --- | --- | --- | --- |
| `analysis/data/` | Manifest generated 2026-10-22; evidence presentation | `experiments/data/`; `manifest.json` hashes inputs/code/products | Prepared local products; `analysis/rebuild.py`, then notebook; no superseding bundle established |
| `analysis/outputs/professor_presentation.html` | Presentation export; generation date not established here | Prepared data and notebook; no sibling manifest | Shareable static view; export command in cached guide, dynamic controls require live notebook |
| `analysis/outputs/boxplots.png`, `classifiers.png`, `descriptors.png`, `endpoints.png` | Loose presentation figures; date not established here | No sibling manifest establishing exact inputs | Illustrative exports; do not attribute them to a frozen run without verification |
| `pipeline/.live-smoke/2026-10-15/` | PubChem retrieval/normalization checkpoint | Raw snapshots, `observations.json`, ingestion/normalization observation records, product sidecars | Dated evidence check; [retrieval report](../pipeline/docs/live_retrieval_check.md); not a fixture |
| `pipeline/.live-smoke/candidates-2026-10-15/` | Candidate retrieval inspection | Saved observations and inspection/walkthrough text | Dated evidence check; same retrieval report; no supersession confirmed |
| `pipeline/.live-smoke/chronic-endpoints/` | Point-of-departure check; folder date unspecified | Typed Parquet products and `.metadata.json` dependency hashes | [Point-of-departure report](../pipeline/docs/point_of_departure_check.md); see offline EPA example for a fresh output, not an overwrite |

See [data conventions](data.md) for obtaining inputs and future run naming.
Keep old manifests and CSV/Parquet exports intact. Hash agreement establishes
file integrity; it does not establish scientific validity or automatic supersession.

## Professor follow-up — 2026-11-04

`analysis/outputs/professor-followup-2026-11-04-final/` is a new exploratory
matched-cohort checkpoint, generated by `analysis/professor_followup.py` from
`structure-2026-10-28-stress-baseline/structural_features.parquet`. Its manifest
hashes exact inputs, code, locks and five CSV products. It adds halogen ablations,
held-out attribution and raw Morgan logistic/forest comparisons without replacing
older bundles. See [findings](../analysis/FINDINGS.md#halogen-attribution-and-raw-fingerprint-classifiers--2026-11-04).

`analysis/outputs/dietary-review-2026-11-04-final/` records a **40-candidate
identity/review pilot**, not a model result. `dietary_candidates.py` consumes the
tracked seed TSV, `dietary-pubchem-2026-11-04/` snapshots and the existing structural
feature bundle. The manifest hashes four products and all inputs. There are three
holds, one existing-selection identity overlap (L-proline), and no accepted
high-dose-safety or plant-inactivity labels. Preserve the raw responses and save
human decisions in a new versioned working copy.

## Automated dietary review — 2026-11-04

`analysis/outputs/dietary-triage-sources-2026-11-04/` preserves 95 public request
snapshots (full bodies/statuses/URLs/times, including one 404). Its derived
`analysis/outputs/dietary-triage-2026-11-04-final/` bundle is generated by
`analysis/triage_dietary.py` from the frozen dietary `review.csv`, these snapshots
and the tracked `dietary-triage-v1` policy. It contains triage, extracted evidence,
text flags, curated leads, a computed README and hash manifest. This is preliminary
research prioritization (12 provisional, 26 review, 2 presumed-negative exclusions),
not accepted safety/plant labels or a validated classifier. See the
[workflow contract](../analysis/docs/dietary-triage.md) and
[findings](../analysis/FINDINGS.md#preliminary-automated-dietary-review--2026-11-04).

## Deeper review connection audit — 2026-11-05

`analysis/outputs/deeper-review-connection-2026-11-05/` is a read-only evidence/
lineage/support audit of the local 16-file `notes/compound_review_deeper_2026-10-29/`
package. It retains file/study inventories, identity overlaps, hypothetical split
support, broken-link inventory, audit counts, standalone audit code and hashes.
This is not a new assay acquisition or approved labeling/model run. See the
[integration assessment](../analysis/docs/deeper-assay-review.md) for the connection
to dietary triage and the remaining source, label and diversity requirements.

## Verification release audit — 2026-11-05

`analysis/outputs/verification-release-audit-2026-11-05-final/` is an offline audit
of the 16-file `notes/compound_verification_release_2026-11-05/` input. It retains
external reference checks, effective conditional scenarios, priority queue,
identity holds, model-readiness guards, an explicitly hypothetical isomer drawing,
11 new lead identities, five usable new fingerprints and complete hashes/versions.
It approves no labels and fits no models. The corresponding
`analysis/outputs/verification-release-sources-2026-11-05/` preserves 28 public
request snapshots (including six unresolved name-query 404s), URLs/timestamps,
response bodies, acquisition script and hashes. The earlier prototype output
without `-final` is superseded. See the [assessment and reproduction commands](../analysis/docs/verification-release.md).

## 200-compound dietary comparator audit — 2026-11-05

`analysis/outputs/food-comparator-200-audit-2026-11-05/` preserves an executed
offline identity/overlap audit of the user-reported verified-benign 200-row TSV,
with row-level checks, 200 fingerprints, formula eligibility, audit code and
input/code/output hashes. No biological labels were assigned or models fitted.
The source TSV, older working reviews and model results were preserved.
See the [scope and reproduction instructions](../analysis/docs/compound_sources.md#expanded-user-verified-dietary-list--2026-11-05).

## Weekly pilots — 10 November 2026

The [workflow contract](../analysis/docs/weekly-pilots.md) and
[dated findings](../analysis/FINDINGS.md#weekly-two-track-pilots--2026-11-10)
explain policies, counts and remaining scientific review. All paths below are
local/ignored; new versions were written without replacing earlier frozen runs.

| Run ID under `analysis/outputs/` | Products / status |
| --- | --- |
| `weekly-toxicity-2026-11-10` | EPA inventory, every-row eligibility audit, rat oral exact medians/censored bounds, pooled tertiles and figures; selection-conditioned pilot |
| `weekly-models-2026-11-10` | Matched 171-compound scaffold reports with F1, coefficient metadata, 2,048-bit OOB importance; selection diagnostics only |
| `weekly-literature-sources-2026-11-10` | 15 PubChem identities and four publisher page responses with access statuses and immutable acquisition manifest |
| `weekly-literature-pdfs-2026-11-10` | Two primary PDFs, rendered Table 2 pages, text copies and source/hash manifest |
| `weekly-literature-acquisition-input-2026-11-10` | Exact earlier acquisition resource, independently matched to its original SHA256; later annotations have a new resource version |
| `weekly-literature-2026-11-10-reviewed` | 15 provisional structures, four cited source packets, descriptor points/medians/IQRs versus 58 selected herbicides; labels remain unknown |
| `weekly-ecotox-2026-11-10` | Full chemical inventory, archive members and 100 raw evidence samples; core source relations verified, no measurement normalization |
| `weekly-research-2026-11-10-final` | Standalone walkthrough, F1 figure, fold weight summary, literature/LD50 and candidate ECOTOX overlaps; seven upstream bundles verified |

The official ZIP and acquisition manifest are under
`experiments/data/raw/ecotox/2026-09-15/`. Its SHA256 is
`6aba4def7d6e405e8f9f44173e4fe132013f3657bb4b5491f1fcc660fd1454b1`;
the HTTP byte count and all member CRCs passed. No CompTox credentials were
needed for bulk acquisition or offline preflight. The full ECOTOX ingestion plan
remains broader than this inventory prototype. No accepted activity model or
natural tested-negative cohort is established by these outputs.

## Evidence expansion — 11 November 2026

See the [dated checkpoint](../analysis/FINDINGS.md#evidence-and-comparable-toxicity-expansion--2026-11-11)
and [workflow contract](../analysis/docs/weekly-pilots.md). Paths remain local and
ignored; earlier bundles are preserved unchanged.

| Run ID under `analysis/outputs/` | Products / limits |
| --- | --- |
| `expansion-cohort-2026-11-11` | Frozen 104 source IDs, nine literature priorities, candidate-only source identity worksheet and manifest |
| `expansion-ecotox-2026-11-11-context-verified` | All selected tests/results; typed native/slot tables, dictionaries, admission reasons, source coverage and atomic completed manifest; canonical identity pending |
| `expansion-sources-2026-11-11` | Recovered original 1998 PDF and rendered source-table/figure review intermediates |
| `expansion-primary-2026-11-11-final` | Fifteen source retrieval records with frozen resource, preserved bytes, HTTP/access statuses and hashes |
| `expansion-review-2026-11-11-verified` | Fifteen compound packets, 81 study/condition observations, 32 approval worksheet rows, policy readiness, unknown seven-column labels and preserved identity hold |
| `expansion-toxicity-2026-11-11-final` | Ranked overlap queue, four sensitivity scenarios, 25 censored-observation bin sets, missingness and aquatic exposure strata; no inferred duplicate collapse |
| `expansion-walkthrough-2026-11-11-verified` | Standalone verified HTML, three figures and links to proposal/evidence worksheets; five upstream manifests checked, no models fitted |

The initial ECOTOX expansion bundle records the earlier draft context policy;
use the explicitly `context-verified` bundle above. Source dictionary/record
inspection corrected Daphnia immobilization to ITX/IMBL before the final checkpoint.
None of these bundles approves biological labels or canonical ECOTOX identities.

## Human-reviewed adoption and cohort models — 2026-11-11

See the [adoption/modeling contract](../analysis/docs/human-review.md) and
[dated findings](../analysis/FINDINGS.md#human-review-adoption-and-new-cohort-models--2026-11-11).
Local ignored products:

| Bundle under `analysis/outputs/` | Contents |
|---|---|
| `human-review-adopted-2026-11-11-final/` | Human declaration and source-workbook hash; 19 natural-origin labels; 80 activity decisions in four separate policies; original/adopted ledgers; 119 second-pass condition observations; activity support/empty predictions; preserved identity hold; 30-compound contrast features |
| `reviewed-cohort-models-2026-11-11-final/` | Eight matched five-fold cohort classifiers, out-of-fold predictions, raw-formula coefficients, held-out permutation and 2,048-bit OOB diagnostics; target is 19 natural-occurrence versus 11 commercial-herbicide comparator membership |
| `human-reviewed-progress-2026-11-11-complete/` | `walkthrough.html`, verified model metrics, biological group counts, descriptor summaries/figures and historical LD50 values with updated reviewed-group annotations |

The source workbook is
`expansion-review-2026-11-11-verified/compound_evidence_second_pass_2026-11-11.xlsx`.
No source workbook or frozen prior result was overwritten. Activity-specific
classifiers remain unsupported by within-policy scaffold/class diversity; new
cohort models do not predict biological activity, safety or origin as a universal
property. The presentation notebook and HTML remain local under ignored `notes/`.

## Identity-approved ECOTOX comparisons — 2026-11-11

See [identity approval and context-comparison contracts](../analysis/docs/human-review.md#explicit-ecotox-identity-approval)
and [dated findings](../analysis/FINDINGS.md#explicit-ecotox-identity-approval-and-comparisons--2026-11-11).

| Local bundle under `analysis/outputs/` | Contents |
|---|---|
| `ecotox-identities-approved-2026-11-11/` | Snapshot-bound user approval declaration, 104 approved mapping pairs, original-status ledger, preserved cohort |
| `ecotox-selected-approved-2026-11-11/` | Reimported 79,171 native results / 79,302 slots with approved canonical IDs; unchanged scientific source fields and policies |
| `ecotox-approved-reconciliation-2026-11-11/` | Refreshed canonical admission and overlap status; unchanged rat baseline; no duplicate decisions |
| `ecotox-approved-comparison-2026-11-11-verified/` | `walkthrough.html`, 41 core-policy ecological observations, compound/context summaries, exposure/documentation sensitivities, source row accounting, 16-record rat LD50 review queue and figures |

The core duration fields are observation times, distinct from exposure duration.
The reported exposure/control subset contains zero trout and one Daphnia record.
Ecological concentrations remain separate from rat oral LD50; identity approval
supplies no new activity labels, same-study adjudications or universal safety claim.
The local presentation notebook and HTML remain ignored and uncommitted.

All 104 source mappings are approved, but only 103 have result records.
Acacetin (`ECOTOX:chemical:480444` / `PUBCHEM:5280442`) has zero results in the
frozen snapshot and remains an assessed zero in source coverage. The reconciliation
manifest’s `approved_ecotox_identities` counts observed canonical IDs (103), not
the full approved crosswalk (104). Zero coverage supplies no safety/activity label.

## Local experimental expansion — 2026-11-12

The [experimental checkpoint](../analysis/docs/experimental-expansion-2026-11-12.md)
records permissive AI proposals and intentionally heterogeneous assay pooling.
These results are separate from the 2026-11-11 human-reviewed datasets.

| Local bundle under `analysis/outputs/` | Contents |
|---|---|
| `experimental-heterogeneous-activity-2026-11-12/` | 73-structure pooled sensitivity; four PCA activity models, support statuses and held-out predictions |
| `experimental-heterogeneous-diagnostics-2026-11-12/` | Eight fixed profiles; formula coefficients; held-out and tree-specific OOB permutations |
| `experimental-heterogeneous-controls-2026-11-12/` | Twenty shuffled-label repeats per PCA representation and fold/scaffold stress statuses |
| `experimental-publication-transfer-2026-11-12-final/` | Three publication holdouts; raw formula/Morgan logistic and forest; scaffold-purged comparison, baselines and actual split membership |
| `experimental-ecotox-decisions-2026-11-12/` | Rebuilt 41 aquatic observations with explicit duplicate-decision scenarios; no new real decisions or rat admissions |
| `experimental-research-checkpoint-2026-11-12/` | Offline walkthrough, figures, compact metrics/weights/null controls and verified summary manifest |

Ignored `experiments/bioherbicide-expansion-2026-11-12/` holds source snapshots,
the 16-study screen, 304 provisional plant and 59 other endpoint observations,
policy assumptions, source-specific proposals, identity gaps, no-fit support runs
and reproducible local scripts. Use `pooled-v2-corrected-doi/` inputs; the initial
mistyped-DOI draft is retained as superseded. The pool passes computational gates
but fails publication transfer; it is not an accepted activity or safety model.

### Aquatic context overlay sensitivity — 2026-11-12

See the [overlay contract](../analysis/docs/human-review.md#source-linked-aquatic-context-overlays)
and [dated findings](../analysis/FINDINGS.md#source-linked-aquatic-context-sensitivity--2026-11-12).

| Local bundle under `analysis/outputs/` | Contents |
|---|---|
| `aquatic-context-reviewed-2026-11-12/` | Frozen original observations, eight audited provisional pH proposals, zero adopted fields, original/source-adjudicated summaries and coverage |
| `aquatic-context-experimental-2026-11-12/` | Same source observations; eight explicitly provisional initial-pH enrichments from a primary-authored abstract; field-level provenance and uncertainty preserved |

Both retain 28 trout/13 Daphnia records and zero trout/one Daphnia in the reported-
context subset. All original row fields and the frozen comparison's hashes were
verified unchanged. No source-context assumption supplies a new rat admission or
safety claim. `experiments/aquatic-context-2026-11-12/` contains the source registry,
NCBI XML snapshot, acquisition logs, original-value-bound proposals, executed
verification and exact run source; all remain ignored.

### Experimental structural binding pilot — 2026-11-12

See [contract and checkpoint](../analysis/docs/binding-evidence.md) and
[dated findings](../analysis/FINDINGS.md#natural-product-structural-binding-pilot--2026-11-12).

`analysis/outputs/binding-structural-pilot-2026-11-12-final/` contains two audited
experimental-complex records, three protein entity/sequence records, parent versus
bound-form identities, source/host distinction, DOI/revision/resolution metadata
and hashed provenance. `experiments/binding-pilot-2026-11-12/` contains bounded
public snapshots, the declared source resource, 15 manually transcribed author
contacts, two quantities with separate roles, an executed wrong-cofactor rejection,
a rendered chemical-form comparison and limitations. Both directories are ignored.

The pilot keeps tentoxin's exact bound form distinct from cornexistin's bound
diacid; it does not substitute a cofactor, infer affinities, map weed orthologs or
train a binding model. The preliminary non-final catalog remains preserved.

### Experimental compatible-assay expansion — 2026-11-12

See the [focused checkpoint](../analysis/docs/experimental-expansion-2026-11-12.md#compatible-flavonoid-series-expansion).
The ignored local `experiments/compatible-assays-2026-11-12/transcription-v1/`
holds 324 observations for 27 compounds across two species, three doses and two
endpoints. `analysis-v2/` contains provisional structures, two unsupported
100 µM root-growth preflights, six parent/O-methylated pairs across 36 conditions,
descriptors, SVG/PNG figures and hashed manifests. `verification.json` records
source-cell, policy, constitutional-identity and 136 hash checks. The incomplete
`analysis-v1/` is superseded. These are experimental evidence and descriptive
results, with no new fitted model, reviewed labels or safety conclusion.

### Fixed transfer to the new root-growth paper — 2026-11-12

`analysis/outputs/experimental-flavonoid-transfer-2026-11-12/` contains a separate
four-publication fixed-model diagnostic; see the [checkpoint](../analysis/docs/experimental-expansion-2026-11-12.md#fixed-transfer-to-the-recovered-root-growth-series).
The primary new-paper test trains exclusively on the unchanged earlier 73
compounds and evaluates 20 new radish root-growth compounds. All three profiles
miss both high responses. Scaffold-purged sensitivities expose low precision and
unstable predictions. Concrete protocol, extended inputs and verification are in
`experiments/compatible-assays-2026-11-12/`; 24 reports, 558 predictions and 94
hashes verify. Assay targets remain incompatible; this is exploratory transfer,
without a selected model or safety inference.

### Experimental rat-source review — 2026-11-12

See the [source-review checkpoint](../analysis/docs/rat-source-review-2026-11-12.md).
`experiments/rat-source-review-2026-11-12/` contains cached primary PDF, rendered
pages, 14 material/sex table cells, two provisional acid-case eligibility records,
a conversion-discrepancy audit and separate mixed-basis arithmetic sensitivities.
`analysis/outputs/rat-source-reconciliation-2026-11-12/` adopts four experimental
`different_observation` decisions without changing historical LD50 admissions.
The source review flags two other ester conversions without correcting reported
values. Internal verification covers the source/decision/scenario products and
45 hashes. These ignored local bundles preserve dose basis, native contradictions
and AI review status; no harmonized new natural-product comparison is established.

### Pre-integration preservation

The [local preservation inventory](data.md#local-experimental-preservation--2026-11-12)
records the verified research archive and historical-code Git bundle created
before local main integration. It preserves current experimental files and their
hash-linked dependencies, including unfinished work, without promoting their
scientific status. One superseded preliminary transfer run retains an unresolved
historical script hash; canonical final runs remain separately identified.

## Separate experimental and external-model evidence — 2026-11-12

The [first A/B checkpoint](../analysis/docs/modeled-evidence-2026-11-12.md)
records a source-first provisional release and fixed separate evaluations.

| Local bundle | Contents |
|---|---|
| `analysis/outputs/separate-evidence-2026-11-12-v2/` | Separate A/B observations/targets: 4,234 experimental and 43,128 CATMoS full structures; source/identity/lineage/exclusion audits and code/lock snapshots |
| `experiments/external-evidence-2026-11-12-run1/dietary-test-v1/` | 40 dietary identity attempts; 38 stored TEST successes, two review cases; raw response/code preservation |
| `analysis/outputs/separate-evidence-models-2026-11-12-v3/` | Five scaffold/connectivity outer folds per pathway; baselines, regression/classification, weights, OOB stability, figures and C decision |
| `analysis/outputs/separate-evidence-comparison-2026-11-12-v3/` | Offline `walkthrough.html`, TEST union of 173 full structures, cohort/group descriptions, duplicate audit and paired training-lineage/similarity |

The work root also retains downloaded source packages, a held 13,680-row author
aggregation, API/platform access logs, source-specific normalization review,
independent verification and source backlog. Almost all paired A/B structures
carry teacher-training tags; agreement is not independent validation. Archive
CATMoS scale interpretation is provisional and must not be reused for fresh CLI
exports. C is deferred. No historical rat labels, human approvals, source exports
or previous manifests changed. All scientific data remain ignored/local.

The follow-up `analysis/outputs/separate-evidence-multiclass-oob-2026-11-12-v1/`
adds **same-three-class** forest OOB macro-F1 permutation diagnostics with ten
repeats and class-probability/vote records. It does not replace the frozen outer
splits or binary OOB sensitivity. The gitignored local experimental Marimo
notebook at `notes/notebooks/evidence_experiments.py` begins with Track 1/2
compound/group counts, then explores F1, logistic coefficients, forest importance
and publication-transfer failure. See the checkpoint for its scientific scope.
