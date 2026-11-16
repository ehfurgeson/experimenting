# Historical PubChem retrieval prototype

This earlier standalone script resolves names/CIDs, retrieves PubChem properties
and PUG-View toxicity annotations, and writes `compound_summary.csv`,
`toxicity_long.csv` and raw JSON under its output directory. Inputs include
`chemicals_example.txt` and `hrac_groups_1_2_seed.csv`; dependencies are kept in
`requirements.txt`. Local `results/` is ignored and absent from a clone.

The maintained retrieval, caching, normalization and provenance implementation is
now the [agrotox pipeline](../pipeline/README.md). This prototype is retained to
explain the early acquisition workflow and seed selection. It is not needed for
the maintained analysis, and its outputs should not be substituted for validated
pipeline snapshot bundles. A new live run cannot guarantee the original API data
or reproduce historical scientific results.

For historical inspection, read `pubchem_toxicity.py` and its `--help`; running it
with chemical arguments makes live network requests. No prototype execution or
output migration is required for repository setup.
