# Analysis checkpoints

The current catalog analysis joins plant and toxicity scores for **768,439**
unique structures. The measured-oral comparison has **166** high-LD50 and
high-plant-score overlaps after treating the butyl stearate limit as a lower
bound. The separate model-score comparison has **11,557** overlaps. Explore
the experimental evidence, held-out model metrics, and out-of-bag importance
for all 20 screening forests in the [joint catalog notebook](docs/joint-catalog-notebook.md).
The [joint screen report](docs/joint-catalog-screen.md) records thresholds and
why high oral LD50 alone leaves other hazards unresolved.

## Earlier seven-endpoint and accepted-data checkpoints

The [plant evidence experiments](docs/plant-evidence-experiments-2026-11-17.md)
recover complete primary series, evaluate context and assay-specific models,
reconstruct dose responses and stress-test experimental selection. Read their
feasibility decisions and evidence limitations before using the new working tables.

For the earlier LOTUS overlay, protected model pilots, selection
screens and analogue queue, read the
[17 November research follow-up](docs/research-followup-2026-11-17.md).

Current accepted-sprint bundles are `plant-v5`, `plant-models-v5`,
`integrated-screen-v5`, `toxicity-v2`, `toxicity-models-v2`, `uncertainty-v2`,
and `results-v5`. The 120-structure `results-v2` run is retracted. A
percent-of-control value above 100 has inhibition = 100 − value (120% of control
is −20, low). At or below 100, stimulation (−value, low) is used only when the
comment documents an increase or stimulation. A comment that only names percent
of control keeps inhibition = 100 − response, even if direction is INC. The
toxicity forests were refit on the log10-median targets. Read the
[dated checkpoint](docs/accepted-sprint-2026-11-17.md) and the
[candidate audit](docs/candidate-audit-2026-11-17.md).

For the user-accepted experimental continuation, including expanded toxicity,
plant models and three-axis candidates, see
[accepted-data experiments](docs/accepted-sprint-2026-11-17.md).

For the latest natural-catalog and new-source yield audit, see the
[data-first sprint checkpoint](docs/data-sprint-2026-11-17.md).

