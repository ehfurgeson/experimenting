# Agrochemical Toxicity

A research project for collecting, harmonizing, analyzing, and ultimately modeling the toxicity of agrochemicals and plant-derived natural products, with particular emphasis on **chemical structure**, **herbicide mode of action**, and the distinction between **desired phytotoxic activity** and **off-target human or ecological toxicity**.

> **Historical checkpoint (six-herbicide/sixteen-natural-product stage; superseded):** The [pipeline](../pipeline/README.md) implements PubChem retrieval, endpoint standardization, coverage checks, and descriptive exploratory comparisons for six HRAC group 1/2 herbicides and sixteen natural products. See the historical presentation brief (no longer present) for a short explanation and initial findings. Multi-database integration, formal statistical analysis, and predictive modeling remain future work. Later sections retain the broader research roadmap. Current maintained overview: [repository README](../README.md) and [dated findings](../analysis/FINDINGS.md).

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Scientific Motivation](#2-scientific-motivation)
- [3. Relationship to the Larger Research Program](#3-relationship-to-the-larger-research-program)
- [4. Current Research Questions](#4-current-research-questions)
- [5. Current Scope](#5-current-scope)
  - [5.1 Immediate HRAC Group 1 and 2 Task](#51-immediate-hrac-group-1-and-2-task)
  - [5.2 Natural-Product Comparison Set](#52-natural-product-comparison-set)
  - [5.3 Longer-Term Chemical Scope](#53-longer-term-chemical-scope)
- [6. Current Project Files](#6-current-project-files)
- [7. Current PubChem Retrieval Prototype](#7-current-pubchem-retrieval-prototype)
  - [7.1 What the Script Does](#71-what-the-script-does)
  - [7.2 Current Outputs](#72-current-outputs)
  - [7.3 Current Limitations](#73-current-limitations)
- [8. Proposed Data Architecture](#8-proposed-data-architecture)
- [9. Compound Identity and Chemical Normalization](#9-compound-identity-and-chemical-normalization)
- [10. Toxicity Endpoints of Interest](#10-toxicity-endpoints-of-interest)
- [11. Toxicity Data Standardization](#11-toxicity-data-standardization)
- [12. Planned Data Sources](#12-planned-data-sources)
- [13. Exploratory Data Analysis](#13-exploratory-data-analysis)
- [14. Statistical Comparison: Natural Products vs. Herbicides](#14-statistical-comparison-natural-products-vs-herbicides)
- [15. Missingness and Dependence](#15-missingness-and-dependence)
- [16. Chemical Structure and QSAR Modeling](#16-chemical-structure-and-qsar-modeling)
- [17. Herbicide Targets, Resistance, and Cross-Species Context](#17-herbicide-targets-resistance-and-cross-species-context)
- [18. Proposed Repository Structure](#18-proposed-repository-structure)
- [19. Running the Current PubChem Script](#19-running-the-current-pubchem-script)
- [20. Data Quality and Reproducibility](#20-data-quality-and-reproducibility)
- [21. Important Scientific Caveats](#21-important-scientific-caveats)
- [22. Roadmap](#22-roadmap)
- [23. Current Progress Summary](#23-current-progress-summary)
- [24. Glossary](#24-glossary)

---

## 1. Project Overview

The goal of this project is to build a reproducible computational framework for evaluating the toxicity of chemicals relevant to weed management, with an eventual emphasis on determining whether **plant-derived compounds with useful herbicidal or allelopathic activity can be prioritized as safer alternatives to conventional agrochemicals**.

The project begins with data collection and exploratory analysis rather than immediately training a predictive model. The first priorities are to determine:

1. what toxicity information is available for the chemicals of interest;
2. which toxicity endpoints are sufficiently well represented for meaningful comparison;
3. how measurements can be standardized across databases, species, exposure routes, study designs, and units;
4. whether plant-derived natural products and conventional herbicides differ systematically in important toxicity endpoints; and
5. whether chemical structure and physicochemical properties can eventually be used to predict those endpoints for compounds with sparse or missing experimental data.

The eventual conceptual pipeline is:

```text
plant natural products
        ↓
candidate chemical structures
        ↓
desired agricultural / herbicidal activity
        ↓
toxicity characterization or prediction
      ↙                         ↘
 human / mammalian          ecological
     toxicity               toxicity
      ↘                         ↙
          comparative safety
                  ↓
         candidate prioritization
                  ↓
          experimental testing
```

This is not intended to reduce chemical safety to a single simplistic number. A future safety or prioritization score would need to preserve the distinction between different biological endpoints, uncertainty, exposure context, and data availability.

---

## 2. Scientific Motivation

Conventional herbicides are highly effective tools for weed control, but their use raises questions involving:

- toxicity to humans and other mammals;
- toxicity to aquatic organisms, pollinators, and other non-target species;
- environmental persistence and exposure;
- herbicide resistance;
- off-target biochemical effects; and
- the safety of repeated or widespread agricultural use.

Plant secondary metabolites and other natural products are a potential source of compounds with herbicidal activity. Allelopathic plants, for example, release chemicals that alter the germination, growth, physiology, or survival of neighboring plants. These molecules may serve directly as bioherbicides or as chemical leads for the development of new herbicides.

However, **natural origin is not equivalent to safety**. A plant-derived compound may be biodegradable or environmentally short-lived and still be toxic to mammals, aquatic organisms, insects, or non-target plants. Therefore, candidate natural herbicides need to be evaluated using the same toxicological discipline applied to conventional agrochemicals.

The central motivation of this project is therefore not simply:

> “Can natural products kill weeds?”

but rather:

> **“Can compounds with useful agricultural activity be identified that also have a favorable human-health and ecological toxicity profile?”**

---

## 3. Relationship to the Larger Research Program

This project is one component of a larger effort investigating **natural alternatives to agrochemicals that remain effective while also being safe**.

The larger research program includes multiple complementary components. One component is genomic / target-oriented: identifying which genes or proteins chemicals interact with, determining the biological functions of those targets, and examining target conservation or differences across organisms.

The present project is primarily the **chemical toxicity / data-analysis component**. Its role is to characterize chemicals themselves and answer questions such as:

- Which compounds have evidence for human or mammalian toxicity?
- Which compounds are toxic to fish, aquatic invertebrates, algae, pollinators, or other non-target organisms?
- How complete is the evidence base for each compound?
- Are natural products different from conventional herbicides after measurements are made comparable?
- Which chemical structures or molecular properties are associated with toxicity?
- Can toxicity be predicted for candidate natural products before experimental testing?

The target/genomic tables included in this repository provide an important connection between the toxicity work and the larger biological-target work, but **target information and organism-level toxicity are not interchangeable**. They are complementary sources of evidence.

---

## 4. Current Research Questions

The broad project is being developed around the following questions.

### Data availability

- How many compounds have measurements for each toxicity endpoint?
- Which endpoints have enough observations for statistically meaningful analysis?
- How much overlap exists among PubChem, EPA resources, and other toxicity databases?
- Are natural products systematically less studied than registered herbicides?

### Comparative toxicity

- Are acute mammalian toxicity values different between natural products and herbicides?
- Are natural products different from herbicides in acute aquatic toxicity?
- Do differences remain after accounting for molecular size, lipophilicity, or structural class?
- Are any apparent differences caused by testing patterns rather than biology?

### Chemical structure

- Which molecular descriptors are associated with particular toxicity endpoints?
- Can molecular fingerprints predict toxicity?
- Do structurally similar natural products and conventional herbicides have similar toxicity?
- Are there structural motifs associated with herbicidal activity but lower non-target toxicity?

### Biological targets

- How do herbicide targets vary across weeds, crops, humans, pollinators, and model organisms?
- Are toxicity patterns related to target conservation or potential cross-reactivity?
- Can chemical-target and chemical-toxicity information eventually be combined to improve candidate prioritization?

---

## 5. Current Scope

### 5.1 Immediate HRAC Group 1 and 2 Task

The immediate task motivating the first Python prototype came from a request to investigate **HRAC Group 1 and Group 2 herbicides** and develop a simple workflow that accepts a list of chemical names or PubChem CIDs and retrieves toxicity information.

The attached HRAC reference table identifies the two groups as follows:

| HRAC group | Primary target | Protein type | Representative herbicides in current table |
|---|---|---|---|
| **1** | Acetyl-CoA carboxylase (**ACCase**) | Enzyme | diclofop-methyl, sethoxydim, pinoxaden |
| **2** | Acetolactate synthase / acetohydroxyacid synthase (**ALS/AHAS**) | Enzyme | chlorsulfuron, imazethapyr, pyrithiobac |

The simplest initial smoke-test chemicals are therefore:

```text
diclofop-methyl
chlorsulfuron
```

The existing target-ID table also contains organism-specific context for these targets:

- **HRAC 1 / ACCase**
  - *Lolium rigidum* (annual ryegrass): NCBI protein accession `AAK62311.1` is listed as a partial sequence.
  - *Echinochloa crus-galli* (barnyard grass): accessions `HQ395758.1` and `HQ395759.1` are listed.
  - The table also records known or important ACCase residues and herbicide-resistance substitutions.

- **HRAC 2 / ALS/AHAS**
  - *Amaranthus palmeri* (Palmer amaranth): partial sequence records including `KT833339.1` and `MW361337.1` are listed.
  - *Amaranthus tuberculatus* (waterhemp): `ABM53021.1` is listed.
  - The table records known ALS resistance positions such as Ala122, Pro197, Trp574, and Ser653 in the relevant entries.

These target tables are useful biological context, while the current toxicity script addresses the complementary chemical-safety side of the project.

### 5.2 Natural-Product Comparison Set

The professor-requested initial natural-product examples include:

```text
citrulline
solanine
tricolorin A
azadirachtin
```

These are useful test cases because the retrieval workflow should not be designed only around well-studied registered herbicides. A robust system must also handle natural products that may have less regulatory toxicity data, different naming conventions, fewer standardized studies, or multiple records in chemical databases.

A larger natural-product panel can later be derived from the project’s allelopathy reference material. Candidate compounds mentioned in that literature include phenolic acids, coumarins, terpenoids, flavonoids, benzoxazinoids, sorgoleone, dhurrin, and other chemically identified plant metabolites.

Importantly, plant extracts and complex mixtures should generally be treated separately from isolated compounds when the goal is structure-based analysis. The preferred unit for the main computational dataset is a **chemically identifiable compound with a resolvable molecular structure**.

### 5.3 Longer-Term Chemical Scope

After the initial HRAC Group 1/2 prototype is validated, the chemical set can expand in several ways:

1. additional active ingredients from other HRAC groups;
2. the complete set of representative herbicides in the current HRAC table;
3. a curated list of allelochemicals and other plant-derived bioactive compounds;
4. natural-product-inspired herbicides or synthetic analogues of natural products; and
5. candidate structures supplied by the broader discovery project.

The long-term comparison should be reproducibly defined rather than based only on hand-selected “famous” herbicides.

---

## 6. Current Project Files

The current project context includes the following reference files.

### `Herbicide target table - HRACdb.csv`

A working HRAC mode-of-action reference table containing fields such as:

- HRAC group;
- target protein;
- protein type;
- representative herbicides;
- notes on confirmation of group assignment; and
- resistance-related context.

The table currently provides the immediate chemical context for HRAC Groups 1 and 2 and broader coverage of additional HRAC classes.

### `Herbicide target table - Final_TargetIDs.csv`

A curated target table for a subset of HRAC groups. Current columns include information such as:

- HRAC target/group;
- protein name;
- EC number;
- weed species;
- supporting DOI;
- NCBI protein identifiers;
- binding-site or important residues;
- resistance mechanisms;
- placeholders for crop, human, and bee orthologs;
- known Ki values; and
- resistance mutations.

The current file includes 13 HRAC target groups: `1, 2, 3, 4, 5, 6, 9, 10, 12, 14, 15, 22, 27`.

### `Herbicide target table - Weed_TargetIDs.csv`

A closely related working table containing weed target IDs, residues, resistance mechanisms, and supporting literature. It contains expanded target-site details for several entries.

### `Herbicide target table - SpeciesToTarget.csv`

A working cross-species reference table. It includes example crop/model organisms and non-target organisms such as:

- *Arabidopsis thaliana*;
- tomato;
- soybean;
- maize;
- rice;
- *Chlamydomonas reinhardtii*;
- yeast;
- bacteria;
- *Daphnia magna*;
- *Apis mellifera* (honeybee);
- *Caenorhabditis elegans*; and
- *Danio rerio* (zebrafish).

It also maps several priority weed species, including Palmer amaranth, waterhemp, kochia, horseweed, annual ryegrass, and barnyard grass.

This file may eventually support cross-species target-conservation or off-target analyses, but that work is distinct from the first toxicity-retrieval milestone.

### `Allelopathy_Potential_for_Green_Agriculture.md`

A project reference derived from *Allelopathy: Potential for Green Agriculture* (Mushtaq, Siddiqui, and Hakeem, 2020). It provides context for allelopathic plants, identified allelochemicals, weed-suppression mechanisms, and natural-product approaches to weed management.

### PubChem toxicity retrieval prototype

A Python script has been developed that accepts chemical names or PubChem CIDs and retrieves compound metadata plus the PubChem PUG-View `Toxicity` section.

---

## 7. Current PubChem Retrieval Prototype

### 7.1 What the Script Does

The current script is a **minimal PubChem toxicity retriever**. It is intentionally simple and serves as the first reproducible data-ingestion prototype.

Given one or more chemical names or PubChem CIDs, it:

1. resolves each query against PubChem;
2. retrieves basic chemical identity and structure fields;
3. requests the PubChem PUG-View `Toxicity` section;
4. recursively flattens nested PUG-View sections into a long-form table;
5. preserves source names, references, and URLs when available;
6. saves the original PUG-View JSON response for reproducibility;
7. records failed queries or missing toxicity sections; and
8. includes retry and request-throttling behavior.

Current PubChem structure/identity fields requested include:

```text
Title
MolecularFormula
MolecularWeight
SMILES
ConnectivitySMILES
InChI
InChIKey
IUPACName
```

The script accepts either positional queries or an input TXT/CSV file.

### 7.2 Current Outputs

For a run, the prototype produces:

```text
<output_directory>/
├── compound_summary.csv
├── toxicity_long.csv
├── errors.csv                 # only if errors occur
└── raw/
    ├── <CID>_toxicity.json
    └── ...
```

#### `compound_summary.csv`

Contains one resolved PubChem compound record per input query, including identifiers and basic structural metadata.

#### `toxicity_long.csv`

Contains flattened PubChem toxicity annotations. Current fields include:

```text
Query
CID
Title
SectionPath
Heading
InformationName
Value
Description
ReferenceNumber
SourceName
SourceURL
InformationURL
```

#### `raw/<CID>_toxicity.json`

Stores the original PubChem PUG-View response. Keeping raw responses is important because parsing rules will evolve and the raw source should not need to be re-downloaded every time processing logic changes.

#### `errors.csv`

Records compound-resolution or toxicity-retrieval failures rather than silently dropping them.

### 7.3 Current Limitations

The current prototype is an **ingestion tool**, not yet an analysis-ready toxicity database.

Most importantly, `toxicity_long.csv` still stores many values as PubChem annotation text. It does not yet reliably transform records into standardized columns such as:

```text
endpoint
species
organism_group
exposure_route
exposure_duration
value
qualifier
unit
```

For example, records corresponding conceptually to:

```text
Rat oral LD50 = 560 mg/kg
Fish 96 h LC50 = 2.4 mg/L
Daphnia 48 h EC50 = 7.8 mg/L
```

need to become separate machine-readable toxicity observations rather than only strings embedded in a general annotation table.

Other current limitations include:

- no EPA ECOTOX integration yet;
- no EPA ToxVal / ToxRefDB integration yet;
- no DTXSID resolution yet;
- no standardized CASRN field in the current prototype output;
- no endpoint-specific unit harmonization;
- no censoring/qualifier parser for values such as `<`, `>`, `<=`, or ranges;
- no study-level deduplication across sources;
- no explicit distinction between active ingredient, salt, metabolite, and formulation;
- no compound-group label such as `natural_product` vs. `herbicide` propagated through the pipeline; and
- no endpoint coverage analysis yet.

These are expected next-stage developments rather than defects in the purpose of the initial prototype.

---

## 8. Proposed Data Architecture

The long-term dataset should separate **compound identity**, **individual toxicity observations**, and **derived analysis tables**.

A proposed high-level flow is:

```text
                     INPUT CHEMICAL LISTS
                  ↙                         ↘
       natural products                 herbicides
                  ↘                         ↙
              compound identity resolution
                         ↓
      PubChem / CompTox identifiers + structures
                         ↓
              master compound table
                         ↓
       ┌─────────────────┴─────────────────┐
       ↓                                   ↓
 human / mammalian                   ecological
 toxicity sources                    toxicity sources
       ↓                                   ↓
        standardized study-level toxicity table
                         ↓
              endpoint coverage tables
                         ↓
               exploratory analysis
                         ↓
 natural-product vs. herbicide statistical comparison
                         ↓
           structure–toxicity modeling / QSAR
```

A useful processed data layout would be:

```text
data/
├── raw/
│   ├── pubchem/
│   ├── comptox/
│   ├── ecotox/
│   ├── toxval/
│   └── other/
│
├── interim/
│   ├── resolved_compounds/
│   └── parsed_toxicity/
│
└── processed/
    ├── compounds.parquet
    ├── toxicity_observations.parquet
    ├── human_tox.parquet
    ├── ecotox.parquet
    └── endpoint_coverage.parquet
```

Raw files should be treated as immutable whenever possible. Cleaning and standardization should happen in reproducible processing code.

---

## 9. Compound Identity and Chemical Normalization

Chemical identity is one of the most important technical problems in a multi-source toxicity project.

The desired identifier set is:

```text
internal_compound_id
preferred_name
CASRN
PubChem CID
DTXSID
InChIKey
InChI
canonical / connectivity SMILES
isomeric SMILES, when relevant
molecular formula
molecular weight
```

### Why multiple identifiers are necessary

Different databases may identify the same chemical using different systems. Names alone are unsafe because they can be ambiguous, outdated, misspelled, or associated with salts and mixtures.

The project should therefore resolve:

```text
CASRN
PubChem CID
DTXSID
SMILES
InChIKey
```

into a single internal compound identity wherever possible.

### Special cases requiring explicit handling

The pipeline should not automatically collapse:

- parent compounds and metabolites;
- free acids and salts;
- different stereoisomers;
- technical-grade active ingredients and pure compounds;
- formulated products and active ingredients;
- mixtures and isolated molecules.

For example, a commercial herbicide formulation may have a different toxicity profile from the active ingredient alone because of surfactants or other formulation components.

A future compound table should therefore include fields such as:

```text
substance_type
parent_compound_id
salt_or_form
formulation_flag
mixture_flag
structure_standardization_status
identity_review_status
```

---

## 10. Toxicity Endpoints of Interest

The project should initially focus on endpoints that are both biologically meaningful and sufficiently standardized across compounds.

### Highest-priority initial endpoints

| Domain | Endpoint | Typical comparison | Initial priority |
|---|---|---|---|
| Mammalian acute | Oral LD50 | rat, mg/kg body weight | Highest |
| Aquatic vertebrate | Fish LC50 | preferably 96 h, mg/L | Highest |
| Aquatic invertebrate | EC50 / LC50 | e.g. *Daphnia*, preferably 48 h, mg/L | Highest |
| Aquatic primary producer | Algal EC50 | growth inhibition, often 72–96 h, mg/L | Highest |

These four endpoints are strong candidates for the first natural-product-versus-herbicide comparison because they cover both human-health-relevant and ecological domains while remaining relatively interpretable.

### Additional endpoints of interest

| Domain | Endpoint | Notes |
|---|---|---|
| Mammalian chronic | NOAEL | Dose without observed adverse effect |
| Mammalian chronic | LOAEL | Lowest dose with observed adverse effect |
| Dose-response | BMD / BMDL | Benchmark dose and lower confidence bound |
| Pollinator | Honeybee LD50 | Oral and contact should remain distinct |
| Aquatic chronic | NOEC / NOAEC | Requires careful study-duration harmonization |
| Avian | Oral LD50 / dietary LC50 | Keep test type separate |
| Terrestrial plants | EC25 / EC50 | Particularly relevant for herbicides |
| Developmental/reproductive | Various | Potential later-stage human-health endpoints |
| Mechanistic bioactivity | Assay AC50 etc. | Useful predictors, **not equivalent to organism-level toxicity** |

### Endpoint definitions

- **LD50**: dose associated with 50% lethality in a test population.
- **LC50**: concentration associated with 50% lethality.
- **EC50**: concentration associated with a specified effect in 50% of the test population or response range.
- **NOAEL**: highest tested dose with no observed adverse effect.
- **LOAEL**: lowest tested dose at which an adverse effect is observed.
- **BMD**: modeled dose associated with a specified benchmark response.
- **BMDL**: lower confidence bound on the benchmark dose.

The same endpoint label is not automatically comparable across species, durations, routes, or effect definitions.

---

## 11. Toxicity Data Standardization

The preferred storage level is **one toxicity observation per row**, preserving enough information to understand what was actually measured.

A proposed schema is:

```text
observation_id
internal_compound_id
preferred_name
CID
CASRN
DTXSID
InChIKey
chemical_group

endpoint
endpoint_family
effect
species
species_common_name
organism_group
life_stage
sex
exposure_route
exposure_duration
exposure_duration_unit

value_raw
value_numeric
qualifier
unit_raw
value_standardized
unit_standardized
value_molar

study_id
reference
source_database
source_record_id
study_quality
formulation_flag
test_substance_notes
```

### Preserve the raw value

Raw values should never be discarded during standardization.

For example:

```text
> 5000 mg/kg
```

is not the same observation as:

```text
5000 mg/kg
```

The first is right-censored. A good parser would store:

```text
value_raw       = "> 5000 mg/kg"
qualifier       = ">"
value_numeric   = 5000
unit_raw        = "mg/kg"
```

Likewise, ranges should not automatically be replaced with their midpoint without an explicit analysis decision.

### Unit normalization

Potential standard units include:

```text
mammalian dose:       mg/kg body weight
daily chronic dose:   mg/kg/day
aquatic concentration: mg/L
bee dose:             µg/bee
```

For some analyses, values should also be converted to molar units to prevent molecular weight alone from driving apparent differences between compounds.

---

## 12. Planned Data Sources

### PubChem — current prototype source

Current use:

- chemical name/CID resolution;
- molecular formula and molecular weight;
- SMILES;
- InChI and InChIKey;
- IUPAC name; and
- aggregated toxicity annotations from PUG-View.

PubChem is particularly useful as an early aggregation and identity source. However, absence of a toxicity annotation in PubChem should **not** be interpreted as proof that no toxicity study exists.

### EPA CompTox / DSSTox — planned

Potential roles:

- DTXSID resolution;
- curated chemical identity;
- physicochemical data;
- cross-database mappings; and
- access to additional toxicological data products.

### EPA ECOTOX — planned

Expected to be a primary source for ecological toxicity records, particularly:

- fish;
- aquatic invertebrates;
- algae / aquatic plants;
- birds;
- terrestrial organisms; and
- other non-target species.

Its study-level nature makes species, duration, endpoint, effect, and test conditions important parts of the data model.

### EPA ToxVal / related toxicology resources — planned

Potential source for mammalian and human-health toxicity values such as points of departure, NOAELs, LOAELs, and related values.

### ToxCast / Tox21 — possible later mechanistic layer

High-throughput bioactivity can provide mechanistic predictors and potentially help connect chemical structure to pathway activity. These assay values should remain clearly separated from whole-organism toxicity measurements.

### Literature and specialized sources — as needed

Peer-reviewed primary studies may be required for compounds with sparse database representation, especially natural products. Such additions should retain full provenance and should not silently override curated database records.

---

## 13. Exploratory Data Analysis

EDA should occur **before** complex predictive modeling.

Initial questions include:

```text
How many unique compounds are present?
How many natural products and herbicides are present?
How many compounds have each endpoint?
How many observations exist per compound and endpoint?
How missing is each endpoint?
Which compounds are disproportionately well studied?
What are the endpoint distributions?
How many values are censored (< or >)?
Which species dominate each endpoint?
Which exposure durations dominate?
How much overlap exists across databases?
How often do different sources disagree?
Which chemical classes dominate the dataset?
How correlated are toxicity endpoints?
```

A central early deliverable should be an endpoint coverage matrix such as:

| Chemical | Group | Rat oral LD50 | Fish LC50 | Daphnia EC50 | Algal EC50 |
|---|---|---:|---:|---:|---:|
| Compound A | Natural product | ✓ | — | ✓ | — |
| Compound B | Natural product | ✓ | ✓ | — | ✓ |
| Compound C | Herbicide | ✓ | ✓ | ✓ | ✓ |

This table will strongly determine the appropriate downstream modeling strategy.

---

## 14. Statistical Comparison: Natural Products vs. Herbicides

The central comparative question is:

> **For compounds with herbicidal or allelopathic relevance, which standardized toxicity endpoints differ between plant-derived natural products and conventional herbicide active ingredients?**

### Avoid treating every database row as independent

A registered herbicide may have dozens or hundreds of toxicity measurements while an uncommon natural product may have only one. Comparing all study rows directly would allow highly studied chemicals to dominate the result and would create pseudoreplication.

A reasonable first-stage analysis is therefore:

1. tightly define endpoint/species/duration combinations;
2. standardize units;
3. log-transform concentration/dose measurements when appropriate;
4. summarize repeated measurements at the **compound level**;
5. compare compound-level distributions between natural products and herbicides;
6. report effect sizes and uncertainty, not only p-values; and
7. adjust for multiple endpoint comparisons.

For many toxicity measures, an analysis scale such as

```text
log10(toxicity value)
```

will be more appropriate than the raw scale because toxicity values often span multiple orders of magnitude.

### Later hierarchical analysis

Once enough observations are available, a hierarchical model may explicitly represent levels such as:

```text
compound
  ↓
species
  ↓
study
  ↓
exposure condition
  ↓
endpoint measurement
```

This allows study-level information to be used without pretending repeated measurements are statistically independent.

### Structural adjustment

Two related but scientifically different questions are:

1. **Are natural products less toxic than herbicides on average?**
2. **Are natural products less toxic than structurally or physicochemically similar herbicides?**

The second question is stronger because it can help distinguish an effect of “natural-product status” from differences in molecular properties.

---

## 15. Missingness and Dependence

Missing toxicity measurements are unlikely to be missing completely at random.

A compound may be tested because:

- it is commercially important;
- regulators require testing;
- it is produced at high volume;
- similar compounds raised concerns;
- prior evidence suggests toxicity;
- an organism is particularly relevant to its expected exposure; or
- the compound is simply easy to assay.

Thus:

```text
P(toxicity endpoint measured | chemical characteristics, use, regulatory history, prior evidence)
```

is unlikely to be constant.

This matters because a natural product with no fish LC50 cannot simply be treated as “non-toxic.” It may be **untested**.

Missingness should therefore be analyzed as a feature of the dataset itself. Potential analyses include:

- endpoint coverage by chemical group;
- number of studies per compound;
- probability of having an endpoint measured;
- coverage as a function of registration/commercial status;
- sensitivity analyses restricted to chemicals with comparable data coverage; and
- explicit missingness models if the final dataset is large enough.

Dependence is also important. Multiple values from the same study, species, laboratory, or compound are not independent observations.

---

## 16. Chemical Structure and QSAR Modeling

A longer-term goal is to predict toxicity from chemical structure.

At a high level, quantitative structure–activity/property relationship modeling can be written as:

```text
chemical structure + descriptors
                ↓
        toxicity endpoint
```

Potential molecular representations include:

- canonical or standardized SMILES;
- Morgan/circular fingerprints;
- molecular weight;
- logP / lipophilicity;
- topological polar surface area;
- hydrogen-bond donors and acceptors;
- rotatable bonds;
- aromatic ring counts;
- formal charge;
- heteroatom counts;
- functional-group indicators; and
- other RDKit descriptors.

### Modeling should be endpoint-specific

A single model should not casually combine:

```text
rat LD50
fish LC50
Daphnia EC50
algal EC50
```

as if they measured one quantity. Different endpoints represent different organisms and biological processes.

More defensible approaches include:

- separate models for each endpoint;
- carefully designed multi-task models; or
- a later composite prioritization framework that keeps uncertainty and endpoint meaning visible.

### Validation considerations

Random train/test splits can overestimate performance if very similar analogues occur in both sets. Structure-aware validation should eventually include approaches such as:

- scaffold splits;
- clustered chemical-space splits; and
- external validation when possible.

Modeling should begin only after endpoint definitions, chemical identity, and duplicated/censored data have been handled correctly.

---

## 17. Herbicide Targets, Resistance, and Cross-Species Context

The target tables create a second dimension of the project beyond bulk toxicity values.

Current target information includes:

```text
HRAC group
protein name
EC number
weed species
NCBI protein accession
important / binding-site residues
resistance mutations
resistance mechanisms
supporting DOI
```

Future extensions may add:

```text
crop ortholog
human ortholog
bee ortholog
sequence similarity
binding-site conservation
known Ki / affinity measurements
```

This creates opportunities to examine whether target conservation helps explain off-target toxicity or selectivity.

For example, a possible future workflow is:

```text
chemical
   ↓
herbicide target in weed
   ↓
orthologs in crop / bee / human / other species
   ↓
sequence + binding-site conservation
   ↓
possible cross-reactivity hypothesis
   ↓
compare with observed toxicity data
```

This should be treated as a hypothesis-generating complement to experimental toxicity data, not a replacement for it.

### Resistance context

The current tables also record target-site resistance mutations for several herbicide classes. This information is scientifically useful because it connects:

- herbicide mode of action;
- molecular binding sites;
- evolutionary response in weeds; and
- potential structure–target relationships.

Resistance analysis is not the immediate focus of the toxicity pipeline, but the data should be preserved because it may later support mechanistic modeling.

---

## 18. Proposed Repository Structure

The project can evolve toward the following organization:

```text
agrochemical-toxicity/
│
├── README.md
├── requirements.txt
├── pyproject.toml                 # optional future packaging
│
├── config/
│   ├── endpoints.yaml
│   └── sources.yaml
│
├── data/
│   ├── raw/
│   │   ├── pubchem/
│   │   ├── ecotox/
│   │   ├── toxval/
│   │   └── target_tables/
│   │
│   ├── interim/
│   │   ├── resolved_compounds/
│   │   └── parsed_toxicity/
│   │
│   └── processed/
│       ├── compounds.parquet
│       ├── toxicity_observations.parquet
│       └── endpoint_coverage.parquet
│
├── inputs/
│   ├── chemicals_hrac_1_2.csv
│   └── natural_products.csv
│
├── src/
│   ├── ingestion/
│   │   ├── pubchem_toxicity.py
│   │   ├── ecotox.py
│   │   └── toxval.py
│   │
│   ├── normalization/
│   │   ├── compounds.py
│   │   ├── endpoints.py
│   │   └── units.py
│   │
│   ├── features/
│   │   └── rdkit_descriptors.py
│   │
│   └── analysis/
│       ├── coverage.py
│       └── comparisons.py
│
├── notebooks/
│   ├── 01_compound_resolution.ipynb
│   ├── 02_endpoint_coverage.ipynb
│   ├── 03_toxicity_eda.ipynb
│   └── 04_structure_toxicity.ipynb
│
├── reports/
│   ├── figures/
│   └── tables/
│
└── tests/
    ├── test_pubchem_parser.py
    ├── test_units.py
    └── test_compound_resolution.py
```

This structure is aspirational; the current repository does not yet contain every component shown above.

---

## 19. Running the Current PubChem Script

The current prototype requires Python and the `requests` package.

A minimal environment is approximately:

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows
pip install requests
```

### Query chemicals directly

```bash
python pubchem_toxicity.py diclofop-methyl chlorsulfuron
```

A PubChem CID may also be supplied directly:

```bash
python pubchem_toxicity.py 9750
```

### Read queries from a file

```bash
python pubchem_toxicity.py --file chemicals.txt --out results
```

For CSV input, the current script reads chemical queries from the first column.

### Example initial test list

```text
diclofop-methyl
chlorsulfuron
citrulline
solanine
tricolorin A
azadirachtin
```

This test set deliberately mixes conventional herbicides with natural products so that compound-resolution and toxicity-data sparsity can be evaluated early.

### Example output

```text
results/
├── compound_summary.csv
├── toxicity_long.csv
├── errors.csv
└── raw/
    ├── <CID>_toxicity.json
    └── ...
```

### Recommended immediate testing workflow

For each test compound, verify:

1. Did PubChem resolve the intended chemical?
2. Is the molecular structure correct?
3. Are synonyms or ambiguous names creating incorrect matches?
4. Is a `Toxicity` section present?
5. Which endpoint terms appear?
6. Are toxicity values stored as structured numbers or prose?
7. Are species, duration, and route recoverable?
8. Which external sources are cited by PubChem?
9. Are natural products noticeably more data-sparse than the herbicides?

The answers should determine the design of the next parser rather than assuming in advance that all PubChem toxicity annotations follow one format.

---

## 20. Data Quality and Reproducibility

Reproducibility is a core design goal.

### Preserve raw source data

The current PubChem script already saves raw PUG-View JSON. The same principle should be applied to future sources where licensing and access conditions permit.

### Record provenance

Every processed toxicity observation should retain enough metadata to trace it back to its source:

```text
source_database
source_record_id
reference
DOI / PMID when available
retrieval_date
processing_version
```

### Do not silently overwrite raw measurements

Standardized values should be additional columns rather than replacements for raw values.

### Log transformations

Every transformation should be deterministic and documented. Examples include:

- identifier normalization;
- unit conversion;
- species-name normalization;
- endpoint mapping;
- duplicate handling;
- censoring parsing; and
- compound-structure standardization.

### Version endpoint definitions

A configuration file can eventually define accepted endpoint mappings. For example:

```yaml
fish_acute_lc50:
  endpoint: LC50
  organism_group: fish
  preferred_duration_hours: 96
  standardized_unit: mg/L
```

This makes analysis rules explicit rather than burying them inside notebooks.

### Add automated tests

Particularly important tests will include:

- known chemical name → expected CID;
- unit-conversion correctness;
- qualifier parsing;
- duplicate detection;
- endpoint classification; and
- regression tests using saved PubChem JSON examples.

---

## 21. Important Scientific Caveats

### Natural does not mean non-toxic

The comparison should never assume that a plant-derived molecule is safe because of its origin.

### Hazard is not the same as risk

An intrinsic toxicity value describes hazard under particular experimental conditions. Real-world risk also depends on exposure, dose, environmental fate, formulation, application rate, and other factors.

This project initially focuses primarily on **hazard/toxicity characterization**, not full regulatory risk assessment.

### Herbicides have stronger testing requirements

Registered herbicides are often tested much more extensively than obscure natural products. Greater evidence of adverse effects can therefore reflect greater testing intensity rather than intrinsically greater toxicity.

### Database absence is not evidence of safety

“No result found” should be stored as missing/unknown, not converted to zero toxicity.

### Endpoint names alone do not guarantee comparability

Two `LC50` records may differ in:

- species;
- exposure duration;
- life stage;
- temperature;
- formulation;
- test medium; or
- study design.

### Formulations and active ingredients are different objects

Commercial formulations can have different toxicity from the active ingredient alone. These records should be flagged rather than indiscriminately pooled.

### Plant toxicity is expected for herbicides

A candidate bioherbicide is intentionally phytotoxic. Therefore, strong toxicity to target weeds is not necessarily undesirable. The safety goal is **selectivity**: useful activity against weeds with acceptably low toxicity to humans, crops, pollinators, aquatic organisms, and other non-target species.

### Predictive models require applicability-domain awareness

A QSAR model trained primarily on conventional herbicides may not extrapolate reliably to structurally novel natural products. Model uncertainty and chemical-space coverage should be reported.

---

## 22. Roadmap

### Phase 0 — Project definition and reference collection

**Status: substantially underway**

- [x] Define broad goal: evaluate toxicity of agrochemicals and natural-product alternatives.
- [x] Identify chemical structure as an eventual modeling component.
- [x] Collect allelopathy/natural-product background material.
- [x] Assemble HRAC target/mode-of-action working tables.
- [x] Collect weed target protein IDs and resistance context for several HRAC groups.
- [x] Identify HRAC Groups 1 and 2 as the immediate prototype focus.

### Phase 1 — Minimal PubChem toxicity retrieval

**Status: prototype implemented**

- [x] Accept chemical names.
- [x] Accept PubChem CIDs.
- [x] Resolve basic PubChem structure/identity fields.
- [x] Retrieve the PUG-View `Toxicity` section.
- [x] Flatten annotations into CSV.
- [x] Preserve original JSON.
- [x] Preserve source/reference metadata when exposed by PubChem.
- [x] Add retries and request pacing.
- [x] Record failed queries.
- [ ] Run and manually review a defined HRAC 1/2 + natural-product smoke-test set.
- [ ] Document problematic name resolutions and ambiguous compounds.

### Phase 2 — Standardized PubChem toxicity parser

**Status: planned next step**

- [ ] Identify recurring PubChem toxicity annotation patterns.
- [ ] Parse LD50, LC50, EC50, NOAEL, LOAEL, and related endpoints.
- [ ] Extract species.
- [ ] Extract exposure duration.
- [ ] Extract exposure route.
- [ ] Parse numeric qualifiers (`<`, `>`, ranges, approximate values).
- [ ] Standardize units.
- [ ] Preserve raw annotation text beside parsed values.
- [ ] Add parser unit tests using stored raw JSON.

### Phase 3 — Master compound table

**Status: planned**

- [ ] Create stable internal compound IDs.
- [ ] Add CASRN.
- [ ] Add DTXSID.
- [ ] Normalize InChIKey/SMILES.
- [ ] Review salts, stereochemistry, metabolites, and mixtures.
- [ ] Add `natural_product` / `herbicide` classification.
- [ ] Preserve source plant or HRAC group metadata.

### Phase 4 — EPA data integration

**Status: planned**

- [ ] Import or query ECOTOX records.
- [ ] Import ToxVal / relevant mammalian toxicity data.
- [ ] Connect records through harmonized chemical IDs.
- [ ] Deduplicate overlapping source records where appropriate.
- [ ] Retain source-specific provenance.

### Phase 5 — Endpoint coverage and EDA

**Status: planned**

- [ ] Build compound × endpoint coverage matrix.
- [ ] Compare missingness between natural products and herbicides.
- [ ] Plot endpoint distributions.
- [ ] Characterize species and duration distributions.
- [ ] Quantify database overlap.
- [ ] Identify endpoints with adequate sample size.

### Phase 6 — Natural-product vs. herbicide comparison

**Status: planned**

- [ ] Define comparable endpoint strata.
- [ ] Aggregate repeated observations appropriately.
- [ ] Analyze log-scale toxicity distributions.
- [ ] Estimate group differences and effect sizes.
- [ ] Correct for multiple testing.
- [ ] Perform sensitivity analyses for study coverage and censoring.
- [ ] Explore hierarchical models when sample size supports them.

### Phase 7 — Structure descriptors and QSAR

**Status: future**

- [ ] Standardize molecular structures.
- [ ] Calculate RDKit descriptors.
- [ ] Calculate molecular fingerprints.
- [ ] Visualize chemical space.
- [ ] Build endpoint-specific baseline models.
- [ ] Use structure-aware validation.
- [ ] Quantify predictive uncertainty.
- [ ] Evaluate whether natural-product/herbicide differences persist after structural adjustment.

### Phase 8 — Target/toxicity integration

**Status: future**

- [ ] Complete crop/human/bee ortholog mapping where relevant.
- [ ] Characterize target conservation and important residues.
- [ ] Integrate known resistance mutations.
- [ ] Compare target conservation with observed non-target toxicity.
- [ ] Explore joint structure–target–toxicity models.

### Phase 9 — Candidate prioritization

**Status: long-term**

Develop a transparent framework for prioritizing natural-product candidates based on multiple dimensions such as:

```text
desired herbicidal activity
+ non-target toxicity profile
+ uncertainty / data coverage
+ environmental considerations
+ chemical novelty
+ predicted selectivity
```

Any future “safety score” should be interpretable and should not hide major endpoint-specific hazards behind a single average.

---

## 23. Current Progress Summary

### Available now

- A defined scientific problem centered on agrochemical and natural-product safety.
- A larger project context connecting chemical toxicity with biological targets.
- A curated allelopathy/natural-product reference document.
- An HRAC mode-of-action table with representative herbicides.
- Weed target-ID and resistance-context tables for multiple HRAC targets.
- A cross-species reference table for crops, weeds, model organisms, and non-target species.
- A concrete immediate focus on **HRAC Group 1 (ACCase)** and **HRAC Group 2 (ALS/AHAS)** herbicides.
- Initial conventional-herbicide test compounds such as **diclofop-methyl** and **chlorsulfuron**.
- Initial natural-product test compounds including **citrulline, solanine, tricolorin A, and azadirachtin**.
- A working first-pass Python script for PubChem compound resolution and toxicity-annotation retrieval.
- Raw PubChem response preservation for reproducibility.

### Not yet complete

- A standardized endpoint parser.
- An analysis-ready toxicity observation table.
- A unified PubChem/CompTox/ECOTOX/ToxVal chemical identity layer.
- Systematic endpoint coverage statistics.
- Formal natural-product vs. herbicide hypothesis tests.
- RDKit descriptors or fingerprints.
- QSAR/predictive toxicity models.
- A final safety or candidate-prioritization framework.

The immediate objective is therefore **data engineering and validation**, not model complexity. The highest-value next milestone is to convert a small, manually checked set of PubChem records into a reliable standardized toxicity schema before scaling to hundreds or thousands of compounds.

---

## 24. Glossary

### ACCase
**Acetyl-CoA carboxylase.** Target associated with HRAC Group 1 herbicides in the current project tables.

### Allelochemical
A chemical released or produced by an organism, particularly a plant, that influences another organism. In this project, plant allelochemicals are of interest as potential herbicidal leads.

### ALS / AHAS
**Acetolactate synthase / acetohydroxyacid synthase.** Target associated with HRAC Group 2 herbicides in the current tables.

### BMD / BMDL
**Benchmark dose / benchmark dose lower confidence limit.** Model-based toxicological points of departure.

### CASRN
Chemical Abstracts Service Registry Number.

### CID
PubChem Compound Identifier.

### DTXSID
DSSTox Substance Identifier used by EPA CompTox resources.

### EC50
Concentration associated with 50% of a specified biological effect.

### HRAC
Herbicide Resistance Action Committee. HRAC groups classify herbicides by mode/site of action.

### InChIKey
A fixed-length hashed representation derived from an International Chemical Identifier (InChI), useful for cross-database chemical matching.

### LC50
Concentration associated with 50% lethality in the test population.

### LD50
Dose associated with 50% lethality in the test population.

### LOAEL
Lowest observed adverse effect level.

### NOAEL
No observed adverse effect level.

### NOEC / NOAEC
No observed effect concentration / no observed adverse effect concentration.

### QSAR
Quantitative structure–activity relationship. A modeling framework connecting molecular structure or descriptors to a biological activity or property.

### SMILES
Simplified Molecular Input Line Entry System, a text representation of molecular structure.

---

## Project Philosophy

The guiding principle of this repository is:

> **Collect first, standardize carefully, understand the missingness, compare like with like, and only then model.**

The value of the project is not simply in downloading large toxicity databases or fitting a high-performing machine-learning model. The central challenge is creating a defensible bridge between **chemical identity, biological target, experimental toxicity, chemical structure, and uncertainty** so that potentially useful natural agrochemicals can be evaluated on both efficacy and safety.
