# Components and workflow ownership

The repository supports toxicity-profile comparisons and differentiating chemical
properties toward safer bioherbicides. Known natural-product–protein interactions
remain a broader research objective. Target references and assay evidence provide
context; selection classifiers and screening scores do not demonstrate binding.

```text
preserved references + curated selection / identity decisions
    -> live acquisition (pipeline APIs; local preparation scripts)
    -> frozen PubChem / EPA / ChEMBL snapshots
    -> offline normalization, endpoint matching, evidence coverage
    -> cached analysis / presentation, structural screening, human review
```

`pipeline/src/agrotox/` owns reusable inputs, identity, storage, source adapters,
parsing, normalization, endpoint matching and provenance. `sources/` owns
transport; `parsers/` owns source parsing. Examples expose individual operations,
not a unified CLI. See [pipeline guides](../pipeline/README.md).

`analysis/` owns research implementations and depends on sibling `pipeline/`
through its own locked environment. It is currently a flat script collection:

| Family | Modules (all under `analysis/`) |
| --- | --- |
| Evidence and presentation | `rebuild`, `build_traits`, `endpoint_analysis`, `endpoint_coverage`, `distributions`, `compare`, `classifiers`, `stats`, `presentation`, `professor_notebook` |
| Chemistry and labels | `formula`, `structure`, `labels`, `structure_models`, `screen` |
| Review and diagnostics | `review_assays`, `stress`, `ablations` |
| Catalog screening | `rebuild_joint_catalog`, `catalog_screen_inventory`, `catalog_bulk_screen`, `plant_catalog_screen`, `joint_catalog_screen` |
| Catalog interpretation | `joint_catalog_diagnostics`, `joint_catalog_notebook` |

`analysis/rebuild.py` reads prepared local source caches and writes separate
products. It is not a complete acquisition/bootstrap process. Bare sibling imports,
`runpy` invocation and `analysis/*.py` code hashing depend on this layout.
`pipeline/examples/endpoints.yaml` is shared research configuration. Preserve these
paths until a separately tested packaging or portability change is justified.

`analysis/rebuild_joint_catalog.py` is a separate entry point for the current
catalog workflow. It verifies pinned public downloads, consumes the supplied
imports and tracked compact observations, then rebuilds exact-structure
features, models, the combined screen, and the notebook diagnostics. See the
[joint catalog rebuild](../analysis/docs/joint-catalog-notebook.md).

## Local preparation and earlier analysis

`experiments/01_curate_compounds.py`, `02_fetch_pubchem.py`, `03_fetch_epa.py`
and descriptor retrieval in `04_traits.py` are local preparation tools, absent
from a clone. The [data guide](data.md) records their inputs and manual gaps.
Earlier analysis has maintained replacements:

| Local script | Maintained replacement |
| --- | --- |
| `04_traits.py` | `analysis/build_traits.py` through `rebuild.py`; cached descriptors only |
| `05_distributions.py` | `analysis/distributions.py` |
| `06_compare.py` | `analysis/compare.py` |
| `07_classifiers.py` | `analysis/classifiers.py` |
| `08_epa_coverage.py` | `analysis/endpoint_coverage.py` |
| `endpoint_analysis.py`, `stats.py` | Same-named analysis helpers |

`experiments/stats.py` and `analysis/stats.py` were byte-identical at the cleanup
baseline. Other counterparts differ; this mapping assigns maintenance ownership,
not an assertion of output equivalence. Do not reintroduce descriptor network
retrieval into the offline rebuild.

## Test ownership

Run from the repository root:

```bash
uv run --directory pipeline --locked python -m pytest tests -q
uv run --directory analysis --locked python -X utf8 -m pytest tests -q
uv run --project pipeline ruff check pipeline
uv run --project analysis ruff check analysis
```

Pipeline tests include cross-component regressions in `test_analysis_rebuild.py`,
`test_analysis_presentation.py` and the three `test_experiment_*.py` modules;
the historical names now cover maintained analysis behavior. Their pipeline
environment and autouse Requests block in `pipeline/tests/conftest.py` are
intentional. Analysis tests cover chemistry, labels, scaffold models and diagnostics
with RDKit/scikit-learn. Synthetic fixture documentation stays beside
[pipeline fixtures](../pipeline/tests/fixtures/README.md).

Do not consolidate environments or relocate tests just to match directory names.
Frozen manifests contain absolute paths and code/lock hashes; retain historical
files unchanged. A source move would require updating consumers and compatibility
checks together.
