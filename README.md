# Agrochemical toxicity

Study toxicity profiles of synthetic herbicides and natural products, identify
differentiating properties, and characterize known natural-product–protein binding
interactions to support discovery of safer bioherbicides. Deliverables are analyzed
datasets, reproducible computational workflows and a semester presentation.

The maintained workflows currently cover evidence retrieval, toxicity-profile
exploration, structural selection classification and assay-review preparation.
Protein-binding characterization remains a research goal; these workflows do not
establish it. Evidence availability measures coverage, measured toxicity needs
comparable study context, structural selection labels describe curation, and
herbicidal activity requires independent review. Natural origin alone does not
establish safety.

| Task | Start here |
| --- | --- |
| Understand the project and code | [Documentation index](docs/README.md), [architecture](docs/architecture.md) |
| Use retrieval/normalization APIs | [Pipeline quickstart](pipeline/README.md) |
| Rebuild cached analysis or open the notebook | [Analysis quickstart](analysis/README.md) |
| Recreate the catalog-wide plant and toxicity screen | [Joint screen and notebook quickstart](analysis/docs/joint-catalog-notebook.md) |
| Read current research checkpoints | [Dated findings](analysis/FINDINGS.md), [result inventory](docs/results.md) |
| Review compound activity/origin | [Researcher label guide](analysis/docs/label_review_guide.md) |
| Obtain or prepare inputs | [Data and provenance guide](docs/data.md) |

Requires Python **3.12+** and **uv**. From the repository root, set up each locked
environment separately and run the offline suites:

```bash
uv sync --project pipeline --locked
uv run --directory pipeline --locked python -m pytest tests -q
uv sync --project analysis --locked
uv run --directory analysis --locked python -X utf8 -m pytest tests -q
```

Environment setup may download dependencies. Offline tests need neither research
caches nor credentials. Live PubChem/ChEMBL acquisition uses network access;
EPA CompTox acquisition needs `COMPTOX_API_KEY`. Cached analysis uses existing
bundles and makes no retrieval requests.

| Location | Role |
| --- | --- |
| `pipeline/` | Maintained `agrotox` package, examples, offline tests, locked environment |
| `analysis/` | Maintained research scripts, notebook, policies, tests, locked environment |
| `docs/` | Navigation, architecture, data and result catalogs |
| `herbicide_target_tables/` | Preserved [source spreadsheet exports](herbicide_target_tables/README.md) |
| `Allelopathy_Potential_for_Green_Agriculture.md` | Literature reference; see [catalog](docs/references.md) |
| `prototype/` | [Historical standalone retrieval prototype](prototype/README.md) |
| `experiments/`, `notes/` | Ignored local preparation, provenance and research history |

**Recreate the current catalog analysis** with the tracked rebuild driver, the
supplied `data_imports/` folder and checksum-pinned public downloads. Compact
research inputs are tracked under `analysis/resources/`. Historical runs can
require their own archived inputs. Generated runs and local data stay outside
Git. [Rebuild the catalog analysis](analysis/docs/joint-catalog-notebook.md) ·
[Historical data guide](docs/data.md)
