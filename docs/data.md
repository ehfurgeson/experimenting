# Data, provenance and reproduction

A clone supplies code, lockfiles, policies, synthetic tests, and compact
research inputs. The current catalog rebuild needs the local NICE, NPASS,
and restored plant-v5 files in `data_imports/`. Its public sources have pinned
URLs and checksums. The larger local research archives and generated outputs
live in ignored directories. [Catalog rebuild and data layout](../analysis/docs/joint-catalog-notebook.md)

## Categories and preservation

| Category | Locations / examples | Handling |
| --- | --- | --- |
| Original references | Root Allelopathy text; herbicide CSV exports | Preserve bytes, paths and cited line numbers; [catalog](references.md) |
| Curated inputs and decisions | `experiments/data/compounds.csv`, `compound_classes.csv`, EPA identity crosswalk, independently reviewed labels | Research inputs, not disposable products; retain decision history |
| Raw snapshots | `experiments/data/raw/`, computed-descriptor cache; `analysis/outputs/chembl-2026-10-28/raw/` | Preserve with acquisition metadata, database version and hashes |
| Derived products | `analysis/data/`, structural/stress/ablation exports | Reproduce against exact inputs, code and locks; [bundle inventory](results.md) |
| Human review | Handoff worksheets, policy drafts, evidence logs and annotated packets | Preserve reviewed copies separately from unknown-label templates; check annotations before regeneration |
| Tool state | `.venv`, uv/pytest/Ruff/Python/marimo caches | Separate from scientific caches; no cache deletion is part of this pass |

CSV/Parquet pairs and `traits.parquet` compatibility exports may have different
consumers. Do not delete them as apparent duplicates. Raw ChEMBL evidence is stored
under outputs, so the directory name is not a regeneration guarantee.

## Inputs by workflow

All paths below are relative to the repository root unless identified as relative
to an input bundle. All commands run from the repository root.

| Workflow | Required inputs | Network / credentials |
| --- | --- | --- |
| Offline tests | Tracked code and synthetic fixtures | None after environment installation |
| Cached rebuild | Bundle root: `compounds.csv`, `compound_classes.csv`, validated `raw/pubchem/` bundles and query aliases | None |
| EPA-enriched rebuild | Above plus `epa_identity_crosswalk.parquet` and selected approved identities' `raw/comptox/hazard/` caches | None; a missing approved cache raises |
| Optional trait enrichment | Cached `raw/pubchem_computed/`, ToxCast/property coverage products | None; absent cached descriptors remain missing |
| Presentation | Rebuild products in `analysis/data/` or `AGROTOX_ANALYSIS_DATA` | None |
| Structural screen | Unique `compound_id`, SMILES CSV/Parquet; optional independently reviewed labels/candidates | None; RDKit computes chemical features locally |
| Assay review export | Frozen `raw/chembl/*.json` snapshot bundle | None |
| Live acquisition | Curated queries; EPA identity decisions; selected ChEMBL assay IDs | PubChem/ChEMBL network; CompTox network plus `COMPTOX_API_KEY` |

The maintained [cached guide](../analysis/docs/cached-analysis.md) defines trait
flags, null semantics and output contracts. Coverage zero is not absence of hazard;
missing source assessment is not zero. TEST predictions, model-derived BMD/BMDL,
measured observations, evidence availability and reviewed activity remain distinct.

## Obtain a collaborator bundle

No shared download location or verified backup/versioning arrangement is currently
documented. Obtain an authorized copy from the research maintainer: selected
inputs and class labels, identity decisions, raw snapshots with metadata,
optional descriptor/coverage caches, reviewed labels and the relevant manifests.
Check manifest input hashes against the transferred files before interpretation.
A fresh clone alone cannot reproduce the reported real-data results. An API key
cannot reconstruct manual curation decisions or guarantee historical API responses.
Do not include `.env` or credential values in bundles or reports.

## Local bootstrap: what exists and what remains manual

This is a map of the original local process, not a one-command reproducibility
claim. The local scripts below are ignored and not shipped in a clone.

1. Consult the [source catalog](references.md). Local
   `notes/CURATED_COMPOUNDS.md` records source lines, ambiguities and candidate
   names as of 2026-10-21. `experiments/01_curate_compounds.py` reads the HRAC
   export and a hard-coded natural-product list, writing selection and class CSVs.
   It can overwrite the current selection: preserve reviewed inputs first.
2. Reconcile names/CIDs and curated classes. The source candidate list, current
   selection and resolved analysis cohort have different denominators. Some
   searchable names/CIDs were manually rewritten. Rerunning the original curation
   script alone does not guarantee today's reviewed selection.
3. Local `02_fetch_pubchem.py` uses pipeline retrieval to save query aliases,
   identity properties and toxicity snapshots, with retrieval/failure metadata.
   This is live acquisition. Prefer the maintained
   `pipeline/examples/fetch_snapshots.py` for new API usage; read its `--help`.
4. Local `03_fetch_epa.py` resolves EPA candidates and writes the crosswalk,
   ToxCast, hazard, property and TEST products. It uses `COMPTOX_API_KEY` from
   the environment or local `.env`. Review ambiguous identity candidates rather
   than treating an unapproved match as resolved evidence. Preserve the reviewed
   crosswalk with its source bundle.
