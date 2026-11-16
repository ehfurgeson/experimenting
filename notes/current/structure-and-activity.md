# Structural models and reviewed activity

Current orientation, reviewed 2026-11-02. Read the
[structural workflow](../../analysis/docs/structural-screening.md) and
[analysis decisions](../../analysis/docs/decisions.md) for executable contracts.

## Implemented work

RDKit derives descriptors, Morgan fingerprints, scaffolds, formula features,
Lipinski/Tice-inspired proxies and Ertl synthetic accessibility. These proxies
are not demonstrations of herbicidal efficacy or safe field application.
Unsupported/multicomponent chemistry and formula/InChIKey mismatches remain explicit
review states. Identity auditing uses complete elemental composition separately
from the fixed predictor representation.

Structural evaluation separates the curated selection target from independently
reviewed origin and activity. Canonical structures are deduplicated for evaluation;
conflicting known labels raise. Scaffold-held-out folds use training-only
preprocessing. Insufficient class/scaffold support produces explicit unsupported
results rather than a fallback favorable split.

Stress controls compare representations on the same eligible cohort with shuffled
labels, fold sensitivity and dominant-scaffold removal. Ablations compare nine
feature/preprocessing profiles with fixed C or inner-scaffold C selection. These
remain diagnostics; they do not silently replace production models.

## Results belong to their checkpoint

[Findings](../../analysis/FINDINGS.md) records the 2026-10-27 baseline,
2026-10-28 common-cohort stress checks and 2026-10-29 fixed/nested ablations.
Their cohorts and validation designs differ from the older presentation model.
Formula's ability to distinguish the curated selection is not proof of activity,
natural origin or a causal elemental effect. Nested regularization explains much
of the earlier combined-model gap; choosing a profile after inspecting outer-fold
scores still needs independent confirmation.

## Missing scientific input

The inspected 154-row handoff worksheet still has `unknown` activity and origin
labels throughout. Frozen ChEMBL snapshots preserve 157 measurements from 14 assays
and publications, but heterogeneous dose/species/time/qualifier context prevents
automatic universal active/inactive assignment. A tested low response under one
assay is not a generic negative label.

Use the [researcher label guide](../../analysis/docs/label_review_guide.md) to
review original methods, declare an activity policy, record observations/conflicts,
and cite natural occurrence separately. Preserve baseline templates and save
reviewed labels as versioned research inputs.

## Candidate scoring and limits

The code supports candidate scores from reviewed activity models when its support
guards pass, with training-similarity and scaffold context. Synthetic tests cover
that route. The recorded real-data production candidate run has unavailable
activity models and null probabilities; no accepted real activity classifier,
calibration or broad natural-product prioritization is established.

Before broader screening, obtain adequate reviewed positive and tested-negative
chemistry, reserve independent publication/chemical evidence, evaluate calibration
and domain limits, and record the model/label/input versions. Descriptor completeness
or strong selection accuracy alone does not satisfy these dependencies.


## Local review notebook — 2026-11-03

The [professor-review notebook](../notebooks/README.md) inspects existing features,
matched-cohort fixed/nested models, held-out errors, PCA/stress diagnostics and
label readiness against the professor's requested milestones. It is read-only and
local; no model fitting, label curation or scientific result replacement is implied.
The reviewed activity/origin working copy remains unknown in the inspected bundle.


## Professor follow-up — 2026-11-04

