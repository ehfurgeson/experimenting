# Data-first evidence sprint

Run from the repository root in the locked analysis environment. Real inputs and
products belong in a **new ignored run directory**, never over an existing release.
This workflow adds source evidence; it does not adopt biological labels or fit models.

Freeze the original measured A, teacher-derived B and prepared selection memberships:

```bash
uv run --project analysis --locked python analysis/data_sprint.py \
  --release analysis/outputs/separate-evidence-2026-11-12-v2 \
  --selection analysis/outputs/structure-2026-10-27-verified/structural_features.parquet \
  --output experiments/data_acquisition/NEW_RUN/baseline
```

The freeze verifies A/B bytes against their original manifest and records upstream
paths, hashes, Git commit, full keys, original structures and unresolved selection
rows. The prepared selection includes 176 rows (116 selected natural products and
60 herbicides), rather than assuming the planning shorthand of about 120 is exact.
Selection membership alone does not establish natural occurrence or plant activity.

Acquire selected public exports explicitly (network required):

```bash
uv run --project analysis --locked python analysis/collect_data_sprint.py \
  --run experiments/data_acquisition/NEW_RUN \
  --only npass-structure npass-general npass-toxicity coconut-lite
```

Additional choices are `npass-occurrence`, `npass-species`, `npass-activity`,
`npass-target`, and the versioned `toxval-chemid`, `toxval-echa`, `toxval-test`,
`toxval-dictionary` workbooks. URLs were inspected on the provider pages and EPA
file index; NPASS is version 3.0,
COCONUT CSV-lite is November 2026. SQL dumps are not needed. `sources.json` records
URL, UTC acquisition time, version, license qualification, HTTP status, SHA256,
byte count and failures. A failed/partial download is retained and cannot be
silently retried over the same filename; choose a separate run for another attempt.
HTTP success alone does not qualify file format or scientific content.
NPASS text is stored losslessly as gzip, recording both stored and native hashes
and sizes. Acquisition refuses to start another source with less than 64 MiB free.

Inventory accepted plant policies and screen the existing ECOTOX snapshot:

```bash
uv run --project analysis --locked python analysis/sprint_plant_inventory.py \
  --adoption analysis/outputs/human-review-adopted-2026-11-11-final \
  --ecotox experiments/data/raw/ecotox/2026-09-15/source.zip \
  --output experiments/data_acquisition/NEW_RUN/plant-inventory
```

The accepted-policy inventory counts unique valid full structures and class-bearing
scaffolds within each policy; unresolved policies remain empty. Original accepted
source observations are copied separately. The compressed
`plant_activity_observations.csv.gz` retains native result/test/reference/species
JSON, concentration, qualifier, duration, control and locators for non-algal plant
growth (`GRO`), germination (`GERM`, `GMEN`) and biomass (`BMAS`, `DBMS`) candidates.
Non-algal vascular plants include aquatic species; habitat and medium still require
review. Chlorophyll, photosynthesis and protein effects are not automatically plant
growth observations. Registry strata are discovery groups, not harmonized assays.
All new labels stay unknown, including NOEC and nonsignificant effects. Numerical
effect values do not establish high/low response without a compatible within-assay
policy and primary source review. Existing identity holds remain in force.
Omit `--adoption` for an archive-only inventory in a fresh checkout. This
produces the same ecological observations and assay registry without the
reviewed-policy exports.

Normalize NPASS identities/toxicity and COCONUT catalog overlaps offline:

```bash
uv run --project analysis --locked python analysis/sprint_natural.py npass \
  --structures YOUR_RUN/sources.json --toxicity YOUR_RUN/sources.json \
  --baseline YOUR_RUN/baseline/cohort_membership.csv --output YOUR_RUN/npass
uv run --project analysis --locked python analysis/sprint_natural.py coconut \
  --registry YOUR_RUN/sources.json \
  --baseline YOUR_RUN/baseline/cohort_membership.csv --output YOUR_RUN/coconut
```

Each source registry entry must report a successful download with matching stored
SHA256. RDKit recomputes full keys, records unassigned atom stereocenters and holds
multicomponent structures and provider-key disagreements. NPASS duplicate source
IDs are logged: identical repeats collapse for identity membership; conflicting
structures quarantine the ID. Raw source bytes remain recoverable. All original
toxicity fields are retained in `npass_toxicity_all.csv.gz`. The actual export has
no route, acute context or experimental-status columns, so its eligible table is
empty until primary-source qualification. Rat/LD50 alone does not establish oral.
The NPASS context command optionally accepts `--production data_imports/NPASS`
to inventory Coculture, Elicitation, Engineer and Symbiont beside the main
species, occurrence, activity and target tables. It preserves all native
production rows, including rows outside the supplied cohort.
COCONUT validates every exported structure and writes cohort matches plus identity
conflicts. It adds catalog coverage and zero toxicity observations. Exact full-key
matches still do not resolve unspecified source stereochemistry or tested forms.
For a faster cohort overlay, `coconut --cohort-only` scans all source IDs and
recomputes structures only when the source connectivity block is relevant to
the supplied cohort. The resulting counts explicitly describe that qualification
scope. Use the default mode for a catalog-wide identity-quality census.

Screen selected ToxValDB workbooks offline:

```bash
uv run --project analysis --locked python analysis/sprint_toxval.py \
  --registry YOUR_RUN/toxval-acquisition/sources.json \
  --release analysis/outputs/separate-evidence-2026-11-12-v2 \
  --baseline YOUR_RUN/baseline/cohort_membership.csv --output YOUR_RUN/toxval
```

