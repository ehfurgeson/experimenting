# Local experimental research, 12 November 2026

Branch: `experiment/bioherbicide-expansion-2026-11-12`. No pushes.

Source of truth for results and limitations:
[tracked checkpoint](../../analysis/docs/experimental-expansion-2026-11-12.md).
Open [offline walkthrough](../../analysis/outputs/experimental-research-checkpoint-2026-11-12/walkthrough.html).

## What worked

- Expanded-cohort no-fit support checks reproduce all four accepted-policy deficits.
- A deliberately heterogeneous 73-structure source-response pool passes the five-fold computational gate.
- Exact source table transcriptions preserve 304 plant and59 non-target/other observations across seven papers; eight fulltexts cached and16 primary leads screened.
- Publication transfer and alias provenance now have a maintained tested workflow.
- Signed duplicate decisions now survive queue export and affect explicit downstream aquatic sensitivity scenarios.
- Fifteen scientific manifests verified when the summary was built. Maintained code:270 analysis tests pass and Ruff passes.

## What did not work

- Pooling heterogeneous endpoints did not yield a transferable biological model. Raw Morgan logistic F1=0.7273 versus scaffold-majority0.7193; publication F1 falls to0.3000(Li) and0.5538(He).
- Source-specific Ambrosia and intact-foxtail cohorts are too small for five-fold modeling. Three of five ophiobolin machine structures remain missing after two spellings; no ad hoc structures substituted.
- Literal PubChem names produced multiple structures for bisvertinolone/trichodimerol and no hit for stagonolide A. Do not select the first candidate.
- Publisher automated access to several papers returned403/429 or browser challenges. Two Sage sources are web-text-only and could not be visually verified; no numerical adoption from them.
- Dittrichia supplement HTTP200 returned HTML rather than ZIP. The response remains preserved and marked invalid; no SI was ingested.
- No safer compound ranking or validated natural-product binding workflow emerged from these experiments.

## Assumptions and boundaries

The owner authorized provisional AI adoption. This is not independent human/scientific review. The experimental pooled target means source-specific high/low assay response under three different parent policies. It does not redefine accepted activity labels. Threshold0.5 and fixed features/models were chosen before scores, with no random-split rescue. The new source rules are retrospective proposals; they were not preregistered before reading the papers.

`EXPERIMENT_PROTOCOL.json` records the pooling assumption. `source-policies-v1/policies.json` records narrow proposals. New `inactive` labels mean exact bounded assay responses, not universally nonherbicidal chemistry. All zero/bound/range distinctions survive transcription. Cancer cells, algae, bacteria, rat LD50 and aquatic endpoints are separate. Controls/extracts and repeated species/doses are observations rather than independent chemical structures.

Use `pooled-v2-corrected-doi/`: the initial draft had an incorrectly typed Ambrosia DOI and is preserved as superseded in `SUPERSEDED_RUNS.md`. No model was trained from that draft. Correct primary DOI is10.3390/molecules24050835. Original accepted inputs and GOALS.md were not modified.

## Reproduction

Run from the repository root in the locked analysis environment. Local scripts document exact paths:

- `fetch_sources.py`, `fetch_more_pmc.py`, `fetch_additional.py`, `fetch_identities.py`, `fetch_ophiobolins.py`, `fetch_ophiobolin_aliases.py`: acquisition only; use new cache paths before rerunning to preserve bytes.
- `inspect_html.py`: standard-library table/text extraction; no figure digitization.
- `baseline_preflight.py`, `pool.py`, `build_source_policies.py`: explicit inputs/lineage and no-fit checks; fresh directories required.
- `extract_series.py`, `extract_additional_series.py`: offline complete selected-table transcription with row-count/shape/ID assertions and hashes.
- `summarize.py`: verifies15 bundles then creates the compact checkpoint; fresh output required.

Commands for maintained screening, raw-model diagnostics, shuffled-label controls and publication transfer are in the tracked checkpoint. Generated products and this research folder remain ignored. Never stage notes/ or raw research caches.

## Aquatic source-recovery continuation

`toxicity_source_screen.csv` records the initial three natural-overlap searches after the modeling checkpoint. Marking's publisher abstract describes static bioassays and several condition/aged-solution experiments, but does not map all six retained trout records. Kamaya's primary-authored PubMed abstract reports neutralized initial pH7.45+/-0.05 and a benzoic-acid48h EC50 of7.0mmol/L; full primary methods and eight result mappings are still needed. Stroh's bibliographic record plus government workshop/HSDB leads point to exposure losses and carrier distinctions, but these secondary leads have not been promoted to primary study context. No source-context overlay or rat admission was created from these searches. Continue by obtaining original methods/tables or build tested field-level overlay support that preserves raw context and exposes contradictions.
