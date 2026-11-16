# Local utility inventory

Reviewed by source inspection on 2026-11-02. The Python utilities remain unchanged
because frozen artifacts can record generator/code hashes. They were not executed
or promoted as maintained public workflows. All assume repository-root working
directory and particular local bundles; several execute work at module import.

| Utility | Reads / dependencies | Writes / behavior | Current interpretation |
| --- | --- | --- | --- |
| [audit_chembl_expansion.py](audit_chembl_expansion.py) | `chembl-2026-10-28/raw/chembl/*.json`; analysis structural preparation helpers | Writes `candidates.csv`, `activity_review.csv`, `acquisition_audit.json` inside the original acquisition bundle; no fresh-output guard | Historical scratch acquisition audit. Its CSV writes could overwrite existing products; use maintained `analysis/review_assays.py` with a fresh output for review exports |
| [audit_model_imputation.py](audit_model_imputation.py) | Fixed stress-baseline structural features and prepared traits; analysis/scikit-learn/NumPy/Polars | Creates `imputation-audit-2026-10-29/`, refuses an existing output; reruns diagnostic model comparisons | Historical model diagnostic, not a production model or current acceptance check |
| [build_label_research_handoff.py](build_label_research_handoff.py) | Fixed final review CSVs, raw snapshot hashes and tracked researcher guide | Creates fixed researcher handoff pack, refuses an existing pack; hashes itself/guide/sources; asserts original 154-compound/157-observation unknown-label starting state | Research-specific generator. Do not rerun it to replace an annotated working pack; its original source hash is part of handoff provenance |
| [verify_structural_ablations.py](verify_structural_ablations.py) | Fixed baseline and fixed/nested final manifests, CSVs and their absolute-path dependencies; NumPy | Assertions/checks and printed verification; no explicit scientific-output writes found | Historical read-only verification script, with fixed cohort counts and original environment/path assumptions; a mismatch is not permission to rewrite a frozen manifest |

Bundle paths above are relative to `analysis/outputs/`. Historical script execution
can require the original source/environment, and current documentation may differ
from recorded hashes. Inspect inputs and execution side effects before any deliberate
rerun; this inventory is not a request to execute them.

Maintained routes: [cached rebuild](../analysis/docs/cached-analysis.md),
[structural screen](../analysis/docs/structural-screening.md),
[review/diagnostics](../analysis/docs/diagnostics-review.md) and
[researcher label guide](../analysis/docs/label_review_guide.md).
Future promotion should supply explicit input/output arguments and preserve
historical data/code versions; it is a separate behavior change.