Navigation updated 2026-11-02; the dated checkpoint results below are preserved.
For the separate local-only permissive activity experiment, see
[2026-11-12](#permissive-activity-expansion-and-publication-transfer--2026-11-12).
For the latest structural feature/regularization comparison, start at
[2026-10-29](#feature-combinations-and-nested-regularization--2026-10-29).
For toxicity evidence availability and presentation, start at
[the seven-endpoint checkpoint](#what-the-analysis-now-includes).
For activity/origin adjudication, use the [label review guide](docs/label_review_guide.md);
selection-model results do not establish activity. The [result inventory](../docs/results.md)
identifies local bundles and their status. Test counts below describe their original runs.

Cached analysis refreshed on **2026-10-22**, using the pipeline at `c182291`
plus the experiment integration. This replaces the earlier acute-only experiment
snapshot; old endpoint coverage and classifier accuracy figures are superseded.

## What the analysis now includes

The 176 resolved compounds comprise 60 herbicides and 116 natural products.
The trait table has 78 columns, including 24 endpoint availability flags: eight
comparison policies for each of PubChem, EPA, and their union. LC50 has both a
broad fish policy and a trout-specific policy, so these cover seven endpoint
types. The underlying selection file contains 178 input rows before query
canonicalization. The current EPA crosswalk approves 136 compound identities,
leaves 24 for review, and has 16 unresolved.

| Policy | PubChem herbicides / natural products | EPA herbicides / natural products |
|---|---:|---:|
| Mammal oral LD50 | 39 / 30 | 36 / 14 |
| Fish LC50 | 4 / 4 | 0 / 0 |
| Trout 96-hour LC50 | 4 / 0 | 0 / 0 |
| Daphnia 48-hour EC50 | 0 / 0 | 0 / 0 |
| Mammal oral daily-dose NOAEL | 0 / 0 | 34 / 16 |
| Mammal oral daily-dose LOAEL | 0 / 0 | 32 / 8 |
| Mammal oral daily-dose BMD | 0 / 0 | 0 / 0 |
| Mammal oral daily-dose BMDL | 0 / 0 | 2 / 0 |

Coverage reports use the full selection as the denominator for both sources:
60 herbicides and 116 natural products. EPA trait flags distinguish the 136
approved/assessed identities from unavailable identities with nulls. PubChem
chronic zeros reflect acute-only prose extraction, not proof that its records
contain no chronic studies.

## Evidence and potency limits

Current EPA normalization retains 5,814 source observations: 1,438 complete,
522 partial, and 3,854 failed under the supported endpoint/unit rules. Rejected
records and their reasons remain available for review. Experimental admission
follows the source's explicit mark. BMD/BMDL are model-derived points of departure
from that evidence; stored TEST predictions remain separate and unused by these
endpoint distributions/classifiers. PubChem annotations are not independently
verified as uniformly experimental.

All 92 chronic compound-summary rows have null potency medians because the
example policies count availability across heterogeneous study contexts. No
seven-endpoint potency ranking or safety score is claimed. Study-level doses,
units, qualifiers, and context remain in `data/epa_analysis/measurements.parquet`.

## Distributions and models

The refreshed products contain 118 distribution rows (59 traits × two groups),
59 group-comparison rows, and 27 classifier target rows. Trait categories separate
14 molecular properties, 24 endpoint availability flags, 20 study-coverage counts,
and one assay-activity fraction. Missing values remain missing.

Twelve classifier targets have enough examples in each class for five-fold
validation. Fifteen have `insufficient_class_support`, null accuracy, and no
fitted weights. BMD has no positive examples; BMDL has only two. Classifiers
predict group membership or evidence availability using molecular descriptors,
not toxicity doses. Held-out compounds use training-fold imputation and scaling.
High accuracy on an imbalanced target must be read beside its majority baseline.

These are exploratory descriptions of a purposive selection. Multiple unadjusted
comparisons, differing assay panels, and unresolved identities limit inference;
the results do not establish safety, causation, or population-wide differences.

## Reproduction and validation

Follow the cached commands in [README.md](README.md). EPA evidence, audits,
reviews, and summaries under `data/epa_analysis/` have dependency sidecars.
Other regenerated CSV/Parquet products remain local and ignored. The old
`epa_hazard_comparison.*` products are superseded and are not consumed.

The full pipeline suite passes **1,000 tests**, including 11 focused experiment
integration checks. Ruff passes for the pipeline and retained analysis scripts.
Synthetic tests exercise all seven endpoints, sparse targets, source availability,
and training-only preprocessing without live API calls.

## Professor notebook

`professor_notebook.py` presents the seven endpoint availability distributions
first, then molecular distributions, study coverage, and classifier baselines.
The cached selection contains 176 compounds (60 herbicides, 116 natural compounds).
Median molecular weight is 275.7 versus 174.7 g/mol, and median XLogP is 2.7
versus 1.7. These are descriptors of the selection, not safety conclusions.
Group-classification accuracy is 76.7% versus a 65.9% majority baseline;
NOAEL availability is only slightly above its baseline, while LOAEL is below.
The point of the classifier comparison is whether structure adds useful
information beyond class balance, not whether raw accuracy looks high.

The analysis environment, live marimo notebook, and static HTML export have
been executed. Rendered endpoint, molecular-trait, and classifier charts were
visually checked; the live source selector was checked in the browser.

## Structural classification checkpoint — 2026-10-27

The new `screen.py` command was run against the unchanged cached
`analysis/data/compound_traits.parquet` (176 compounds, 60 selected herbicides
and 116 selected natural products). Local, ignored products are in
`analysis/outputs/structure-2026-10-27-verified/`; `manifest.json` records exact source,
code, environment and output hashes. The existing notebook results above still
refer to its older descriptor model and random compound folds.

RDKit accepts 174 single-component structures. Glufosinate-ammonium and MSMA
are retained as multicomponent review rows. Paraquat, diquat and difenzoquat
have charged formulas outside the conservative formula parser, leaving 171
formula-model rows (55 selected herbicides and 116 natural products). Descriptor
and Morgan models use 174 rows (58 and 116). No supplied neutral formula or
InChIKey conflicts were found. All features are structural; no toxicity values
or evidence-availability features are required.

Five-fold scaffold-held-out results for **selection membership only**:

| Representation | n | Accuracy | Balanced accuracy | ROC-AUC | Fold-majority accuracy | Maximum training-fold PCA components |
|---|---:|---:|---:|---:|---:|---:|
| Formula composition | 171 | 93.6% | 91.9% | 0.952 | 67.8% | 9 |
| RDKit descriptors, rules and SA | 174 | 69.5% | 72.8% | 0.789 | 66.7% | 7 |
| Morgan fingerprint | 174 | 86.8% | 80.2% | 0.963 | 66.7% | 106 |
| Formula + descriptors + Morgan | 174 | 90.2% | 85.3% | 0.975 | 66.7% | 105 |

All fold-majority balanced accuracies are 50%. PCA retains 95% training variance;
its fingerprint representations still retain many components relative to this
small selection. It is a practical comparison, not proof that the dimensionality
problem is solved. Regularization, external validation and additional labeled
chemistry remain necessary. Representations have different eligible rows, so
these results are not a controlled model-ranking benchmark.

Formula is informative about **this curated selection**. Among valid formula
rows, median distinct element count is 5 for selected herbicides and 3 for
natural products. Chlorine is present in 26/55 versus 1/116; nitrogen in 49/55
versus 18/116. These contrasts suggest curation/composition bias as one plausible
source of discrimination; they do not show that elements cause herbicidal
activity or establish natural origin. Isomers can share every formula feature.

The crucial missing input is a reviewed label set: there are **zero separately
reviewed activity or natural-origin training labels** in this run. All eight
activity/origin representation reports therefore have `insufficient_class_support`
and null performance. The system cannot yet establish a validated classifier
for herbicidal natural compounds versus tested inactive natural compounds.
Selection categories must not be substituted for those labels.

Implemented: formula composition, structural descriptors, Lipinski/Tice-inspired
proxy violations, Ertl synthetic accessibility, Morgan features, fold-local PCA,
scaffold validation, independent reviewed-label validation, candidate scoring
with support guards, similarity context and reproducible offline exports.
Synthetic tests cover the reviewed-activity scoring path; real candidate activity
prediction is deferred until labels support it. No broad natural-product library
was imported or falsely treated as inactive.
See [compound expansion evidence](docs/compound_sources.md) for checked sources
and the specific acquisition/curation gaps.

Verification at this checkpoint: 68 structural-analysis tests and 1,006 existing
pipeline tests pass; Ruff passes for both source trees. Focused tests were run
red before implementation, including the uncommon-element identity regression.
The source/lock environment was checked with locked offline synchronization.

## Structural stress and assay acquisition — 2026-10-28

The [validation checkpoint](docs/structural_validation_check.md) records 96 new
diagnostic reports: a shared 171-compound cohort, three-/five-/ten-fold scaffold
validation, largest-scaffold removal, and 20 shuffled-label controls for each
representation. Five-fold selection balanced accuracy is 91.9% formula, 72.4%
descriptors, 76.4% Morgan and 85.5% combined. Shuffled-label means are 49.2–50.2%.
Removing the 49-compound benzene scaffold reduces combined accuracy to 77.0%.
These results describe selection membership; they do not validate activity.

The pipeline also retrieved **157 activity records from 14 ChEMBL assays and
publications**, yielding 154 unique structures across 28 scaffolds, including
149 structures outside the existing selection. Source values, qualifiers,
publication context and structures remain in ignored raw snapshots and review
exports. All structures parse successfully; three records lack numeric outcomes,
45 have inequality qualifiers, and assay doses/timings are heterogeneous.

A single-assay pilot predicting its reported >80% versus <50% growth-inhibition
bands lacks scaffold support for five or three folds. A separate exploratory
two-fold run reaches only 37.1–50.0% balanced accuracy across models. This exposes
the data/model limitation rather than supplying an accepted activity classifier.
The production candidate run retains all 616 candidate/representation rows with
blocked activity-model status and null probabilities. Reviewed activity and
natural-origin labels remain absent; no general active/inactive labels were
manufactured from these raw assays.

Verification: 87 analysis tests, 1,043 pipeline tests, both Ruff checks, live
four-page retrieval equivalence and product manifest hashes pass. The full
checkpoint lists source assays, local products, commands, results and follow-up.

## Feature combinations and nested regularization — 2026-10-29

The [feature-combination checkpoint](docs/feature_combination_check.md) compares
nine predeclared profiles on the same 171 complete compounds and original five
scaffold folds, without imputation. Formula + descriptors reaches 92.82% balanced
accuracy at C=1 versus 91.91% for formula alone; this is a small net gain of one
selected-herbicide detection. Adding fingerprints at C=1 lowers balanced accuracy,
and preserving formula outside PCA alone does not recover the difference.

Nested selection over C=0.01, 0.1, 1, 10, 100, using three inner scaffold folds,
raises original combined performance from 85.45% to 91.48%. Formula-only reaches
92.77%, while combined with formula outside PCA reaches 92.39%. All fingerprint
profiles select C=100 (weaker regularization) in every outer fold. Combined
ROC-AUC was already 0.9773 at C=1 and becomes 0.9793; its fixed-cutoff confusion
counts change from 16 missed herbicides/zero false positives to seven misses/
five false positives. Regularization and operating-point behavior explain a
substantial part of the earlier gap; a simple PCA-information-loss explanation
is not sufficient. The grid-boundary selection is not proof of an optimal C.

All 18 comparisons preserve the same cohort/folds and contain complete held-out
predictions; all 675 inner candidate scores and selected C values are saved.
Verification: 26 focused tests, 143 analysis tests, 1,043 pipeline tests, both Ruff
checks and all product hashes pass. These remain selection-membership experiments;
no production default or scientific label was changed, and external/activity
validation remains outstanding.

## Halogen attribution and raw fingerprint classifiers — 2026-11-04

`professor_followup.py` compares eight fixed profiles on the existing **171 unique
compounds (55 selected herbicides, 116 selected natural products)** with identical
five scaffold folds, seed 20261027, no tuning, and a 0.5 decision cutoff. Local
bundle: `analysis/outputs/professor-followup-2026-11-04-final/`, with exact hashes,
held-out predictions, coefficients and permutation exports. These results describe
the selected source groups; natural products have not been relabeled non-toxic.

| Profile | ROC-AUC | Balanced accuracy |
| --- | ---: | ---: |
| Original formula PCA logistic | 0.9516 | 91.91% |
| Raw standardized formula logistic | 0.9513 | 92.77% |
| Halogen counts/fractions only | 0.8170 | 82.30% |
| Halogen presence only | 0.8167 | 83.21% |
| Formula, direct halogen columns dropped | 0.9462 | 85.78% |
| Composition recalculated without halogens | 0.9130 | 82.15% |
| Raw Morgan logistic | 0.9467 | 88.66% |
| Raw Morgan random forest | 0.9487 | 88.66% |

Halogens occur in **37/55** selected herbicides versus **1/116** natural products.
This supports the professor's proposed source of separation, but does not explain
all of it: the stricter halogen-removed representation still separates the groups.
The raw formula comparator's largest mean absolute standardized coefficients are
N count (positive 1.293), Cl count (positive 0.938), element count (positive 0.883),
C count (positive 0.617) and O count (negative −0.548). Mean test-fold permutation
AUC drops (ten shuffles/fold) are 0.0543 for joint halogen columns, 0.0493 for N
count and 0.0304 for Cl count. Correlated features prevent causal or unique
importance attribution; coefficient/permutation values explain the raw formula
comparator, not the original PCA model. No independent evaluation set was used.

The two raw fingerprint models each produce 43 TP, 12 FN, 115 TN and 1 FP at 0.5,
although their probabilities differ. Morgan fingerprints encode radius-2 atom
neighborhoods (2048 bits, chirality included); raw logistic uses C=1 and the forest
uses 500 trees/minimum leaf 2. See the [diagnostic contract](docs/diagnostics-review.md#professor-follow-up-halogens-and-raw-fingerprints).
No accepted activity classifier, three-group biological result or safety claim
follows from these selection scores. Those require reviewed assay and comparison
labels plus independent validation.

Follow-up verification: **153 analysis tests** and analysis/notebook Ruff checks
pass. The selectively tracked
[marimo notebook](../notes/notebooks/findings.py) passes `marimo check`
and executes/exports successfully in the locked environment. It verifies saved
product hashes, recomputes all eight held-out metric pairs and checks shared
compound/scaffold folds before display. Its static HTML export remains local.
The candidate acquisition/review checkpoint is documented separately in the
[source guide](docs/compound_sources.md#dietary-comparator-review-pilot--2026-11-04).
The pipeline suite was not rerun for these analysis-only additions.

## Preliminary automated dietary review — 2026-11-04

The [triage workflow](docs/dietary-triage.md) analyzes the unchanged 40-candidate
review template using **95 saved requests**: 40 PubChem hazard sections, 40 toxicity
sections and 15 distinct food-use documents. All toxicity sections were retrieved;
xylitol's hazard section returned HTTP 404. Food-use checks use the official **2025
CFR edition** or FDA GRAS notices, confirming 38 named leads and two mixture-scoped
references (fructose/HFCS and maltose/malt syrup). They do not establish current
regulatory compliance or high-dose safety.

The frozen `dietary-triage-2026-11-04-final/` bundle assigns **12 provisional dietary
shortlist, 26 priority review, 2 excluded as presumed plant-negatives**. The excluded
cases are caprylic/capric acids, based on registered herbicide use. The standalone
`evidence_gap` category is zero because higher-priority flags take precedence;
**five rows still have gaps**: xylitol's absent hazard section; no extracted
toxicity text for xylitol, lactose and L-malic acid; lactose's missing GHS statement
field; and the two mixture-scoped food references.

The provisional list is glycerol, glycine, L-alanine, L-asparagine, L-aspartic acid,
L-glutamic acid, L-isoleucine, L-leucine, L-serine, L-threonine, L-tyrosine and
L-valine. These have named conditional food-use leads and no trigger under this
bounded policy. They are **not** verified benign at high doses or accepted controls.
The toxicity text pass promotes tryptophan, methionine, lysine and glutamine out of
the earlier GHS/agency-lead-only 16-candidate pilot shortlist. These are review
leads, not established harmful effects: source passages can include null findings,
co-exposures, other species or historical contamination.

The output preserves exact source passages/contributor context and distinguishes
handling, systemic GHS, population/dose and plant-comparator concerns. All safety
and plant-activity labels remain unknown. Neither supervised triage validation
against human decisions nor a comprehensive clinical/plant literature review has
been performed. No candidate was added to model training or existing labels changed.

Verification: **165 analysis tests** and analysis Ruff checks pass. Focused
regressions cover missing evidence, conflicting/suffixed GHS codes, exact human
versus non-human section matching, null-finding text hits, prior holds/overlaps,
source identity, preservation of human decision fields and frozen-source bytes.
All final triage input/policy/code/lock/product hashes agree. The pipeline suite
was not rerun for these analysis-only additions.

## Deeper assay-review package integration audit — 2026-11-05

The [integration assessment](docs/deeper-assay-review.md) audits all 16 files in
local `notes/compound_review_deeper_2026-10-29/`. All 15 listed release hashes match;
the first 16 source columns for all 157 observations match the original handoff,
and source snapshot hashes agree. All 154 packets retain their indexed structures
and observation IDs. Working activity/origin labels remain entirely unknown.

Its proposed 47 active / 31 low-response scenarios across three incompatible
policies are useful review leads. They are not an approved training set. The Li
2006 hypothetical known subset has only two low-response-bearing scaffolds; He's
50 hypothetical known outcomes occupy only two total scaffolds. Both fail current
three-/five-fold scaffold support. No classifier was fitted, no labels changed,
and the provisional files' successful schema parsing was not treated as approval.
The set has five exact structure overlaps with the original selection and none
with the 40 dietary candidates. These are complementary evidence workstreams,
not interchangeable negative labels or newly independent compound acquisitions.

The local audit bundle is `analysis/outputs/deeper-review-connection-2026-11-05/`,
including executed audit code, inventories, crosswalk/support tables and hashes.
The assessment records copied-link/access-summary inconsistencies and identifies
original source-table/structure mapping plus broader negative scaffold diversity
as the next dependencies. Original source files and unrelated dependency edits
were preserved; prior model performance and the full test suites were not rerun.

The updated follow-up notebook passes `marimo check` and Ruff and executes/exports
successfully. Its new section 6b verifies the audit products and displays the file/
study inventories, identity overlaps and hypothetical support checks.

## Verification release: identity hold and new leads — 2026-11-05

The [release assessment](docs/verification-release.md) reviews all 16 new files,
verifies all 15 listed hashes and reproduces 154 unique full InChIKeys. All 157
observations retain their original 16 source fields. Independently saved reference
retrievals reproduce 15 full external identity matches and one connectivity-only
comparison; they do not prove source result-to-structure mapping or accepted origin.

Li 7b / CHEMBL2253255 has a reported allyl-versus-frozen-cyclopropyl discrepancy.
The fresh overlay gives its unresolved identity hold precedence over historical
conditional activity: **46 active / 31 low response / 8 gray / 68 unassessed /
1 hold**, all unapproved. A hypothetical isomer illustration retains the same
formula while changing identity and 21 Morgan bits; no correction or activity
transfer is asserted. The compound is absent from the original selection cohort.

Of 11 new compound-name leads, five PubChem identity candidates have independently
consistent SMILES/keys and new fingerprints; six remain unresolved after name
queries. All targets remain null. Primary 2021 detached-leaf evidence provides
bounded no-lesion/weak-response review leads, not universal inactivity. No new
classifier was fitted: accepted activity/origin labels remain zero, and the
hypothetical subsets fail current scaffold support even after excluding the hold.

The fresh final audit and 28-request source bundle are cataloged in
[results](../docs/results.md#verification-release-audit--2026-11-05). Original
release files and editable human review files remain unchanged. A separate
proposal validator now rejects known activity labels on held IDs; its passing
result is not scientific approval. See the assessment for commands and next steps.

Verification: **178 analysis tests pass**, including 13 focused release/hold tests;
analysis Ruff checks pass. The checker accepts the unchanged 154-row unknown-label
working copy without writing to it. Regression tests reject source/identity/band
inconsistency, preserve missing reference/lead evidence and reject a schema-valid
known activity assignment to a held ID. No pipeline code or dependencies changed;
the unrelated pipeline dependency edits were preserved.

The professor follow-up notebook now incorporates these findings in its opening
presentation, exact verification steps and detailed section 6c, including the
hypothetical structure illustration and interactive reference/priority/lead tables.
It verifies every final-audit product hash before display. `marimo check`, notebook
Ruff checks and executed HTML export pass; the existing matched-model metrics are
rechecked from their frozen out-of-fold predictions, not refitted.

## Expanded dietary comparator identity audit — 2026-11-05

The user supplied 200 compounds reported verified benign in
`notes/plant_animal_food_compounds_200.tsv`. The [structural audit](docs/compound_sources.md#expanded-user-verified-dietary-list--2026-11-05)
checks all 200 distinct names/CIDs/keys and reproduces every supplied SMILES/key
pair. All 200 have Morgan fingerprints; 192 have supported formula features.
The four-column file does not include benignity citations/exposure/reviewer records;
PubChem CID correspondence and biological safety were not independently reverified.
No plant-inactive labels or model targets were inferred.

All 40 pilot identities are included, giving 160 additional exact identities.
There are 43 scaffold groups, including 98 ACYCLIC compounds. The original selection
has 16 exact overlaps (17 including connectivity-only matches); the 154 assay
candidates have none. Existing models and source files are unchanged. The fresh
`food-comparator-200-audit-2026-11-05/` bundle retains code, row-level identity and
overlap results, features, versions and hashes. The notebook opening and new
section 6.1 explain progress toward a dietary-comparator contrast while keeping
plant activity a separate target. Historical pilot review statuses are preserved.

Verification for this notebook update: all cell definitions are unique, the opening
executes in source order, `marimo check` and Ruff pass, and fresh executed HTML
export succeeds. All new audit input/code/output hashes match; the 200 feature
rows have unique full keys, nonmissing fingerprints and null model targets.
The full analysis test suite was not rerun for this notebook/documentation update.

## Weekly two-track pilots — 2026-11-10

The [pilot workflows](docs/weekly-pilots.md) now provide an offline acute rat oral
LD50 comparison, a literature-led structural review, model diagnostic additions,
and a verified cross-track walkthrough. All groups below remain purposive; no
activity/origin labels were approved and no biological model was fitted.

- **EPA LD50:** 5,814 cached hazard rows across 88 source chemicals yielded 43
  eligible exact and 25 censored acute rat oral records. There are 34 compounds
  with exact medians (26 selected herbicides, eight unreviewed natural-product
  selections), plus 15 censored-only compounds. Pooled linear tertile cutoffs are
  **1,080 and 3,400 mg/kg**, with ties retained. Lower LD50 means greater toxicity.
  The exploratory medians across retained acute contexts are not regulatory risk
  categories; source selection and heterogeneous study context limit inference.
- **Literature:** 15 name-resolved structures from four primary publications have
  matching PubChem/RDKit full keys; the source structures and occurrence/activity
  decisions remain provisional. Compared with 58 supported unique selected
  herbicides, these leads have median RDKit molecular weight 150.221 g/mol,
  calculated logP 1.793 and TPSA 37.3 Å². The 1998 phenolic source remains an
  abstract-level screen; 2020/2024 PDF treatment tables were visually checked.
  Formulation effects, 2020 control mortality and 2024 site-dependent responses
  prevent automatic universal labels. Citral mixtures are excluded.
- **Selection diagnostics:** on the same 171-compound five-fold scaffold cohort,
  formula-raw logistic F1 is **0.9143**, formula-PCA F1 **0.8972**, and raw Morgan
  logistic/forest F1 **0.8687** each at threshold 0.5. Raw formula coefficients
  are exported per fold and summarized by feature in the walkthrough. The separate
  full-cohort 500-tree forest OOB F1 is **0.9038**; 2,048 bit-level permutation
  diagnostics use 10 seeded repeats and a minimum of 84 OOB votes per compound.
  Repeat SD is not a significance test; OOB is not scaffold-independent validation.
- **ECOTOX:** the official September 15, 2026 ZIP reproduces 18,551 chemicals,
  725,635 tests, 1,250,611 results, 132,423 references and 29,651 species. Core
  primary/foreign keys and all archive member CRCs pass. There are 13,129 source
  chemicals with results, 104 candidate DTXSID selection overlaps, and a bounded
  100-row raw evidence sample. The 15,952 source records marked LD50 span source
  contexts and are not admitted rat oral measurements. Full normalization remains
  a follow-up. See [preflight contract](../pipeline/docs/epa-chembl.md#ecotox-bulk-inventory-preflight).
- **Cross-track review:** four literature leads overlap eligible cached EPA
  evidence (three exact, one censored-only); nine have candidate ECOTOX overlaps.
  These joins prioritize review without approving natural origin or plant labels.

The final local reading artifact is
`analysis/outputs/weekly-research-2026-11-10-final/walkthrough.html` with upstream
hash verification and source citations. The original acquisition resource was
preserved at its exact historical hash after later PDF annotations changed the
working resource; input-version resolution is explicit in the final manifest.
Frozen older bundles, raw snapshots, unknown-label worksheets and the Li 7b hold
were preserved. Full adapter development, primary isolation/source-identity review,
scientific activity-policy approval and independent negative-bearing chemistry
remain prerequisites for the intended three-group biological comparison.

## Evidence and comparable-toxicity expansion — 2026-11-11

The [expansion workflows](docs/weekly-pilots.md#expansion-compound-evidence-and-approval-handoff)
advance source evidence, ECOTOX observations and review preparation. They do not
approve scientific labels or fit biological models.

- The frozen cohort contains **104 source chemicals**, prioritizing the nine
  literature overlaps. Its complete **49,760 tests / 79,171 native results /
  79,302 concentration-slot records** are exported with snapshot/result/slot IDs,
  raw context JSON and source locators. Equal results remain separate. There are
  **3,267 complete** bounded-endpoint/unit parses and **76,035 review** slots;
  unsupported endpoints/codes/units remain visible. All source identity decisions
  remain candidates, so canonical compound IDs and canonical coverage remain null.
- Strict aquatic contexts yield **28 trout 96-hour mortality LC50 slots** (six
  measured, 22 unmeasured exposures) and **13 Daphnia 48-hour immobilization EC50
  slots** (one measured, 12 unmeasured), all active-ingredient basis and each from
  a distinct result within its stratum. No canonical comparison is admitted.
  Bulk source checks established Daphnia **ITX/IMBL**, not the draft BEH/IMBL;
  `IMM` means immunological. The context-verified bundle records the corrected
  explicit policy. No mortality/growth/immobilization endpoints are interchanged.
- All **15 literature leads** have compound packets, with **81 study/condition
  observations**, four unapproved activity-policy proposals and **32 origin/activity
  worksheet rows**. The original 1998 paper was recovered and its methods/results
  and figures inspected: solution tests use three dishes with 20 seeds each;
  lettuce and barnyard-millet observations occur at six and four days respectively;
  soil lettuce tests use four cups with five germinating seeds at five days.
  Graphical response magnitudes were not invented. Primary isolation or analytical
  characterization leads are linked independently; missing full texts, exact
  source structures, regiochemistry, stereochemistry and chemical forms remain
  review fields rather than accepted facts. Named structures reconstructed from
  the source nomenclature match all **15 database full InChIKeys**, including the
  three compounds with specified E geometry. This is explicitly a name-to-structure check, not
  independent spectral/drawing validation or source chemical-form approval.
- **Sarmentine dose conflict:** the 2015 methods say 10 mg/mL but weed-spectrum
  Table 1/2 headings say 20 mg/mL. Its seven-day injury band is retained as a band,
  and its activity proposal remains unknown. The 2020 water-control mortality,
  2024 site/formulation/dose differences, source melting-point/spectral consistency
  and natural free-acid versus ester occurrence remain explicit review issues.
- The historical rat oral baseline remains **43 exact observations / 34 compound
  medians**, with **25 censored observations** assigned compatible **observation**
  bins, not invented point values or compound-median labels. Frozen cutoffs remain
  **1,080/3,400 mg/kg**. Scenario-specific tertiles are separate. The strict
  reference/sex/strain/elapsed-duration subset is empty and is reported as
  insufficient documentation. No ECOTOX rat oral observations were admitted.
- The publication/chemical-hint review queue contains **18,992 pairs**, ranked
  by explicit context agreements. This is not a count of duplicates. No decisions
  were approved and no observations collapsed. Cross-source duplicate exclusion
  requires both source identity approval and signed same-observation evidence.
- All 15 seven-column accepted-label rows remain **unknown**; the frozen Li 7b
  identity hold is preserved byte-for-byte. Hypothetical source-policy proposals
  have positive/low-response counts **5/0, 3/0, 1/4, 0/0**, respectively; none has
  both-class five-fold scaffold support. These are readiness counts, not model
  results, and policies are not pooled. The existing 154-compound validator and
  historical worksheets remain unchanged.

The local final reading artifact is
`analysis/outputs/expansion-walkthrough-2026-11-11-verified/walkthrough.html`; it verifies
five upstream input/output manifests and links the editable review worksheets.
Source availability gaps and scientific approvals are outstanding research work,
not pipeline zeros, safe/unsafe assignments or permission to train on proposals.

## Human review adoption and new cohort models — 2026-11-11

The user supplied a human-reviewed second-pass workbook and explicitly approved
remaining supported prior proposals. The [adoption workflow](docs/human-review.md)
records that human-review assertion separately from the workbook's historical
AI-only wording. Specific second-pass decisions override the original proposals.
Original files, historical labels/results and the Li 7b hold remain unchanged.

- **Adopted evidence:** 19 natural-occurrence labels (15 second-pass compounds and
  four earlier ophiobolins), plus 80 bounded activity decisions under four separate
  policies. K1998 has 5 active/0 low-response; Okamoto 1991 4/0; Li 2006 11/10;
  He 2011 29/21. The latter three are adopted under the user's assertion of source
  review, with original review flags retained in the ledger. Three explicit Li
  identity gaps remain excluded: 7b constitutional isomer, unreadable 7w and
  unresolved comparator geometry. Manufacturing provenance is not converted to
  a canonical synthetic-origin label. Unknown outcomes remain unknown.
- **Revised evidence interpretation:** the second-pass workbook contains 119
  study/treatment observations. It withdraws formulation-only ingredient activity
  and field low-response labels; LSD non-significance does not establish
  equivalence. Sarmentine remains unknown due to dose/formulation ambiguity.
  Five 1998 classifications reproduce the authors' two-species very-active reagent
  category at 1 mM (lettuce day six, millet day four), not a general quantitative
  efficacy estimate. Walker 2003 is retracted and excluded; independent Farag 2022
  evidence supports trans-cinnamic-acid occurrence. Independent sources also
  replace the anomalous salicylic-acid isolation citation and support free
  pelargonic-acid occurrence.
- **Activity model checks:** no activity estimator is fitted. Li's 21 accepted
  examples occupy three active-bearing/two low-response-bearing scaffolds; He
  has only two scaffolds in each class. K1998 and Okamoto lack a low-response
  class. All four representations retain explicit class/scaffold insufficiency
  and null scores under each policy; no incompatible assays are pooled.
- **New structural models:** a distinct 30-compound purposive cohort contrast uses
  19 approved natural-occurrence examples (seven scaffold groups) versus 11
  documented commercial-herbicide manufacturing comparators (six scaffold groups).
  Target 1 is commercial comparator membership, not activity or absence of natural
  occurrence. Eight fixed profiles share all 30 structures and five scaffold folds.
  Raw/PCA formula F1 is **0.8421**, Morgan logistic **0.6667**, forest **0.6000**,
  and halogen-only/presence **0.9000**. Formula AUROC is 1.0, with three false
  negatives at the fixed 0.5 threshold; perfect ranking is not calibration or
  prospective validation. These scores cannot be interpreted as changes in the
  historical 171-compound task's performance.
- **Interpretation:** new raw-formula mean coefficients include distinct-element
  count +0.9123, chlorine count +0.8404 and nitrogen count +0.5141 on the fold-local
  standardized scale. They are correlated-feature associations, not causal
  molecular modifications. The separate full-cohort forest OOB F1 is **0.9000**
  with at least **111** OOB votes per compound and 10-repeat permutation summaries
  for all 2,048 bits. The gap from scaffold-held-out F1 illustrates the weaker
  structural separation of OOB evaluation. Repeat SD is not statistical significance.
- **Biological description:** five approved K1998 natural active compounds span
  three scaffolds, with median MW **150.177 g/mol**, calculated logP **1.7038** and
  TPSA **37.3 Å²**. The 58 supported unique selected-herbicide comparators have
  corresponding medians **279.1135**, **2.90424**, **62.73**. Fourteen other approved
  natural compounds remain activity-unknown under K1998. The natural low-response
  group is explicitly empty; these are descriptive samples, not a validated
  three-class biological dataset.
- **Rat oral LD50:** all 43 exact observations, 34 exact compound medians, 25 bounds
  and frozen 1,080/3,400 mg/kg cutoffs remain unchanged. Approved occurrence now
  identifies coumarin (active under K1998, median **520 mg/kg**), salicylic acid
  (activity unknown, **891 mg/kg**), benzoic acid (activity unknown, **2,565 mg/kg**)
  and trans-cinnamic acid (active, censored-only). The three exact reviewed-natural
  medians and single active exact median cannot establish a safety advantage.
  ECOTOX source identities remain candidates rather than inheriting approval from
  DTXSID overlap; no ecological or mammalian endpoints are pooled.

The local [result inventory](../docs/results.md) links the adopted evidence,
new model bundle and `human-reviewed-progress-2026-11-11-complete/walkthrough.html`.
The ignored learning notebook's opening now shows the new decisions, 30-compound
scores, coefficients/OOB diagnostics, policy support, biological descriptors and
LD50 annotations. Historical 171-compound results remain separately labeled.

Verification for this adoption/modeling checkpoint: **232 analysis tests pass**,
analysis and notebook Ruff checks pass, and the updated marimo notebook executes
all **67 cells** and exports without errors. All 22 adoption, six model and 11
synthesis output hashes match; model scores are independently recomputed from
held-out predictions. The source workbook hash and original hold bytes are
unchanged. Final descriptor/model/LD50 figures were rendered and visually
inspected. No pipeline implementation changed, so its full suite was not rerun.

## Explicit ECOTOX identity approval and comparisons — 2026-11-11

The user explicitly confirmed human review and approval of **all 104 frozen
ECOTOX source-to-canonical mappings**. The [identity-adoption workflow](docs/human-review.md#explicit-ecotox-identity-approval)
binds that assertion to the frozen source snapshot and exact mapping pairs,
checks canonical SMILES/key consistency, and preserves the original candidate
crosswalk. A whole-form salt mapping remains usable for evidence attachment even
when its multicomponent structure is excluded from structural models; no parent
conversion or biological-label inference occurs.

The full selected-cohort reimport reproduces **49,760 tests, 79,171 native results
and 79,302 concentration slots**. All scientific native/measurement fields are
identical; only canonical identity attachment/status changes. All 104 mappings
are approved. Normalization remains 3,267 complete / 76,035 review slots; identity
approval does not repair unsupported endpoints, codes, units or numeric values.

Core policy admission now attaches canonical IDs to **28 trout mortality LC50
records across seven compounds** and **13 Daphnia immobilization EC50 records
across 11 compounds**. There are 39 exact values and two lower bounds. Each slot
is a distinct native result and test within its policy; publication/study
independence is not established. Trout exposure analysis is six measured / 22
unmeasured; Daphnia is one measured / 12 unmeasured, all active-ingredient basis.
Different formulation, exposure type, medium and exposure duration remain strata.

**Observation duration is not automatically exposure duration.** The core screens
use reported observation times of 96/48 hours. The reported-context sensitivity
requires exposure type, a reported control type and equal exposure/observation
duration. It retains **zero trout and one Daphnia record**. Reported fields do not
establish study quality. Missing actual exposure-duration metadata limits claims
of fully harmonized continuous 96-/48-hour exposures, and pH/temperature/age can
still vary. Source-record medians remain descriptive rather than pooled effects.

Approved natural-occurrence overlaps include six juglone trout records (active
under K1998), one eugenol trout record (activity unknown under K1998), and benzoic
acid/salicylic acid Daphnia records (activity unknown). All nine are unmeasured-
concentration records and fail the additional exposure/control documentation
subset. None establishes a biological-group safety ranking. The two censored
Daphnia results remain bounds, not point estimates or substituted medians.

The updated cross-source queue still contains **18,992 candidate pairs**; identity
link status is now approved where relevant, but no same-observation decisions were
supplied and no results were collapsed. Excluding unresolved overlap candidates
does not remove any of the 41 admitted aquatic observations. The 16 ECOTOX rat
LD50 records retain explicit context-review reasons, including dietary routes,
unsupported body-weight/acid-equivalent units and absence of an explicit acute
test type. No title-only acute inference is made. The historical **43 exact /
25 censored observations, 34 compound medians and 1,080/3,400 mg/kg cutoffs remain
unchanged**. Plant-activity training labels/features are unchanged; no new
classifier was fitted for this identity-only update.

The new standalone reading artifact is
`analysis/outputs/ecotox-approved-comparison-2026-11-11-verified/walkthrough.html`.
The ignored marimo notebook/HTML now open with the identity-approved coverage,
individual aquatic values, exposure/context sensitivities, row accounting and rat
review queue. Older candidate-only status is explicitly historical. A temporary
disk-space failure was resolved by sharing verified byte-identical native export
storage; both old/new file paths, scientific bytes and hashes are preserved.

All 104 source mappings are approved, but only 103 have result records.
Acacetin (`ECOTOX:chemical:480444` / `PUBCHEM:5280442`) has zero results in the
frozen snapshot and remains an assessed zero in source coverage. The reconciliation
manifest’s `approved_ecotox_identities` counts observed canonical IDs (103), not
the full approved crosswalk (104). Zero coverage supplies no safety/activity label.

Verification: **248 analysis tests and 1,057 pipeline tests pass**; analysis and
notebook Ruff checks pass. All **74 marimo cells** execute and the HTML export
contains the current coverage/context distinctions. All 31 outputs across the
four new identity/import/reconciliation/comparison bundles match their manifests.
Native/result and measurement-field equality, canonical attachment, zero-hit
coverage, original source hashes, links and native Markdown cells are checked.
The final aquatic and exposure figures were rendered and visually inspected.

## Permissive activity expansion and publication transfer — 2026-11-12

The [experimental checkpoint](docs/experimental-expansion-2026-11-12.md) records
the owner's authorized relaxation of scientific adoption for local experiments.
It does not change accepted human labels or frozen sources. Sixteen primary-study
leads were screened; eight full texts cached; seven studies yielded **304 plant
and 59 other endpoint observations**, including controls and repeated conditions.
New transcriptions and source-to-structure mappings remain explicitly provisional.

The accepted four activity policies still fail five-fold class/scaffold support.
An intentionally heterogeneous sensitivity policy pools 21 Li rows, 50 He rows
and two provisional Ambrosia compounds: **73 structures, 41 high-response and
32 low-response labels**, with six/five class-bearing scaffold groups. It predicts
source-specific response extremes under different species/dose/endpoint rules,
not a shared herbicidal-activity definition.

Raw Morgan logistic scaffold F1 is **0.7273**, versus training-majority F1
**0.7193**; balanced accuracy is 0.6559 and AUROC 0.6791. Publication-held-out F1
drops to **0.3000 for Li and 0.5538 for He**, both below their majority baselines.
Formula PCA is near chance; the forest's OOB F1 0.7436 does not supply scaffold
independence or formal significance. Fixed shuffled-label controls, standardized
formula weights, tree-specific OOB permutation and all predefined model reports
are retained. No profile was promoted to candidate screening.

The work also adds generic no-fit activity preflight, alias-aware publication
transfer with scaffold purging, and fixes duplicate decisions lost between
reconciliation queues and downstream aquatic sensitivities. A fresh ECOTOX run
preserves the 28 trout/13 Daphnia admissions and 16 rat review records; no real
duplicate decisions or rat additions were inferred.

The local entry point is
`analysis/outputs/experimental-research-checkpoint-2026-11-12/walkthrough.html`;
the tracked checkpoint gives assumptions, failed retrievals, unresolved identities,
commands and exact input/output locations. Fifteen manifests verified; figures
rendered/inspected; **270 analysis tests and Ruff passed**. Pipeline tests were
not rerun because pipeline code did not change. No transferable activity model,
safer candidate or validated binding workflow is established by these experiments.

## Source-linked aquatic context sensitivity — 2026-11-12

The new [context-overlay contract](docs/human-review.md#source-linked-aquatic-context-overlays)
preserves native observations while accepting explicit field-level proposals with
source hashes, original-value checks, reviewer/date and uncertainty states.
Default reviewed mode requires verified full-text scientific review. Explicit
experimental mode also permits provisional primary abstracts and AI review; those
conditions remain visible in the audit and manifest. Nonmissing contradictions
cannot silently override the native context. All admitted sibling slots of a test
need consistent explicit decisions.

A real-data experiment uses the [primary-authored Kamaya abstract](https://pubmed.ncbi.nlm.nih.gov/15722097/)
retrieved as verified PMID-matching NCBI XML after HTML-content checks failed.
Its initial pH 7.45 ±0.05 is provisionally associated with eight reference80404
observations. Reviewed mode applies zero fields; experimental mode adds eight pH
metadata fields. **All original fields of the 41 observations remain unchanged**,
including concentrations/qualifiers, native contexts and identities. Core counts
remain 28 trout/13 Daphnia; the reported-context subset stays zero trout/one Daphnia.
No exposure duration, measured concentration, control response or rat admission is
inferred. pH metadata do not automatically harmonize the existing summary strata.

Local bundles are `aquatic-context-reviewed-2026-11-12/` and
`aquatic-context-experimental-2026-11-12/` under `analysis/outputs/`; acquisition,
proposals, verification and the exact hash-matching run source are under ignored
`experiments/aquatic-context-2026-11-12/`. Both new manifests and the frozen input
manifest verify. **287 analysis tests and Ruff pass**; pipeline code/tests were
unchanged/not rerun. The experiment demonstrates the software integration and its
limits: abstract metadata do not replace original protocol/result-cell recovery.

## Natural-product structural binding pilot — 2026-11-12

The [binding-evidence contract and checkpoint](docs/binding-evidence.md) audits
**two experimental X-ray complexes and three deposited protein constructs** from
primary sources/RCSB, separately from activity/origin labels and toxicity models.
Tentoxin in [1KMH](https://www.rcsb.org/structure/1KMH) matches its parent full
InChIKey and involves spinach chloroplast ATPase alpha/beta entities. The
[8CI0](https://www.rcsb.org/structure/8CI0) inhibitor is cornexistin's diacid `UP0`,
with a different exact identity from parent cornexistin. The paper's presumed
anhydride-hydrolysis relationship is connectivity-consistent; full stereochemical
provenance remains a review task.

The default 8CI0 ligand-interaction link instead selected `8EL`, a thiamine-related
cofactor. Following the actual non-polymer inventory and checking chemical form
rejected that erroneous parent/inhibitor substitution. The cofactor is not a
negative-binding example. Maize protein origin remains distinct from its E. coli
expression host; UniProt sequence versions and weed ortholog mappings are unknown.

A companion table retains 15 author-reported contacts without remapping paper
residue/monomer labels or calculating distances. The reported maize transketolase
IC50 50 ±5 μM remains functional inhibition, and the tentoxin preparation
concentration remains preparation metadata. Neither becomes a Kd/Ki. No binding
classifier, new natural-origin label or safety claim is produced.

Local sources/resource/curation/figure are under
`experiments/binding-pilot-2026-11-12/`; the canonical output is
`analysis/outputs/binding-structural-pilot-2026-11-12-final/`. Final catalog,
curation and figure manifests verify, and the chemical-form comparison was
rendered and inspected. **299 analysis tests and Ruff pass**. Pipeline code/tests
were unchanged/not rerun. Original isolation evidence, density/ligand quality,
affinity measurements and independent prediction remain unfinished research.

## Compatible-assay low-response expansion — 2026-11-12

The [experimental checkpoint](docs/experimental-expansion-2026-11-12.md#compatible-flavonoid-series-expansion)
adds 324 source-linked observations for 27 compounds in a complete two-species,
three-dose germination/root-growth series. Twelve retrospective assay policies
remain separate. Each 100 µM root-growth policy has 2 high, 18 low-inhibition and
7 intermediate responses; the labeled structures span two high-bearing and nine
low-bearing scaffold groups. This recovers broader low-response chemistry, but
all representations fail five-fold support and no model was fitted.

Six constitutional parent/O-methylated pairs give descriptive comparisons of
rounded group means, with source SDs preserved and no inferred uncertainty or
causation. All 27 unique PubChem name mappings remain provisional; no natural
occurrence or accepted activity labels were added. Local reproduction, figures,
source checks and 136 verified hashes are in
`experiments/compatible-assays-2026-11-12/`; use the complete `analysis-v2/`.
Two recovered large-library papers remain leads rather than negative training
sets because selection, endpoint and data-access limitations are unresolved.

## Fixed-model transfer to a new root-growth paper — 2026-11-12

The [follow-on transfer experiment](docs/experimental-expansion-2026-11-12.md#fixed-transfer-to-the-recovered-root-growth-series)
keeps the earlier 73 training compounds and model settings fixed, testing 20 new
radish root-growth compounds (2 high/18 low) from the recovered paper. Formula
logistic, Morgan logistic and Morgan forest all miss both high responses: F1 0,
balanced accuracy 0.4444/0.2778/0.2500. Training-majority baseline F1 is 0.1818.
Scaffold purging removes 21 He2011 benzene-group compounds; Morgan recall rises
to 1.0 but precision is only 0.1333/0.1111, with 13/16 false positives. This is
unstable transfer across incompatible assay contexts, not a selected improvement.

The primary test was specified before these scores, with no tuning. Seven
intermediate responses stay unknown and all original 73 feature/label values
remain unchanged apart from the extended common experimental policy name.
`analysis/outputs/experimental-flavonoid-transfer-2026-11-12/` retains all four
publication holdouts. Local verification recomputes 24 reports from 558
predictions and checks split membership plus 94 hashes. This provides another
explicit failed transfer experiment, without candidate scoring or a safety claim.

## Primary rat-source review and dose-basis sensitivity — 2026-11-12

The [source-review checkpoint](docs/rat-source-review-2026-11-12.md) maps two
pending 2,4-D records to male/female single-dose oral results in primary Table 1.
The source reports acid-equivalent and material-tested doses separately. Native
dietary metadata conflict with the acute methods; explicit gavage/capsule
technique remains unresolved. The two source-reported acid-equivalent cases are
provisionally eligible only under a separate AI experimental single-dose oral
policy, with zero historical admissions.

Four priority pairs are experimentally adjudicated `different_observation`:
EPA counterparts are 91-day dietary LOELs rather than acute LD50s. The existing
importer adopts all four in the new reconciliation queue. Full-table arithmetic
also flags two other female ester conversions inconsistent with the displayed
formula; reinspection confirms transcription, and printed values stay unchanged.

Relaxed mixed-basis arithmetic shifts the 2,4-D median from 375 to 607 mg/kg by
record pooling, or 520.75 after first aggregating the new paper's two sexes.
Unknown historical dose basis/lineage prevents a harmonized comparison. All
34 exact-median bins and 1,080/3,400 mg/kg cutoffs remain unchanged; 25 bounds are
preserved. Verification checks 14 table cells, two flags, two case mappings,
four adopted decisions, three scenarios and 45 hashes. Separate elapsed-week
support preserves native two-week times without implying acute exposure;
1,076 pipeline tests, 299 analysis tests and pipeline Ruff pass. Frozen evidence
and biological labels remain unchanged; no model or safer candidate is produced.

## Separate experimental and external-model evidence — 2026-11-12

The [first A/B checkpoint](docs/modeled-evidence-2026-11-12.md) records new public
bulk acquisition and separate provisional outcomes: 4,234 exact experimental
compound summaries and 43,128 eligible CATMoS structures. A separate dietary
TEST batch raises coverage from 136 to 173 full structures, leaving two identity
reviews open. All measured/predicted labels, raw failures and exclusions remain
separate; historical rat admissions and human labels are unchanged.

Fixed scaffold/connectivity-held-out forest macro-F1 is 0.430 A versus majority
0.226, and 0.616 B versus majority 0.200. A forest log-dose MAE is 0.636 versus
median baseline 0.650; B MAE is teacher reproduction, not experimental accuracy.
Per-fold coefficients, OOB stability, metrics, support and membership are retained.
Only 3,361 structures pair; 3,359 carry teacher-training tags, so their high
agreement cannot supply independent validation. C is deferred. Archive-specific
CATMoS scale interpretation, original-study/form provenance, publication/provider
holdouts, qualified external plant-activity models and further source collection
remain unresolved. The checkpoint lists canonical bundles, exact verification
and the next-source backlog; all scientific assets remain local and ignored.


## Same-target multiclass OOB exploration — 2026-11-12

The frozen A/B cohorts (4,234 experimental / 43,128 external CATMoS estimates)
now have additional full-cohort forest diagnostics for the primary three-class
LD50 target. OOB macro-F1 is 0.484 / 0.729; the scaffold-held-out forest
macro-F1 remains 0.430 / 0.616. Ten within-tree OOB permutation repeats place
TPSA first in both forests. Repeat SD describes stability, not significance;
B measures reproduction of stored teacher estimates rather than measured toxicity.
See the [checkpoint](docs/modeled-evidence-2026-11-12.md#same-target-oob-exploration-and-local-notebook)
for feature drops, exact biological group intersections, provenance and the local
experimental notebook. Earlier binary OOB and frozen validation results remain
preserved.
# Data-first source yield — 17 November 2026

The [dated sprint checkpoint](docs/data-sprint-2026-11-17.md) records an AI
experimental, provenance-linked source audit against unchanged A/B and selection
memberships. COCONUT matches 1,478/4,234 A structures (34.9%), NPASS 793, and either
catalog 1,617. NPASS taxon/publication links cover 476 A structures, pending primary
review. Catalog membership does not establish independently verified occurrence.

NPASS toxicity lacks route/acute/experimental-status fields. Bounded ToxValDB source
screening finds 445 candidate new exact-value structures and 884 additional
censored-only structures through local identifier links; form/independence holds
prevent admission. Confirmed net-new eligible structures remain zero, independent
study novelty unknown. ECOTOX adds a review inventory of 73,317 non-algal plant
growth/germination/biomass results, with no new labels. All four accepted plant
policies still fail existing class/scaffold support. Only one A structure has
already adopted occurrence and plant-response evidence. No new model was fitted.
