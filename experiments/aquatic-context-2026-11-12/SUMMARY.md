# Aquatic context overlay experiment — 12 November 2026

The source-linked overlay reader is `analysis/context_overlay.py`; its maintained
contract is [human review](../../analysis/docs/human-review.md#source-linked-aquatic-context-overlays).

## Actual run

- Frozen input: `analysis/outputs/ecotox-approved-comparison-2026-11-11-verified/`.
- `sources/kamaya2005_pubmed.xml` is the primary-authored abstract for PMID15722097,
  retrieved through NCBI EFetch and checked for matching PMID/abstract content.
  It is not the full paper. `sources/sources.json` records URL/kind/hash/reference.
- `provisional_ph_decisions.json` associates initial pH7.45 with eight reference80404
  rows, explicitly as a provisional study-to-row inference. The abstract's
  +/-0.05 is retained in the rationale; it is not reinterpreted as a confidence
  interval. Exposure duration, chemical analysis and control responses are not
  inferred from that abstract.
- `analysis/outputs/aquatic-context-reviewed-2026-11-12/`:0 applied fields.
- `analysis/outputs/aquatic-context-experimental-2026-11-12/`:8 initial-pH fields
  applied in a separate sensitivity. These proposals have AI experimental review,
  not independent human or full-methods verification.

Both runs preserve every original field of all41 admitted observations. Core
counts remain28 trout and13 Daphnia; the reported-context subset remains0 trout
and1 Daphnia. All concentrations, bounds, identities, observations and original
context fields are unchanged. No rat record is admitted; no duplicate decision
is created or applied by this standalone experiment. pH is additional metadata,
not a new stratification variable or evidence of comparable exposure.

`verify_run.py` checks all41 original row fields against both output tables,
byte equality of original exports, exactly8 experimental pH enrichments, and the
new/frozen manifests. `verification.json` records the executed assertions.

## What worked and failed

- NCBI's ordinary PubMed HTML request returned HTTP200 but failed the actual
  article/abstract content assertions. No source registry entry was created from
  that response. EFetch XML succeeded on the next legitimate retrieval route.
- Field-level provenance, original-value checks, review modes and explicit
  unresolved/contradiction states now work without editing frozen native data.
- Synthetic regressions show that full-text-supported exposure/control recovery
  can change the documentation sensitivity, while source values/qualifiers stay
  unchanged. They also reject partial/inconsistent decisions across sibling test
  slots and refuse silent nonmissing contradictions.
- This real abstract-based experiment does not resolve continuous exposure
  durations, treatment-specific protocols or missing controls. More metadata did
  not increase the reported-context subset. Original methods and result cells
  remain the scientific dependency.

## Reproduction and provenance

`build.py` contains concrete input paths and both mode invocations; use fresh
proposal/output paths when rerunning. `fetch_abstract.py` documents the failed
HTML-content route; `fetch_abstract_xml.py` documents the successful XML route.
Both source and result snapshots remain ignored and immutable.

The run preceded two validation-only improvements (strict reference-number shape
and rejection of nonfinite unresolved proposals). Its exact earlier reader source
is retained as `context_overlay_run_source.py`; its hash matches both run
manifests. The maintained reader has287 passing analysis tests and clean Ruff.
No source, reviewed label, GOALS.md, rat cutoff or prior manifest was overwritten.
