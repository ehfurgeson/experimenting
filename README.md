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
| Read current research checkpoints | [Dated findings](analysis/FINDINGS.md), [result inventory](docs/results.md) |
| Review compound activity/origin | [Researcher label guide](analysis/docs/label_review_guide.md) |
| Obtain or prepare inputs | [Data and provenance guide](docs/data.md) |

Requires Python **3.12+** and **uv**. From the repository root, set up each locked
environment separately and run the offline suites:

```bash
uv sync --project pipeline --locked
uv run --project pipeline pytest pipeline/tests -q
uv sync --project analysis --locked
uv run --project analysis pytest analysis/tests -q
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

**A fresh clone does not include real-data inputs or frozen results.**
`experiments/`, `notes/`, `analysis/data/` and `analysis/outputs/` are intentionally
ignored. The local `notes/GOALS.md` is the unmodified research compass, not a
clean-clone prerequisite. Read the [data guide](docs/data.md) before running
real-data examples. Raw snapshots and reviewed research inputs are distinct from
disposable tooling caches.
