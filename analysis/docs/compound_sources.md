# Compound expansion evidence

Sources checked 2026-10-27. This is an acquisition assessment, not a claim that
unreviewed database membership supplies activity ground truth. The present
176-compound selection has no separate reviewed activity/origin label file.

## Herbicide identities

[HRAC's 2026 classification](https://hracglobal.com/tools/2026-hrac-global-herbicide-moa-classification)
provides an active-ingredient master list in XLSX, with and without molecular
structures, plus the classification poster and revision report. This is the
most direct source for extending the current 60-herbicide selection and
preserving mode of action. The master list is broader than a few representatives
per HRAC group; it is not a balanced bioactivity training set.

Acquire a dated copy, preserve active-ingredient name, HRAC group and source row,
then resolve exact structures through the existing identity pipeline. Review
salts, esters, stereochemistry, mixtures and parent identities before deduplicating.
HRAC inclusion supports recognized herbicide use, but does not supply a comparable
assay dose, species and inactive control for the current reviewed-activity schema.
Do not label these as synthetically originating merely because they are marketed.

[WSSA's herbicide resources](https://wssa.net/weed/herbicides/) provide names,
structures and classification links for cross-checking identity. They are a
complementary authority, not an independent replicate of an HRAC label.

## Natural compound candidates

| Source | Acquisition route and retained evidence | Appropriate role | Limits |
|---|---|---|---|
| [COCONUT downloads](https://coconut.naturalproducts.net/download) | Versioned CSV/SDF exports; archive release, checksum, COCONUT ID, structure, original source and occurrence references where available | Broad structure library for later screening and diversity sampling | A natural-product collection is not a labeled herbicide assay; inspect provenance before asserting natural occurrence |
| [LOTUS](https://lotus.naturalproducts.net/) and its [primary paper](https://elifesciences.org/articles/70780) | Structure–organism–reference records via the portal/Wikidata; freeze query results and retain DOI, taxon, structure identifiers and references | Natural-occurrence evidence and traceable literature leads | Occurrence is not activity or inactivity; overlapping sources must be deduplicated |
| [KNApSAcK Core](https://www.knapsackfamily.com/knapsack_core/top.php) | Search by metabolite, organism, formula, C_ID, CAS, InChIKey or SMILES; retain C_ID, species and underlying reference | Targeted occurrence checking and literature discovery | Public query access does not establish unrestricted bulk reuse; verify snapshot terms and provenance before automated bulk acquisition |

The COCONUT download page currently offers the **October 2026** release,
including CSV and SDF, and states CC0 licensing. Its database “active/inactive”
dump terminology must not be interpreted as a herbicidal assay outcome. The
[COCONUT 2.0 primary publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC11701633/)
describes the curated collection and archived data.

LOTUS defines natural products by documented structure–organism relationships;
its paper documents CC0 dissemination and frozen snapshots in the
[LOTUS Zenodo community](https://zenodo.org/communities/the-lotus-initiative).
Archive an exact export instead of depending on a changing live query.

KNApSAcK Core reports 63,735 metabolites and 159,606 metabolite–species pairs,
last updated July 3, 2026. The [legacy download page](https://www.knapsackfamily.com/KNApSAcK/)
lists a 2008 package; do not mistake that for a current Core snapshot.
No current bulk export or reuse permission was established in this review.

These three sources should initially be an **unlabeled screening pool**, not
negative controls. Natural occurrence can be recorded independently once its
references are checked. Natural herbicides remain natural and active at once.

## Plant bioactivity and tested negatives

The primary study [A large-scale crop protection bioassay data set](https://www.nature.com/articles/sdata201532)
describes crop-protection literature deposited in ChEMBL, including organism-level
herbicidal measurements. Its suggested starting point is to search assay
descriptions for “herbicidal” and inspect the returned assays. The
[ChEMBL search guide](https://www.ebi.ac.uk/training/online/courses/chembl-quick-tour/accessing-chembl-data/searching-using-the-web-interface/)
and [web-service documentation](https://www.ebi.ac.uk/chembl/api/data/docs)
provide retrieval routes. Prefer this activity source for comparable tested
actives/inactives over inferring labels from NP database absence.

[PubChem BioAssay AID 389133](https://pubchem.ncbi.nlm.nih.gov/bioassay/389133)
is a concrete plant-growth assay lead (Amaranthus growth inhibition at 100 µM).
It is a curation lead, not an imported label or proof that all its records are
suitable negatives. Trace its original paper, units, qualifiers, species,
controls, duration and measured outcomes. ChEMBL and PubChem can mirror the same
publication: deduplicate at publication/assay/compound level before splitting.

An acceptable negative must be tested under a defined plant assay policy with
adequate exposure and controls. “Not registered”, “not found”, mammalian
nontoxicity, target binding alone, and unknown activity do not qualify.
Choose a biologically coherent endpoint and threshold before curation; record
species, dose/concentration, duration, route, units and outcome alongside the
primary citation. A string policy identifier does not establish comparability.
Conflicting assays need review rather than averaging away species dependence.

## Readiness for expansion

The structural command already accepts CSV/Parquet lists with `compound_id`
and SMILES, without toxicity or PubChem resolution. Keep source-specific
metadata in a separate provenance table keyed by compound ID, and preserve
original formulas/InChIKeys for identity checks. `--candidates` writes explicit
blocked states while reviewed activity models lack support.

Before broad screening, obtain reviewed positive and negative plant-activity
examples, including natural actives and tested natural inactives, across enough
scaffolds for validation. Reserve independent compounds/publications as an
external check. Evaluate label policy, balanced accuracy, precision–recall,
calibration and similarity domain before choosing a model; the current formula
selection result is not that acceptance check. Only then freeze a natural-product
release and score it in batches, preserving IDs, model/input hashes and review
flags. Scaling to an entire collection will need a batch interface: the current
command loads the supplied candidate list in memory and uses direct pairwise
training similarity, so it is intended for reviewed subsets initially.

No full external collection was downloaded or appended to training here. This
follows the requested order—establish reliable activity classification before
large-scale natural-product screening—and avoids manufacturing negative labels.

## Screening heuristic references

[Lipinski and colleagues](https://pubmed.ncbi.nlm.nih.gov/11259830/) concern oral
solubility/permeability; transplanting their ranges to agrochemicals is a
hypothesis to assess, not an activity test.
[Tice (2001)](https://doi.org/10.1002/1526-4998(200101)57:1%3C3::AID-PS269%3E3.0.CO;2-6)
examines agrochemical screening properties. The implemented numerical proxy
follows the explicitly reported [2022 primary screening study](https://www.mdpi.com/2073-4395/12/7/1635),
using RDKit definitions. The original Tice full text was not retrievable in this
review, so original-calculator equivalence is not asserted.
[Avram et al. (2014)](https://link.springer.com/article/10.1186/s13321-014-0042-6)
provides an additional primary comparison of pesticide-likeness methods.

[Ertl and Schuffenhauer (2009)](https://link.springer.com/article/10.1186/1758-2946-1-8)
describe the fragment/complexity synthetic-accessibility heuristic. The actual
implementation is [RDKit's bundled SA scorer](https://github.com/rdkit/rdkit/blob/master/Contrib/SA_Score/sascorer.py)
with its packaged fragment scores. Neither SA nor any rule violations become
activity labels. Exact locked versions are stored with local model products.

## Measured assay acquisition checkpoint — 2026-10-28

The [structural validation checkpoint](structural_validation_check.md) now
documents a bounded pipeline acquisition from ChEMBL_37: 14 assays from separate
publications, 157 activity records and 154 unique structures (28 scaffolds).
The local raw bundles preserve source values, inequality qualifiers, structures,
publication records, request parameters and database version. Review exports
retain source hashes; no activity or origin labels were attached automatically.

The acquisition adds 149 structures outside the existing selection, but more
records did not establish sufficient independent negative-bearing scaffolds.
A source-reported response-band pilot has insufficient support for five/three
folds and poor two-fold performance. Cross-assay dose, species, timing, units,
publication duplication and response thresholds still require explicit review.
The pipeline entry point is `agrotox.chembl.fetch_assay`; raw and generated
artifacts remain ignored under `analysis/outputs/chembl-2026-10-28/`.

## Dietary comparator review pilot — 2026-11-04

`analysis/resources/dietary_candidate_seeds.tsv` supplies **40 public candidate
names** with food-use references and explicit caveats: 20 amino acids, six sugars,
five polyols, seven fatty acids and two organic acids. This is a deliberately small
review pilot, not 200 verified safe compounds. The amino-acid source is
[21 CFR 172.320](https://www.ecfr.gov/current/title-21/section-172.320), which sets
conditions for nutrient addition. Other rows cite specific food-use provisions or
FDA GRAS notices. The fructose/maltose references concern mixtures (HFCS/malt
syrup); those rows explicitly require exact-compound dose review. GRAS notices
apply to proposed uses, not unlimited exposure. High-dose safety, natural-occurrence
references and plant activity remain unreviewed for every row.

The source check identified a substantive counterexample to generic benign labels:
[the EPA registration-review table](https://downloads.regulations.gov/EPA-HQ-OPP-2021-0336-0002/content.pdf)
lists caprylic/capric acids in herbicide products despite their edible-source fatty
acid food-use provision. They are retained on **hold** as rejected presumed plant
negatives. Lauric acid is conservatively held for biological-activity review, not
claimed to be a registered herbicide. Xylitol has a separate
[FDA dog-toxicity warning](https://www.fda.gov/animal-veterinary/animal-health-literacy/paws-xylitol-toxic-dogs).
These examples show why the comparison needs separate human dietary exposure,
non-target hazard and plant-response axes. The seed caveats are a source review
by the analysis workflow, **not completed human adjudication**.

Acquire identities explicitly, then rebuild offline (fresh output paths):

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis python analysis/dietary_candidates.py --fetch --snapshots analysis/outputs/dietary-pubchem-new
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis python analysis/dietary_candidates.py --snapshots analysis/outputs/dietary-pubchem-new --features analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet --output analysis/outputs/dietary-review-new
```

The online step retains timestamped query URLs and full PubChem property responses
in numbered JSON snapshots. Retries cover transient HTTP errors; partial acquisition
remains preserved if a later request fails. A failed or interrupted acquisition is
not a complete bundle. Offline build requires one unique snapshot per seed name,
a single CID/property record, valid single-component RDKit chemistry, exact
PubChem/RDKit InChIKey agreement and no duplicate candidate InChIKeys. Identity
agreement verifies internal structural consistency; a person must still check name,
stereoisomer, anomer and source-record meaning. New name resolution can change.

Products are `candidates.tsv` (exactly name, PubChem CID, SMILES, InChIKey),
`review.csv` (citations, caveats, identity status, blank dose/population/reviewer/
decision fields), `features.parquet` (2048-bit Morgan vectors, descriptors, formulas,
scaffolds; **all model targets null**), `overlaps.csv` (exact canonical or first-block
InChIKey matches to existing chemistry) and a hash manifest. Holds remain in the
four-column candidate export for transparent review; it is not a training-label
file. Exact matching does not cover every salt, tautomer or stereochemical issue.
The 4 November local pilot verified all 40 structures, found 29 in the shared
ACYCLIC scaffold group and identified L-proline already in the natural-product
selection. Do not place shared identities into different training/test roles.

Before accepting any comparator, save a versioned copy of `review.csv`; specify
species/population, dose with units, exposure route/duration and primary safety
reference, document natural occurrence separately, and have the researcher sign
and decide each row. Keep the frozen template unchanged. If the target is plant
inactivity, obtain tested-negative plant assays rather than converting dietary
use to activity=0. Broaden scaffold/family diversity after reviewing this pilot;
adding many closely related nutrients does not create independent validation.

The [preliminary automated review](dietary-triage.md) now acquires PubChem hazard/
toxicity records and dated official food-use documents, then prioritizes the
worksheet using inspectable rules, textual leads and explicit evidence gaps.
Its provisional dietary shortlist is a review aid, not accepted safety or plant
activity truth; original candidate and human-review files remain unchanged.

## Expanded user-verified dietary list — 2026-11-05

The local `notes/plant_animal_food_compounds_200.tsv` contains 200 distinct names,
PubChem CIDs and supplied InChIKeys. The user reports these compounds verified
benign. Its four columns contain identity data, not the supporting exposure,
reviewer or source records. Preserve the assertion and its scope separately from
what the structural audit establishes; do not infer plant inactivity from it.

A fresh offline audit at
`analysis/outputs/food-comparator-200-audit-2026-11-05/` reproduces all 200 supplied
SMILES-to-InChIKey pairs. All 200 have 2048-bit Morgan fingerprints; 192 have
supported formula features. Eight charged records are unsupported by the current
formula workflow. PubChem CID-to-structure correspondence was not independently
re-fetched, and this is not an independent benignity assessment.

All 40 earlier pilot identities are included: 160 additional full-key identities.
There are 43 scaffold groups, with 98/200 compounds sharing ACYCLIC. Sixteen exact
full-key matches occur with the original selection (17 including connectivity-only
matches); none occur with the 154 assay candidates. Match counts refer to distinct
new-list rows, not pairwise overlap records. The 45 connectivity matches to the
40-compound pilot include stereochemical alternatives and are not 45 exact matches.

Products: `audit.json`, `identity_checks.csv`, `overlaps.csv`, `features.parquet`
and the executed `audit.py`, with input/code/output hashes and RDKit/Polars versions
in `manifest.json`. Biological target columns remain null; no classifier was fitted.
The source TSV, prior review worksheets and frozen model bundles were unchanged.
To reproduce locally, copy the retained `audit.py` into a fresh empty directory
under `analysis/outputs/` and run it with `analysis/.venv/bin/python`. It requires
the original TSV and three earlier feature bundles recorded in its manifest.
Do not rerun into the frozen audit directory.

The [findings notebook](../../notes/notebooks/findings.py) verifies these output
hashes and the current TSV hash, then presents a concise opening update and a
section 6.1 with scaffold counts and interactive identity/overlap tables. Older
40-compound pilot sections remain historical. Next retain cited dose/population/
duration/reviewer decisions, check CIDs, reconcile overlap and define whether the
next model predicts dietary-comparator membership or measured plant response.
