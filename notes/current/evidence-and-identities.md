# Evidence, identity and input conventions

Current orientation, reviewed 2026-11-02. The normative implementation contracts
remain in the [pipeline decisions](../../pipeline/docs/decisions.md) and topic
guides; this note links research interpretation to them without duplicating schemas.

## Identity and curation

Curated queries resolve to PubChem compounds; aliases can share a CID, while
unresolved queries remain explicit. EPA adds an approved DTXSID crosswalk with
candidate/review evidence. Names alone do not establish equivalence. Keep salts,
esters, stereochemistry, mixtures and formulation context visible.

| Stage | Known local checkpoint | Source / update trigger |
| --- | --- | --- |
| Source candidate curation | 61 herbicide + 127 natural-product candidates, including plant response markers | [Dated provenance](../CURATED_COMPOUNDS.md); change only with a new reviewed source record |
| Retrieval selection | 178 input rows | `experiments/data/compounds.csv`; retain manual name/CID decisions |
| Prepared analysis cohort | 176 resolved rows: 60 herbicides, 116 natural products | `analysis/data/compound_traits.csv`; verify manifest and stage denominators on a new rebuild |
| EPA identity | 136 approved / 24 review / 16 unresolved | `experiments/data/epa_identity_crosswalk.csv`; approved identities gate EPA retrieval/analysis |

The first candidate list is historical source provenance, not a current roster.
Its `NOTES` line references now resolve to the preserved pre-split
[notes snapshot](../archive/sources/research-notes-2026-11-02.md). See
[inputs and identities](../../pipeline/docs/inputs-identity.md).

## Endpoints and evidence classes

| Endpoint types | Current support / interpretation |
| --- | --- |
| LD50, LC50, EC50 | PubChem prose extraction plus structured EPA normalization; context/unit rules still gate eligibility |
| NOAEL, LOAEL | Structured EPA support; daily doses remain distinct from total doses |
| BMD, BMDL | Structured EPA support; model-derived points of departure, kept distinct from TEST predictions |

[Shared policies](../../pipeline/examples/endpoints.yaml) configure eight named
comparisons for seven endpoint types: broad oral LD50, broad fish LC50,
96-hour rainbow-trout LC50, 48-hour Daphnia EC50, and four mammalian oral daily-dose
point-of-departure policies. There is no configured algal comparison yet. The
research priority includes algal growth and other aquatic evidence; implementation
support is not the same as adequate local coverage.

Current example policies describe availability. Heterogeneous chronic records do
not become pooled potency medians. Custom point-of-departure potency comparisons
require explicitly constrained study context; BMD/BMDL also require benchmark/model
context. PubChem chronic zeros reflect parser scope, not absent chronic studies.
See [endpoint contracts](../../pipeline/docs/endpoints-comparisons.md) and the
[dated endpoint note](../archive/reports/ENDPOINT_DEFINITIONS.md) for its historical counts.

ToxCast activity/curve metrics, source-admitted experimental hazard, measured and
calculated chemical properties, stored TEST predictions, and BMD/BMDL remain
separate evidence classes. An assay hit is not an organism-level LD50. Preserve
source admission, provenance and review reasons rather than relabeling all records
as measured toxicity.

## Missingness and reproducibility

A source flag is one for an eligible match, zero for an assessed source without
a match, and null for unavailable assessment. The union is one if either matches,
zero only if both were assessed without a match, and otherwise null. Coverage is
an extraction/eligibility result, not proof of biological inactivity or safety.

The maintained cached rebuild reads existing source bundles, uses no API key and
never fetches missing descriptors. Acquisition/preparation remains partly local
and manual. The [data guide](../../docs/data.md) records required files, credentials
for live acquisition, transfer gaps and the complete bootstrap boundary.
Raw snapshots, curated decisions and reviewed labels are research inputs;
virtual environments and tooling caches are different. Keep old manifests and
source artifacts unchanged. See [results](../../docs/results.md).


## ECOTOX explicit identity approval — 11 November 2026

The user approved all 104 frozen mappings. New versioned identity/selected-result
bundles attach canonical IDs without changing source scientific fields. Core
observation-duration policies admit 28 trout LC50 and 13 Daphnia EC50 records;
reported actual-exposure/control fields retain only zero trout / one Daphnia.
The 16 rat LD50 source rows remain in context review; historical rat medians and
cutoffs are unchanged. No biological labels or duplicate-study decisions follow
from identity approval. See [contract](../../analysis/docs/human-review.md#explicit-ecotox-identity-approval)
and [findings](../../analysis/FINDINGS.md#explicit-ecotox-identity-approval-and-comparisons--2026-11-11).
