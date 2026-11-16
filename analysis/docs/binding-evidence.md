# Experimental protein–ligand structural evidence

The offline `binding_catalog.py` audits explicitly declared X-ray complexes and
exports their parent/bound chemical identities and protein construct sequences.
It is a small structural-evidence workflow, not an affinity predictor or a
validated natural-product binding dataset. Scientific interpretation and source
review remain separate from software identity checks.

## Inputs and command

Run from the repository root in the locked analysis environment:

```bash
uv run --project analysis --locked python analysis/binding_catalog.py \
  --resource YOUR_WORK/records.json --snapshots YOUR_WORK/sources \
  --output analysis/outputs/NEW_BINDING_CATALOG
```

The resource has a `records` list. Each record declares a unique nonempty
`interaction_id`, four-character uppercase `pdb_id`, `ligand_component_id`,
`parent_name`, `parent_snapshot`, `parent_bound_relationship`, a list of
`target_entity_ids`, `primary_doi`, `primary_source_file`, `source_locator`,
`natural_product_context` and `limits`. A hydrolysis relationship additionally
requires `relationship_locator`. All real research inputs remain ignored.

The snapshot directory contains raw RCSB Data API responses named
`PDB_entry.json`, `PDB_polymer_ENTITY.json`, `PDB_nonpolymer_ENTITY.json` and
`COMPONENT_chemcomp.json`. Supply all non-polymer entities listed by the entry
and every declared target polymer entity. `parent_snapshot` is a raw PubChem
PUG property JSON with exactly one result containing stereochemical `SMILES` and
`InChIKey`; multiple hits fail rather than choosing the first. The primary source
file must be local and contain the declared DOI. These textual/source declarations
are not independently authenticated scientific approval. Acquisition is separate;
the command performs no network calls.

## Checks and scientific meaning

The declared component must actually occur in the released experimental X-ray
entry; its primary citation DOI and protein entry/entity IDs must match. Positive
finite reported resolution is required. RCSB component and PubChem parent SMILES
must independently reproduce their respective full InChIKeys in RDKit. Existing
single-component carbon-structure eligibility applies. No salt stripping,
tautomer merging or first-hit identity selection is implicit.

`exact_parent` requires the same full InChIKey for parent and deposited ligand.
`source_reported_anhydride_hydrolysis` preserves different parent/bound structures
and checks that one anhydride opening yields the bound graph **without stereo**.
This checks chemical connectivity consistency, not reaction kinetics, occurrence,
protonation equivalence or complete stereochemical provenance. The source must
support the proposed relationship; the software cannot establish it from a formula
or a compound name alone. Other transformations require a separate implementation
and evidence review; they are not silently normalized.

Protein exports retain the target's source organism separately from expression
host, deposited construct sequence, chain labels, sequence hash and UniProt
mappings supplied by RCSB. A UniProt sequence version remains unknown unless
actually retrieved by a future workflow. The deposited construct is not asserted
to equal the current full-length protein or a weed ortholog. Merely appearing in a
complex does not assign a contact to every polymer entity or author chain.

`interactions.csv` contains experimental-complex evidence, identity/form checks,
resolution, revision and data-release metadata, DOI/locator and limits.
`protein_entities.csv` and `protein_sequences.fasta` retain the declared constructs.
The manifest hashes the exact loaded source bytes, code, locks and products and
records RDKit/Polars versions. Inputs must be separate from a new output directory;
validation occurs before product creation.

Affinity endpoint/value/unit remain null. Crystal preparation concentrations,
enzyme IC50 values, docking scores and geometric contacts are not Kd/Ki labels.
Natural-origin labels remain unknown: a paper's natural-product background is
retained for curation, not promoted to independently reviewed occurrence truth.
Rejected wrong-form/cofactor mappings are not negative-binding examples.

Focused checks:
`uv run --project analysis --locked pytest analysis/tests/test_binding_catalog.py -q`.

## First local pilot — 2026-11-12

Two primary sources and deposited complexes were inspected:

| Parent / deposited form | Structure | Protein source / mapping | Resolution |
|---|---|---|---:|
| Tentoxin / `TTX`, exact parent | [1KMH](https://www.rcsb.org/structure/1KMH) | Spinach chloroplast ATPase alpha/beta; P06450 / P00825 | 3.4 Å |
| (+)-Cornexistin / diacid `UP0` | [8CI0](https://www.rcsb.org/structure/8CI0) | Maize chloroplastic transketolase; Q7SIC9; expressed in E. coli | 1.902 Å |

The [tentoxin primary paper](https://doi.org/10.1073/pnas.052546099) describes an
alpha/beta-interface site involving beta Asp83 and alpha hydrophobic residues.
The full parent/deposited InChIKeys agree. The entry's released-experimental-data
flag is `N`; no independent density or refinement validation was performed. Its
0.05 mM complex-preparation concentration is not an affinity estimate.

The [cornexistin primary paper](https://doi.org/10.1002/chem.202300199) describes
binding of a diacid, presumably produced by anhydride hydrolysis. Parent
C16H20O6 and bound C16H22O7 retain different exact keys; anhydride-opening
connectivity agrees. The default structure-page ligand-interaction link selected
`8EL`, a thiamine-related cofactor. Inspecting the actual non-polymer entities
identified `UP0` as the inhibitor; trying the cofactor with the parent cornexistin
record fails the chemical relationship check. The cofactor is not a nonbinder.

The local companion curation retains **15 author-reported contact descriptions**,
without assigning calculated distances or mapping paper residue/monomer labels
onto current protein sequences. It also retains the paper's maize transketolase
**IC50 50 ±5 μM** as functional inhibition, with uncertainty definition and full
assay conditions unresolved. This is not a Kd/Ki or an IC50 assigned directly to
isolated `UP0`. No crop/weed selectivity or organism-level safety follows from a
crop-protein complex.

The pilot exports **two structural records and three sequences** (507, 498 and
688 residues). No model was fitted. Outputs are under local ignored
`analysis/outputs/binding-structural-pilot-2026-11-12-final/`. Source snapshots,
resource, exact first-run code, curation, acquisition failures/decisions and a
rendered parent/bound-form comparison are in
`experiments/binding-pilot-2026-11-12/`. The final catalog, companion curation and
figure manifests verify. The chemical figure was rendered and inspected.

Verification: **299 analysis tests and Ruff pass**. This verifies the software
contracts and the bounded source checks; independent scientific adjudication,
density inspection, original isolation evidence, residue-to-sequence mapping,
measured binding affinities, weed orthologs and external predictive validation
remain open.