The default audit covers TEST, ChemIDplus and ECHA. To audit other v9.7.0
tables, acquire them with `collect_data_sprint.py --only` and use the same
unique source IDs in `sprint_toxval.py --only`. Options include HPV, TSCA 8(e),
OPP, DoD, ToxRefDB, EFSA, ECOTOX and WHO JECFA study tables.

The screen requires explicit experimental/rat/oral/acute/LD50, positive finite
mg/kg values, supported exact/bound qualifiers, record references and no source
QC failure. Every source row and all linked `record_source` records are retained
in compressed observations; exclusions are counted by reason. **Endpoint-eligible
candidates are not admitted labels.** Source DTXSIDs link only when existing valid
ICE/CATMoS identities agree on one full key; ambiguity remains unresolved, without
salt/parent or stereo merging. These are local identifier links, not new tested-form
verification. All candidates retain tested-material and original-study independence
holds. Candidate exact versus censored-only novelty is reported separately from
confirmed net-new eligible structures (zero until holds resolve). Study novelty
remains null. Reference/dose overlaps with A flag possible mirrors for review;
different dose/reference text does not prove independence. ChemIDplus's actual
experimental status is `undetermined`; TEST has explicitly experimental source rows
which still need their original lineage reviewed.

Join NPASS occurrence references and screen plant activity without adopting labels:

```bash
uv run --project analysis --locked python analysis/sprint_npass_context.py \
  --registry YOUR_RUN/acquisition-v2/sources.json --npass YOUR_RUN/npass \
  --baseline YOUR_RUN/baseline/cohort_membership.csv --output YOUR_RUN/npass-context
```

`npass_occurrences.csv.gz` covers the exact cohort-key subset, retaining original
organism/isolation/reference fields. Publication-plus-taxon links are distinct from
catalog/database links and remain unreviewed database assertions. Organism engineering,
coculture and symbiont flags remain in raw organism JSON. They require interpretation
before any accepted occurrence claim. `npass_plant_assay_leads.csv.gz` separates plant
protein mechanisms, explicit phenotype candidates, unresolved organism endpoints and
tissue/other channels. The taxonomy screen uses populated numeric IDs from source
Viridiplantae records; missing IDs never join, coverage is incomplete and green algae
can appear. NPASS target IDs are **not assay IDs**. Reported activity values are not
automatically experimental doses. Dose, duration and controls remain missing until
original-assay retrieval. The registry groups target/reference/endpoint leads only;
no high/low labels or independent studies are inferred from these rows.
The provider's delimiter-only general-information separator is ignored; populated
rows with missing/extra fields still fail rather than shifting columns silently.

Synthesize the canonical products into an auditable local report:

```bash
uv run --project analysis --locked python analysis/sprint_report.py \
  --baseline YOUR_RUN/baseline --npass YOUR_RUN/npass --coconut YOUR_RUN/coconut \
  --context YOUR_RUN/npass-context --toxval YOUR_RUN/toxval --plant YOUR_RUN/plant-inventory \
  --adoption analysis/outputs/human-review-adopted-2026-11-11-final \
  --output YOUR_RUN/reports
```

This dated synthesis requires the frozen 4,234 A / 43,128 B / 176 selection rows.
It verifies upstream scientific inputs and products, retains catalog, unreviewed
taxon/publication and already adopted occurrence tiers separately, and joins the
already adopted assay-specific plant responses without pooling labels. Outputs are
`cohort_overlap.csv.gz`, count/denominator tables, `source_waterfall.csv`, the complete
selection evidence queue, a 28-row computational audit sample, two rendered scientific
plots and `DATA_YIELD_REPORT.md`. Code, package versions and current lock hashes are
retained. Historical manifests and dependency edits are preserved. The queue ranks
evidence completeness for research follow-up, not safety or predicted efficacy.
See the [dated checkpoint](data-sprint-2026-11-17.md) for this acquisition's results.

For the targeted six-assay ChEMBL follow-up, preserve complete assay snapshots
with the existing `agrotox.chembl.fetch_assay` adapter. The local acquisition script
and request logs retain the exact selected IDs. The offline source review uses
the snapshot registry and complete 12-molecule podolactone identity response:

```bash
uv run --project analysis --locked python analysis/sprint_chembl_review.py \
  --snapshots YOUR_RUN/chembl-assays-v1 --output YOUR_RUN/chembl-review
```

The source-specific review retains all bounds and native rows. Podolactone assay
bounds remain unresolved to a single dose because the primary qualitative table
summarizes activity across concentrations. The Logran control has a specific
formulation-versus-single-ingredient hold. Primary text was available through web
parsing, but PDF bytes and screenshots were inaccessible; visual verification is
explicitly unavailable. No bounds or unknowns become adopted labels. Supply
`--chembl YOUR_RUN/chembl-review` to `sprint_report.py` to include the held source
package and separate exact-identity candidate coverage in the synthesis.

Complete the all-NPASS catalog crosswalk without repeating chemistry normalization:

```bash
uv run --project analysis --locked python analysis/sprint_catalog_cross.py \
  --npass YOUR_RUN/npass --coconut YOUR_RUN/coconut --output YOUR_RUN/catalog-cross
```

The crosswalk verifies both input bundles, excludes every held COCONUT source ID,
and uses the already verified provider full keys. All NPASS source IDs remain in
the output, with exact, connectivity-only, unresolved or held identity status.
Counts distinguish source IDs from distinct full keys; catalog overlap does not
add occurrence corroboration, toxicity labels or independent studies.

Use exact full keys for admitted joins. Connectivity matches are review candidates.
Catalog membership, taxon/reference occurrence, measured toxicity and plant phenotype
remain separate axes. Missing evidence never means synthetic origin, low hazard or
plant inactivity. A/B independent-study counts remain unknown pending lineage review.
