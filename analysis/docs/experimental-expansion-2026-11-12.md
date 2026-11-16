# Experimental activity expansion — 2026-11-12

This local-only experiment deliberately relaxed scientific adoption requirements,
with the owner's authorization. It made a model computationally fit-able but did
**not** establish transferable activity or safer natural herbicides. Original
human-reviewed labels, sources and frozen results remain unchanged. New source
mappings and decisions are explicitly AI experimental proposals.

## What was tested

The four accepted activity policies were independently checked with
[expanded-cohort preflight](structural-screening.md#expanded-activity-cohort-preflight).
Counts reproduce the handoff: K1998 has 5 active / 0 low-response compounds and
3 / 0 class-bearing scaffolds; Okamoto 4 / 0 and 1 / 0; Li 11 / 10 and 3 / 2;
He 29 / 21 and 2 / 2. No accepted individual policy supports five-fold fitting.

A deliberately heterogeneous sensitivity policy,
`EXPERIMENT-HETEROGENEOUS-REPORTED-EXTREMES-v1`, combines the **21 Li and 50 He**
known activity rows with **two provisional Ambrosia rows**. The latter map
confertin and neoambrosin to unique PubChem name hits; their primary assay has
lettuce ordinal responses 4 and 0 at 1 mM after seven days. The proposed source
rule uses grades 4/5 for high response and 0/1 for low response; other grades stay
unknown. Isolation is reported in the same [primary paper](https://doi.org/10.3390/molecules24050835).
The source-to-database stereochemical mapping, vehicle details and replication
remain provisional. No unknown was converted into a negative.

The pooled target is **source-specific high versus low response**, with parent
policies retained in `pooled_lineage.csv`. It is not a common efficacy estimand:
Li uses 150 g a.i./ha visual response, He 1,500 g a.i./ha fresh-weight response,
and Ambrosia a lettuce solution/well assay. Combining these endpoints was an
intentional experimental assumption, not a revision of the accepted policies.

The pool has **73 unique eligible structures**, 41 high-response and 32 low-response
labels, with six and five class-bearing scaffold groups. Its actual five-fold
partitions contain both classes. Representation, seed, threshold 0.5, fixed
regularization, fold-local preprocessing and scaffold grouping were preserved.
The experiment protocol was written before model scores were computed; source
rules were proposed retrospectively after inspecting the literature.

## Results and what failed

| Fixed profile | Scaffold F1 | Precision | Recall | Balanced accuracy | AUROC |
|---|---:|---:|---:|---:|---:|
| Formula PCA logistic | 0.5714 | 0.5581 | 0.5854 | 0.4958 | 0.4897 |
| Standardized raw-formula logistic | 0.5128 | 0.5405 | 0.4878 | 0.4783 | 0.5111 |
| Raw Morgan logistic | 0.7273 | 0.6809 | 0.7805 | 0.6559 | 0.6791 |
| Raw Morgan forest | 0.6804 | 0.5893 | 0.8049 | 0.5431 | 0.5831 |

The training-majority scaffold baseline has **F1 0.7193**, balanced accuracy 0.5.
Thus F1 0.7273 alone is weak evidence of improvement. All eight fixed profiles,
confusion counts and held-out predictions are retained; no favorable profile was
selected for candidate scoring.

[Publication transfer](diagnostics-review.md#publication-transfer) gave a much
less favorable assessment:

| Held-out publication | Test n | Raw Morgan logistic F1 | Balanced accuracy | AUROC | Majority F1 |
|---|---:|---:|---:|---:|---:|
| Li 2006 | 21 | 0.3000 | 0.3364 | 0.3818 | 0.6875 |
| He 2011 | 50 | 0.5538 | 0.3818 | 0.3547 | 0.7342 |
| Ambrosia 2019 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.6667 |

The two-compound test is descriptive and exceptionally small. Publication-only
and publication-plus-scaffold-purge splits coincide in this cohort: publications
share no scaffold groups. A forest predicts every He test compound high-response,
reproducing majority F1 0.7342 while balanced accuracy remains 0.5. That illustrates
why a seemingly useful F1 can coexist with failed transfer. These results do not
support new-compound screening, a universal activity label or a safety claim.

Twenty fixed-seed label shuffles were run for each PCA representation. Formula
PCA actual F1 0.5714 lies inside the shuffled range 0.4348–0.7160. Morgan PCA
actual F1 0.6897 exceeds the 20 observed shuffled values (range 0.4167–0.6329),
but this small exploratory control is not a formal multiplicity-adjusted
significance claim and does not repair publication-transfer failure. These are
PCA controls, distinct from the raw-Morgan profiles above.

The full-cohort forest's tree-specific **OOB F1 is 0.7436**. Each bit has ten OOB
permutation repeats; repeat SD is descriptive, not a p-value, and OOB does not
hold out structural families. The largest reported mean F1 drop is bit 294,
0.0403 ± 0.0115 across repeats. Hashed fingerprint bits are not unique chemical
motifs. Raw-formula coefficient means include Cl fraction +0.5852 (fold SD
0.1644) and O count −0.4440 (SD 0.3946), on training-fold standard-deviation
scales with positive meaning experimental high response. Correlated composition
features, small chemical series and failed transfer prevent causal interpretation.

## New evidence and unresolved leads

The local literature screen has **16 primary-study leads**, eight cached full
texts and complete selected-table transcriptions from seven studies:

| Primary source | Plant observations | Other endpoint observations | Important limit |
|---|---:|---:|---|
| [Ambrosia 2019](https://doi.org/10.3390/molecules24050835) | 12 | 0 | Two compounds; doses/species remain separate |
| [Nonenolides 2021](https://doi.org/10.3390/jof7100829) | 39 | 39 | Includes controls; related lactones; `n/a` is not zero |
| [Sorbicillinoids 2019](https://doi.org/10.3389/fchem.2019.00435) | 80 | 0 | Cited assay duration/vehicle unresolved; ambiguous database hits |
| [Cleomside 2020](https://doi.org/10.3390/molecules25194461) | 40 | 0 | Includes extract; germination index; six-/seven-day and vehicle gaps |
| [Rosemary 2018](https://doi.org/10.3390/toxins10120498) | 42 | 0 | Twenty-one species represent one tested compound |
| [Marine fungi 2018](https://doi.org/10.1039/c8ra08047j) | 51 | 0 | Three qualitative null statements retain their wording; no invented numbers |
| [Ophiobolins 2021](https://doi.org/10.47371/mycosci.2020.11.002) | 40 | 20 | Separate intact/punctured leaves; raw intervals/bounds; delayed-lesion text conflict |

These **304 plant and 59 other endpoint observations** include controls, extracts,
multiple doses, species and endpoints. They are not 363 independent compounds,
new training labels, rat LD50 measurements or comparable safety observations.
Each row retains raw response, context, source locator/hash, extraction status and
unresolved reasons. No new observation received independent human review.

A separate proposed 48-hour, intact-foxtail policy at 1 mg/mL gives one high-response,
three exact-zero low-response and one unknown ophiobolin. `<1 mm` remains unknown,
not zero. Only two of five database structures were recovered by name; one has
known low response and the other unknown response. The three missing identities
are explicitly excluded from computational support; no standalone activity model
was fitted. Ambrosia's separate two-compound policy also remains unsupported.

Other screened leads remain useful without becoming labels. Pileostegia isolated
31 compounds and tested a 12-compound subset; the USDA summary renumbers that
subset. This is not evidence that the other 25 isolated compounds were tested
negatives. Semenovia's furanocoumarins include low-response results, but local PDF
retrieval returned 403 and visual verification was unavailable. Dittrichia has
figure/method dose differences and a supplement URL returning HTTP 200 with an
HTML download page rather than a ZIP; that response was rejected as data.
Additional perlatolic-acid, diarylamine, artemisinin, lignan and pine-metabolite
leads retain access/method/identity limits in `literature_screen.csv`.

## Reproduction and local files

Work root: `experiments/bioherbicide-expansion-2026-11-12/` (ignored). It contains
acquisition scripts/logs, source hashes, `EXPERIMENT_PROTOCOL.json`, baseline
preflights, `source-policies-v1/`, `transcription-v1/`,
`transcription-additional-v1/` and the 16-row literature screen. Use
`pooled-v2-corrected-doi/` for pooled inputs: the first draft mistyped the Ambrosia
DOI and is retained as superseded, without model fitting from that version.

Model/result bundles under `analysis/outputs/` are
`experimental-heterogeneous-activity-2026-11-12/`,
`experimental-heterogeneous-diagnostics-2026-11-12/`,
`experimental-heterogeneous-controls-2026-11-12/`,
`experimental-publication-transfer-2026-11-12-final/` and
`experimental-research-checkpoint-2026-11-12/`. The last provides `walkthrough.html`,
figures, compact metrics/weights and a verified manifest. Run the following commands from the repository root:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/screen.py --compounds YOUR_WORK/pooled_compounds.csv \
  --labels YOUR_WORK/pooled_labels.csv --output analysis/outputs/NEW_SCREEN
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/professor_followup.py --features YOUR_SCREEN/structural_features.parquet \
  --target activity_target --permutation-repeats 10 --oob-repeats 10 \
  --output analysis/outputs/NEW_DIAGNOSTICS
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/stress.py --features YOUR_SCREEN/structural_features.parquet \
  --target activity_target --permutations 20 --output analysis/outputs/NEW_CONTROLS
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked --offline python analysis/publication_transfer.py --features YOUR_SCREEN/structural_features.parquet \
  --lineage YOUR_WORK/pooled_lineage.csv --output analysis/outputs/NEW_TRANSFER
```

Replace all placeholders and use fresh output directories. The software commands
remain offline; source acquisition is separate and may encounter access failures.
The local experiment scripts preserve the concrete input paths and extraction
assertions. Fifteen input/result manifests were verified when the checkpoint was
built. Both summary figures were rendered to PNG and inspected.

The toxicity integration experiment additionally fixed lost duplicate-review
states between reconciliation export and downstream aquatic sensitivities, with
regression checks. A fresh real-data run in
`experimental-ecotox-decisions-2026-11-12/` preserves the 28 trout and 13 Daphnia
admissions, 16 rat review cases and zero new duplicate decisions. Frozen source
exports and rat medians/cutoffs are unchanged.

Verification: **270 analysis tests passed**, analysis Ruff passed, and diff
whitespace checks passed. Pipeline code did not change and its suite was not
rerun. This is software verification, not independent biological validation.

The next useful experiments require compatible external assay evidence and exact
new structures, followed by publication-held-out checks. Relaxing scientific
adoption made it possible to test this idea; it did not produce a transferable
model. Binding characterization and supported natural-group toxicity rankings
remain open research objectives.

## Compatible flavonoid-series expansion

A separate [primary study](https://doi.org/10.3390/ijms13055406) provides all
27 named compounds across two species, three doses (1/10/100 µM), germination
counts and radicle lengths at 120 hours: **324 observations**, not independent
compounds. Tables 1/2 and methods 3.2/3.3/3.5 supply raw means, SDs, controls,
significance symbols and three Petri dishes of ten seeds per determination.
Catechol is among the tested compounds despite not being a flavonoid.

The transcription preserves every row, including nonsignificant results.
Inhibition is derived as `100 × (1 − treated mean / control mean)`; negative
values retain stimulation. These ratios of rounded means have no reconstructed
SE, CI or IC50. Source SDs are not SEs, and seeds are not treated as independent
replicates. Water or 0.5% acetone vehicles are reported without compound-level
assignment; the authors report no difference between vehicle and water controls.

Twelve separate species × endpoint × dose policies use analyst-defined
**≥50% inhibition** for high response, **≤20%** for low inhibition, and unknown
for intermediate responses. These are retrospective experimental rules, without
score-based threshold tuning. Stimulation counts as low inhibition for this
narrow target; it does not establish biological inactivity. No assays are pooled.
All 27 PubChem name queries return one record, with RDKit/full-InChIKey agreement.
Source stereochemistry and sample mappings remain provisional AI decisions;
all natural-origin labels remain unknown.

At **100 µM**, each species independently has **2 high / 18 low / 7 intermediate**
root-growth responses. The 20 labeled structures span two high-bearing and nine
low-bearing Murcko groups. All four representations fail five-fold preflight;
three more high compounds and three more high-bearing scaffold groups are needed
for even the count minimum. Other policies have at most one high response.
This adds useful low-response chemistry without establishing a fitted classifier.

Six retrospectively selected parent/O-methylated pairs give 36 descriptive
comparisons across species/doses. Constitutional O-demethylation checks pass while
explicitly ignoring stereochemistry. Chrysin and pinocembrin dimethyl ethers show
stronger mean inhibition than their parents in both species at 100 µM; the
3-hydroxyflavone pair shows a small opposite difference in radish. The result is
not a universal methylation effect or causal mechanism, and replicate-level data
are unavailable for uncertainty of the differences. No efficacy or safety
prediction follows.

Two larger-library leads were recovered but not labeled: the
[pollen screen](https://doi.org/10.1186/s12870-016-0875-4) reports 19 inhibitors
and three stimulators as selected hits from 1,040 compounds, with secondary-assay
time wording requiring reconciliation. Its omitted library members are not
secondary-assay negatives. The [Prestwick study](https://doi.org/10.1016/j.isci.2025.112375)
reports 1,519 compounds in a mutant-specific screen, but full datasets/code are
available on request. An [18-metabolite Cuscuta study](https://doi.org/10.3390/agriculture12101746)
remains an access-limited lead (403/429), without ingested labels.

The ignored local root `experiments/compatible-assays-2026-11-12/` contains cached
primary HTML, extraction and identity logs, `transcription-v1/`, verified
`analysis-v2/`, `verification.json` and `SUMMARY.md`. Acquisition is separate from
offline analysis. Run `verify.py` there through the locked analysis environment
to check 324 source cells/ratios, 12 policies, 27 structures, 36 comparisons,
six constitutional pairs and 136 hashes. The SVG/PNG figure was rendered and
inspected. The incomplete `analysis-v1/` is retained with its exact source after
a plotting failure and is superseded. Production code and frozen evidence were
unchanged; no analysis/pipeline suite was rerun for this evidence-only addition.

## Fixed transfer to the recovered root-growth series

After the separate evidence checkpoint, an explicit local protocol selected the
radish 100 µM/120 h root-growth policy **before new model scores**. It preserves
the original 73-compound pool and fixed raw-formula logistic, Morgan logistic and
Morgan forest profiles, with threshold 0.5. Twenty new known-response compounds
form the primary publication-held-out test (2 high, 18 low); seven intermediate
responses remain unknown. No structure overlaps canonically with training.
The common experimental policy is explicitly extended to
`EXPERIMENT-HETEROGENEOUS-REPORTED-EXTREMES-plus-FLAV2012-v2`; its constituent
assays still do not measure a common efficacy endpoint.

| Fixed profile, original 73 training compounds | F1 | Precision | Recall | Balanced accuracy | AUROC | TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---|
| Raw-formula logistic | 0 | 0 | 0 | 0.4444 | 0.5000 | 16 / 2 / 2 / 0 |
| Morgan logistic | 0 | 0 | 0 | 0.2778 | 0.3333 | 10 / 8 / 2 / 0 |
| Morgan forest | 0 | 0 | 0 | 0.2500 | 0.2778 | 9 / 9 / 2 / 0 |

All three miss both high responses. The training-majority baseline predicts all
high (F1 0.1818, balanced accuracy 0.5). Maximum radius-2, 2,048-bit Morgan Tanimoto
to training ranges 0.1111–0.2388 for these 20 compounds; this describes chemical
distance, without a validated applicability cutoff or calibrated uncertainty.

Scaffold purging removes **21 He2011 training compounds**, whose benzene Murcko
group is shared with test catechol. This broad group is not a near-duplicate
criterion. Training falls to 52 compounds, 27 high/25 low. Formula still misses
both positives; Morgan logistic instead predicts 15/20 high with 13 false
positives (F1 0.2353, precision 0.1333, recall 1.0, balanced accuracy 0.6389,
AUROC 0.4167). Forest predicts 18/20 high with 16 false positives (F1 0.2,
precision 0.1111, recall 1.0, balanced accuracy 0.5556, AUROC 0.3333). These
sensitivities expose instability; neither is selected as an improved model.

Secondary four-publication diagnostics retain all held-out sources. Adding the
new low-response panel does not repair transfer: publication-only He2011 F1 is
0 for formula/forest and 0.0645 for Morgan logistic; Li2006 F1 is 0, 0.3333 and 0,
respectively. The expanded labeled pool has 43 high/50 low compounds with
source-dependent class balance. Assay incompatibility, chemistry and class
composition remain entangled; these results cannot isolate a cause of failure
or validate a general herbicidal endpoint. No threshold changes, model selection,
new candidate ranking or safety inference followed the test.

Local `external_protocol.json`, `external_transfer.py` and `external-inputs-v1/`
under `experiments/compatible-assays-2026-11-12/` retain the concrete inputs,
parent policies and nearest-training comparisons. The new output is
`analysis/outputs/experimental-flavonoid-transfer-2026-11-12/`, with predictions,
membership, metrics and manifest. `verify_external.py` independently recomputes
24 metric/confusion reports from 558 predictions, checks all 73 old rows unchanged
apart from policy name, split membership/scaffold disjointness and 94 hashes;
`external_verification.json` records success. Source-specific no-fit preflights
and earlier pooled results remain frozen. No production code changed or suite
was rerun for this experiment.
