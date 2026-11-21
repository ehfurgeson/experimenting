# Public import results, 18 November 2026

The [import audit](import-coverage-2026-11-18.md) covers all 27 local files.
This run reconstructs the public evidence on branch `feat/import-coverage`
from base `09e87d1`. Output directories below are relative to
`experiments/import-expansion/`. The [analysis README](../README.md) and
[data sprint](data-sprint.md) document the commands.

## Source yield

| Product | Result |
| --- | --- |
| `public-cohorts-v2/` | ICE 4.1 gives 5,921 exact and 47 censored eligible observations, with exact medians for 4,234 structures. The pinned OPERA archive gives 43,128 eligible full-key CATMoS teacher targets after duplicate resolution. The provisional A and B cohort counts reproduce the earlier checkpoint. |
| `nice-context-v3/` | Scanned all 974,778 data rows in the 11 supplementary workbooks. Retained 93,538 exact-structure rows, 3,483 identifier-only rows and 4,636 held rows. All 1,105 dermal rows linked to A are mixture records and stay on hold. |
| `nice-archives/` | 4,173 ClassyFire records support exact structure context and 182 remain on hold. The cHTS archive supplies 3,437,353 DTXSID-linked endpoint rows across 1,945 measured-cohort structures. This is coverage. No interpretation of cHTS responses or QC flags was made. |
| `npass-context-v2/` | The four previously unused production tables supply 276 exact cohort record links out of 2,553 source rows. The occurrence overlay retains 18,921 taxon/publication rows for 1,697 distinct full structures pending primary review. The activity sweep recovers 469 plant-protein records and separates these from plant growth evidence. |
| `coconut/` | Recomputed identities for all 738,793 source entries. There are 724,233 distinct valid full keys, with 1,478 exact ICE matches and 6,263 exact CATMoS matches. The bounded pass produced the same cohort overlap CSV byte for byte. |
| `ecotox/` | EPA's 15 September 2026 archive gives 73,317 non-algal growth, germination and biomass review records across 25,333 discovery strata. The public-only extraction reproduced the earlier source count. |
| `toxval/` and `toxval-more/` | Screened 197,857 records across eleven ToxValDB v9.7.0 workbooks. The original three workbooks supply 445 exact-dose structure leads outside ICE. Eight additional workbooks supply 83, with 20 overlapping the first screen. HPV and TSCA 8(e) account for the additional qualifying exact-dose rows. The union has 508 held exact-dose structure leads, an increase of 63. |