5. Local `04_traits.py` acquires missing computed PubChem descriptors under
   `raw/pubchem_computed/` as well as assembling traits. It overlaps with old
   analysis and is not the supported offline rebuild. Transfer cached descriptors
   with the source bundle; there is no separate tracked acquisition CLI for this
   complete historical preparation sequence.
6. Run the maintained offline rebuild into a separate fresh product directory:

   ```bash
   uv run --project analysis python analysis/rebuild.py --source experiments/data --output analysis/rebuild-review
   AGROTOX_ANALYSIS_DATA=analysis/rebuild-review uv run --project analysis marimo run analysis/professor_notebook.py
   ```

   The output must be outside the input source tree. PubChem-only rebuilds use
   a clean output directory. Preserve the resulting manifest alongside products.
7. Acquire ChEMBL assays separately with the maintained
   `pipeline/examples/fetch_chembl_assay.py`, then use the
   [frozen review workflow](../analysis/docs/diagnostics-review.md) and
   [human label guide](../analysis/docs/label_review_guide.md). Acquisition is not
   label adjudication. Save working labels separately from frozen templates.

Preparation utilities need individual review before promotion to tracked code;
no blanket unignore or scientific re-curation is part of this cleanup.

## Paths, manifests and future runs

Historical manifests retain absolute paths. When transferring bundles, map those
paths to the supplied data root and compare hashes; do not rewrite the evidence
to imply that it was created elsewhere. Documentation/code hashes may differ
from a frozen run after maintenance. Verify product/input integrity separately
from whether today's code matches the original recorded version.

For future frozen runs use `analysis/outputs/<workflow>-<YYYY-MM-DD>-<run-id>/`
and a short bundle README recording the question, exact command, input root,
manifest, status and any explicitly superseding run. Keep existing folders stable.
A root-relative manifest format requires a separate compatibility change.

## Dietary comparison pilot

The public `analysis/resources/dietary_candidate_seeds.tsv` is a reproducible
candidate-generation resource, not reviewed research truth. Timestamped PubChem
responses live locally in `analysis/outputs/dietary-pubchem-2026-11-04/`; the frozen
review products live in `analysis/outputs/dietary-review-2026-11-04-final/`.
Transfer both directories and their manifest for the exact 40-identity checkpoint.
A fresh clone can perform a new explicit acquisition but cannot recreate an old
PubChem response from its query alone. See the
[source and review contract](../analysis/docs/compound_sources.md#dietary-comparator-review-pilot--2026-11-04).

## Local experimental preservation — 2026-11-12

Before integration into local main, the research snapshot at
`f597eed0cb60b705f77d8fb807a0386da3649363` was preserved under the ignored
`experiments/backups/pre-main-2026-11-12/` directory. This is a same-disk local
preservation copy; no off-device backup or distribution is claimed.

`research-preservation.tar.gz` contains 677 workspace files and a complete-history
Git bundle, inventory and creation script. The workspace includes every dated
experimental root, including unfinished/failed work, and hash-linked dependencies
from result manifests. The archive is 288,172,502 bytes; its SHA-256 is
`8e9045f46c0e164681793a90eceef6bff56d39bea22101f94b70d46c951dd4d8`.
Every workspace file was read back and hash-verified, including three internal
hard links. A separate bare restoration of the Git bundle passed full `git fsck`
and contains the recorded snapshot commit.

`historical-supplement.tar.gz` preserves the exact earlier weekly-literature
acquisition resource, its manifest, verification/recovery tools and history audit.
Its SHA-256 is
`104b5c9f5edf429e5350fa89b375691b623c68f98130c7db759e86549e4c8eb4`.
Forty-four of 45 historical hash differences resolve to exact archived files or
code in the bundled history. One unresolved script hash belongs to the superseded
non-final `experimental-publication-transfer-2026-11-12/` run. Its results are
preserved, but exact historical code reproducibility is unproven; the canonical
`-final` transfer run has recoverable source. Frozen manifests remain unchanged.

Use the archive directory's `README.md`, `inventory.json`, `verification.json`,
`historical_reference_resolution.json` and `supplement-verification.json` for
scope and recovery details. `verify_archive.py` checks the main archive without
extracting over the checkout. Restore into a new empty directory and explicitly
select the recorded Git commit; the bundled main ref is the earlier baseline.
Historical absolute paths remain intact, so another checkout location requires
an explicit mapping. Archive integrity does not establish scientific validity,
complete historical environment reproducibility, or permission to publish the
contained source papers/private research notes. Data remain outside Git.

## Separate A/B source-first inputs — 2026-11-12

The [A/B workflow](../analysis/docs/modeled-evidence.md) has an explicit public
bulk collector plus a separate credentialed stored-TEST expansion command.
The [dated checkpoint](../analysis/docs/modeled-evidence-2026-11-12.md) identifies
canonical releases, immutable scientific inputs and normalization limits. A clone
contains the software and source URLs, but not the original selection's trait/
identity caches, the resolved dietary feature inventory or the new research
bundles. Acquisition and offline normalization/evaluation are separate operations.
Preserve raw workbook/archive bytes and code/protocol/lock snapshots. Do not share
raw scientific assets or credentials without separate authorization. Existing
archives/manifests are historical evidence and must not be rewritten by new runs.