New matched-cohort halogen diagnostics reproduce the original formula result
and show substantial halogen signal alongside non-halogen composition signal.
Raw Morgan logistic and forest comparisons are also available; see the dated
[findings](../../analysis/FINDINGS.md#halogen-attribution-and-raw-fingerprint-classifiers--2026-11-04).
The [new notebook](../notebooks/findings.py) explains methods/results,
errors and required decisions. A 40-identity dietary pilot now has PubChem/RDKit
identity agreement, explicit review caveats/holds and overlap checks, but no
accepted high-dose safety or plant-inactivity labels. Existing reviewed activity
inputs and frozen historical runs were preserved. The actual three-group
biological comparison and independent activity validation remain dependencies.


A preliminary automated review now prioritizes the 40 dietary candidates using
95 frozen PubChem/food-use requests plus dated curated agency leads and bounded
text screens. It produces 12 provisional dietary candidates, 26 priority reviews
and 2 presumed-plant-negative exclusions. These remain review categories, not
accepted labels. Five rows have retained gaps; all safety and plant-activity
labels remain unknown. See the [workflow contract](../../analysis/docs/dietary-triage.md)
and notebook section 6a for reasons, passages and human decisions.


## Deeper assay-review package connection — 2026-11-05

The 16-file `notes/compound_review_deeper_2026-10-29/` package contains additional
study-level annotations on the existing 154 ChEMBL compounds. Its 47 conditional
active / 31 conditional low-response scenarios are unapproved; source mapping and
quality remain unresolved. A complete integrity/lineage audit confirms preserved
source fields, five original-selection structure overlaps and no dietary-list
overlap. Hypothetical Li/He subsets fail current three-/five-fold scaffold support;
no activity model was fitted or labels promoted. See the maintained
[integration assessment](../../analysis/docs/deeper-assay-review.md) and notebook
section 6b for the full file inventory, cautions and highest-value review steps.

## New verification release — 2026-11-05

The [release assessment](../../analysis/docs/verification-release.md) independently
reproduces 15 full external identity matches and one connectivity-only comparison.
Li 7b / CHEMBL2253255 now has an unresolved source-identity hold overriding the
historical conditional active scenario (effective 46 active, 31 low response,
8 gray, 68 unassessed, one hold; all unapproved). Five of 11 new named leads have
provisional PubChem identities/fingerprints; six name queries remain unresolved.
Source drawings, bounded policies and independent negative-bearing chemistry still
block activity modeling. No accepted labels or new classifier fits were produced.
The notebook's presentation overview and section 6c reflect this follow-up.

## Expanded dietary comparison — 2026-11-05

The user now reports 200 verified-benign dietary compounds. Their supplied
SMILES/key pairs all agree; all have fingerprints and 192 have supported formula
features. They include all 40 pilot identities, add 160 exact identities, occupy
43 scaffold groups (98 ACYCLIC), and overlap the original selection at 16 full keys
(17 including connectivity-only). A separate frozen structural audit assigns no
biological targets; benignity evidence/limits are not in the four-column TSV and
plant inactivity is not implied. See [source contract](../../analysis/docs/compound_sources.md#expanded-user-verified-dietary-list--2026-11-05)
and notebook section 6.1 for the counts, overlaps and next modeling distinction.


## Weekly pilots — 2026-11-10

The [tracked checkpoint](../../analysis/FINDINGS.md#weekly-two-track-pilots--2026-11-10)
adds the conservative rat oral LD50 pilot, 15 provisional literature identities
from four publications, F1/logistic-weight/OOB diagnostics and the ECOTOX source
inventory. No origin/activity approvals, tested-negative cohort or biological
model were established. The standalone local walkthrough is at
`analysis/outputs/weekly-research-2026-11-10-final/walkthrough.html`.


## Source evidence and proposal readiness — 2026-11-11

All 15 named-structure reconstructions match database full keys; source spectra,
chemical form and scientific approval remain separate. Four proposed activity
policies remain unapproved and none has both-class five-fold scaffold support.
The verified review exports 81 observations and 32 origin/activity worksheet rows;
accepted seven-column labels remain unknown and the Li 7b hold is preserved.
See the [checkpoint](../../analysis/FINDINGS.md#evidence-and-comparable-toxicity-expansion--2026-11-11).


## Human review adoption — 11 November 2026

The user supplied the human-reviewed second-pass XLSX and approved remaining
supported proposals. The new versioned adoption bundle has 19 natural-occurrence
labels and 80 decisions in four bounded activity policies; it preserves explicit
Li gaps and the revised workbook's unknown field/formulation outcomes. None of
the activity policies supports the existing five-fold class/scaffold requirements.
A separate 19-versus-11 reviewed provenance-cohort comparison was fitted without
turning activity-unknown examples into negatives. See the current
[contract](../../analysis/docs/human-review.md),
[findings](../../analysis/FINDINGS.md#human-review-adoption-and-new-cohort-models--2026-11-11)
and result inventory. The original 154-row working templates remain unchanged;
accepted labels reside in the new adoption bundle, not those historical files.

## Local permissive experiments — 12 November 2026

On local-only branch `experiment/bioherbicide-expansion-2026-11-12`, a deliberately
heterogeneous 73-compound pool supports computational fitting but fails
publication transfer. A complete 27-compound flavonoid-series source now adds
324 observations and 18 low-inhibition compounds across nine scaffold groups
under each separate 100 µM root policy; only two high responses remain, so the
individual policies still cannot fit five folds. Identities and new rules remain
AI experimental; accepted origin/activity evidence is unchanged.

The fixed 73-compound models all miss both high responses in the new 20-compound
radish test. Purging 21 shared benzene-scaffold training compounds yields many
false positives instead. No transferable activity model or safer candidate is
established. See the maintained [experimental checkpoint](../../analysis/docs/experimental-expansion-2026-11-12.md)
for source provenance, fixed protocols, descriptive O-methylation comparisons,
failed acquisitions, metrics and verified local artifacts. Next value is a
chemically diverse **compatible-assay** series with high and low responses;
adding arbitrary low-response rows to the heterogeneous pool did not fix transfer.
