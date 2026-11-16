# Local preparation and historical experiments

This ignored directory holds original preparation scripts, curated research
inputs and raw caches. Maintained analysis now lives in [analysis/](../analysis/README.md),
using the tracked [pipeline](../pipeline/README.md). Earlier numbered analysis
scripts remain for historical context; use their maintained replacements in the
[architecture map](../docs/architecture.md).

| Local preparation | Role / boundary |
| --- | --- |
| `01_curate_compounds.py` | Builds an initial selection from the HRAC export and embedded natural-product list; reviewed name/CID decisions are additional inputs |
| `02_fetch_pubchem.py` | Live PubChem acquisition through pipeline retrieval; saves validated raw bundles |
| `03_fetch_epa.py` | Live EPA identity, ToxCast, hazard, property and TEST retrieval; needs `COMPTOX_API_KEY` and identity review |
| Descriptor retrieval in `04_traits.py` | Fetches missing computed PubChem descriptors; this network behavior is intentionally absent from the maintained offline rebuild |

See the [data/bootstrap guide](../docs/data.md) for required files, manual decisions,
source provenance and collaborator bundle gaps. Do not rerun preparation over
reviewed selections or modify raw evidence merely to refresh an analysis.
No research inputs or caches are shipped in a fresh clone.

Use the [cached-analysis guide](../analysis/docs/cached-analysis.md) for current
rebuild/presentation commands. Its rebuild reads existing source caches into a
separate product directory without fetching API records or missing descriptors.
Dated scientific results and limitations live in [FINDINGS.md](../analysis/FINDINGS.md);
the duplicate local checkpoint report has been removed.

Keep curated inputs, raw snapshots, reviewed decisions and compatibility products
intact. They are research assets, distinct from disposable tooling caches.