The EPA leads retain the source references, dose qualifiers and study-form holds.
The audit established no additional independent studies for admission as
training labels. Rat oral LD50 covers acute lethality for a specified species
and route. Field exposure, chronic toxicity and crop selectivity need their own evidence.
[EPA ToxValDB release](https://doi.org/10.23645/epacomptox.20394501)
and [ECOTOX database](https://cfpub.epa.gov/ecotox/index.cfm).

## Catalog and herbicide comparison

The cutoffs are the project's existing rat oral LD50 bins. Low is ≤1,080,
medium is >1,080 through 3,400, and high is >3,400 mg/kg.

| Evidence group | Low | Medium | High | Total |
| --- | ---: | ---: | ---: | ---: |
| COCONUT or NPASS exact key with an ICE median | 702 | 504 | 411 | 1,617 |
| HRAC name-linked structure with an ICE median | 39 | 56 | 36 | 131 |
| COCONUT or NPASS exact key with a CATMoS teacher target | 2,411 | 3,343 | 1,355 | 7,109 |
| Catalog-linked EPA exact-dose leads outside ICE with all qualifying reports in one bin | 32 | 40 | 35 | 107 |

The EPA catalog screen has another 20 structures with exact reports spanning
multiple bins. Catalog and HRAC rows can overlap. Exact catalog membership
supports triage for low-LD50 exclusion and directs primary occurrence review.
Catalog absence leaves natural origin unknown. Previous direct comparison
also found useful LOTUS taxon/reference links and a false origin inference
from a soybean study involving glyphosate. See the
[LOTUS review](research-followup-2026-11-17.md#natural-toxicants-occurrence-links-and-analogues).

Halogens occur in 92 of 131 HRAC name-linked structures with an ICE median
(70.2%) and in 278 of 1,617 ICE structures with a catalog match (17.2%).
Median molecular weight is 256.5 and 182.3, respectively. These are overlapping
convenience cohorts. Herbicide-use membership, source occurrence evidence and
plant response remain distinct. The dataset has too few qualified plant
responses for an inference about structural differences between biologically
natural high- and low-response groups.

## Model and panel results

| Target | Group-held-out forest macro-F1 | Logistic macro-F1 |
| --- | ---: | ---: |
| ICE experimental A | 0.431 | 0.382 |
| OPERA CATMoS teacher B | 0.616 | 0.465 |

B measures agreement with teacher outputs. The two models have different
evaluation targets. The standardized logistic weights for the low-LD50
class are fold means. The largest magnitudes in A are H-bond acceptors
(+0.390), polar surface area (−0.388) and rotatable bonds (−0.336). B gives
polar surface area (−1.070), rotatable bonds (−0.790) and H-bond acceptors
(+0.717). These are conditional associations. The separate binary forest's
OOB permutation diagnostic shows the largest mean F1 drop for rotatable
bonds in A (0.033) and polar surface area in B (0.110). Three repeats measure
shuffle stability. They do not provide significance tests or an independent
chemical holdout. The complete per-class metrics, fold predictions, weights,
OOB results and model manifest are in `public-models-v2/`.
The [block permutation test](oob-null-test.md) evaluates global binary OOB F1
against a scaffold-preserving null.
The [NPASS and NICE experiments](import-model-experiments.md) evaluate
source-linked training labels and curated assay features on measured ICE splits.

The [2026 HRAC master list](https://hracglobal.com/tools/2026-hrac-global-herbicide-moa-classification)
provides an independent herbicide-use benchmark. The panel scores 274 of 365
active-ingredient rows with both forests, including 131 A and 224 B
group-held-out scores. The 91 unscored rows remain visible with ambiguous or
unresolved identity. The model panel uses literal source-name leads. Tested form
still requires review, and exploratory scores for outside-cohort rows use full-fit
models. Per-row outputs are in `public-panel-v4/`.

The [original reviewed panel rerun](reviewed-selection-results.md) uses the
supplied `data_imports/structural_features.parquet`. Both forests scored all
116 natural-product rows and 58 of 60 herbicide rows, matching the coverage
reported in the [previous run](research-followup-2026-11-17.md). Two
multicomponent herbicide identities remain on hold.

## Plant evidence and analogue results

The follow-up [Parthenium review](parthenium-evidence.md) adds a separate
plant dose-response study and checks analogue rank sensitivity to exact ICE
reports. The [limonene review](limonene-evidence.md) links enantiomer-specific
lab germination effects, primary biosynthesis evidence and a high rat oral
LD50 record. The [catalog hazard review](catalog-hazard-review.md) gives
the record-level low-bin evidence and the LOTUS/NPASS comparison.

* `integrated-v4/` retains 14 precise ECOTOX response points over eight
  structures. These require a reported concentration and control context,
  explicit response scale, and an unambiguous DTXSID link. The broader
  discovery inventory retains all threshold endpoints and weaker context.
  Only one NPASS taxon/reference-linked ICE structure outside the linked
  HRAC benchmark also had a retained high response. It is dibutyl phthalate.
  The source reports 25% of control for Chinese sprangletop, normalized to
  75% inhibition. EPA documents widespread plasticizer use, so the natural
  origin lead remains on hold pending production and contamination review.
  [Plant study](https://doi.org/10.1071/CP13339)
  and [EPA environmental hazard assessment](https://www.epa.gov/system/files/documents/2025-12/17-dbp-environ-hazard-tsd-public-release-hero-december-2025.pdf).
* A primary *Annona reticulata* study adds 12 pure-isolate growth I50 values
  across cress and timothy, three compounds, and root and shoot elongation.
  Endpoints span 0.013–0.120 mM after 48 hours. Hydroxytyrosol supports a
  full-structure link. The loliolide and pentylfuranone sample mappings retain
  stereochemistry review holds. These lab isolates add evidence for inhibition
  within the reported conditions. The [prior field review](research-followup-2026-11-17.md#prioritized-research-and-next-work)
  gives the commercial pelargonic acid formulation context separately.
  [Annona primary study](https://doi.org/10.3390/agronomy12112883).
* Hydroxytyrosol lacks an exact ICE target. A public FDA dossier cites a
  rat acute oral bound above 2,000 mg/kg, which spans the project's medium
  and high bins. It supplies no exact point. The top five high-ICE-bin
  catalog analogues for this query have Morgan Tanimoto 0.217–0.286.
  The earlier analysis produced 18 pairs at ≥0.6 using 116 original
  queries and a broader, assumption-sensitive toxicity pool. Neither search
  transfers observed plant activity or establishes human safety.
  [FDA-hosted toxicology dossier](https://www.fda.gov/media/152671/download?attachment=).

## Two exact-structure evidence checks

| Compound | Plant result | ICE rat acute oral evidence |
| --- | --- | --- |
| Vanillin | An isolated-compound study reports suppression of radish root and shoot elongation. The trial concerns a single species and its tested exposures. | Five eligible records span 1,580–3,925 mg/kg. The cohort median is 3,300 mg/kg (medium). The held-out A forest assigns low. OECD summarizes the underlying rat studies, with some point estimates and intervals crossing the project's medium/high boundary. |
| Decanoic acid (capric acid) | A commercial caprylic/capric acid blend was tested in field and greenhouse weed-control experiments. Individual ingredient efficacy remains unresolved in that trial. | Three eligible reports span 3,320–15,800 mg/kg. The cohort median is 3,730 mg/kg (high). The held-out A forest assigns medium. The source values cross the project's medium/high boundary. |

The vanillin records are ICE `Data` rows 570, 572, 573, 575 and 576.
The decanoic acid records are rows 15409–15411. Both cases depend on
retaining individual records and tested form when the aggregate crosses a
class boundary or a published efficacy result involves a formulation.
[Vanillin plant study](https://www.scielo.br/j/pat/a/zL4YBLxMTTNMVXS5qVkVFMB/),
[OECD vanillin assessment](https://hpvchemicals.oecd.org/ui/handler.axd?id=2928e1f3-70af-4d2c-80a8-3c1205d0daa3)
and [commercial formulation trial](https://doi.org/10.1002/ps.8711).
