# Binding pilot — 12 November 2026

Start with the [maintained contract/checkpoint](../../analysis/docs/binding-evidence.md).
The final catalog is `analysis/outputs/binding-structural-pilot-2026-11-12-final/`.
Source acquisition and records are local, ignored and separate from frozen human
origin/activity labels and toxicity datasets.

## What worked

- Primary papers plus RCSB entry/entity/component responses provide two traceable
  experimental complexes and three deposited protein sequences with source/host
  distinction, UniProt mapping, revision and sequence hashes.
- Tentoxin's parent and depositedTTX full InChIKeys agree.
- Cornexistin parent andUP0 differ, as expected for the paper's proposed anhydride
  hydrolysis. A one-opening graph check reproduces the bound connectivity without
  asserting complete stereo or mechanistic provenance.
- The 15 author-reported contact records preserve paper residue and monomer labels
  without inventing sequence mappings or distances.
- Functional IC50=50+/-5micromolar for added cornexistin against maizeTK and
  tentoxin0.05mM complex-preparation concentration are separate quantity roles.
  No Kd/Ki was assigned. Model fits:0.
- Maintained software:299 analysis tests passed and Ruff passed.

## What did not work / assumptions

- The default8CI0 ligand-interaction URL led to8EL, a bound thiamine-related
  cofactor. It is not the cornexistin inhibitor. The actualUP0 entity was recovered
  from the non-polymer inventory. `curation-v1/wrong_cofactor_rejection.json`
  records the failed cofactor substitution; no partial product was created.
  This is an identity error, not evidence that the cofactor does not bind.
- Parent names are cross-checked against PubChem but original natural-isolation
  evidence has not received independent review. Natural-origin labels remain
  unknown in the catalog. Bound diacid occurrence is not independently established.
- 1KMH is3.4A and has experimental-data-released flagN. Neither complex received
  independent density/refinement inspection. Entry metadata do not prove crystal
  quality or model accuracy.
- Paper residue numbering has not been mapped to the construct sequences. UniProt
  sequence versions and validated weed orthologs remain unknown. E.coli is the
  expression host for8CI0; Zea mays is the target-protein source.
- The two positive complexes cannot train a binding classifier; there are no
  measured nonbinder controls or a harmonized affinity dataset.

## Files and reproduction

`fetch.py` and `fetch_bound_form.py` acquire only the declared public sources;
`records.json` defines the two complexes and source relationship assumptions.
Use fresh source paths before retrieval reruns. Build offline with:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline \
  python analysis/binding_catalog.py --resource experiments/binding-pilot-2026-11-12/records.json \
  --snapshots experiments/binding-pilot-2026-11-12/sources \
  --output analysis/outputs/REPLACE_WITH_FRESH_DIRECTORY
```

`curate_contacts.py` creates the manual source-linked companion tables and executes
an actual wrong-cofactor failure check; it requires a fresh curation directory.
`draw_forms.py` builds the [chemical form comparison](figures-v1/bound_forms.svg).
The original preliminary catalog is retained; its exact code is preserved as
`binding_catalog_initial_run_source.py`. The canonical final catalog includes an
additional required-provenance-field validation and uses the maintained code.

Next: independently check original isolation and deposited density/ligand quality;
map author residue numbers to target constructs; add compatible measured binding
or functional assays while retaining their different endpoint meanings. Do not
score safer candidates from this pilot or fill unknown Ki/ortholog fields by analogy.
