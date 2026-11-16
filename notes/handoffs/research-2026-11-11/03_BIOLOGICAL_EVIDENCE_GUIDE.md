# Research guide B: biological evidence and independent chemistry

**Assignment:** build a defensible natural low-response comparison and increase independent scaffold support for activity modeling. Start with the [project handoff](01_PROJECT_HANDOFF.md). Your first deliverable is source-linked evidence and policy-separated decisions, not a higher model score.

## 1. What is already accepted

There are **19 natural-occurrence labels** and **80 activity decisions under four separate policies**. The owner has already approved the supported decisions and all 104 ECOTOX identity mappings. Do not repeat those blanket approvals. Investigate a previously accepted item again only if new evidence creates a specific contradiction.

The five natural active examples under K1998 are 3-phenylpropionic acid, 2-hydroxyphenylacetic acid, coumarin, juglone and trans-cinnamic acid. Fourteen other approved-natural compounds have unknown activity under that policy. There is no validated natural low-response class under K1998.

| Policy | Active / low-response | Scaffold support, active / low-response | Necessary five-fold scaffold deficits |
|---|---|---|---|
| K1998 two-species category | 5 / 0 | 3 / 0 | At least 2 additional active-bearing groups and 5 negative-bearing groups; no existing negative rule |
| Okamoto 1991 upland | 4 / 0 | 1 / 0 | At least 4 additional active-bearing groups and 5 negative-bearing groups; also at least one more active compound |
| Li 2006 post, 150 g a.i./ha | 11 / 10 | 3 / 2 | At least 2 additional active-bearing and 3 negative-bearing groups |
| He 2011 post, 1,500 g a.i./ha | 29 / 21 | 2 / 2 | At least 3 additional active-bearing and 3 negative-bearing groups |

The accepted IDs are source-specific. More structures in an original study can be reviewed within its scope; adding another publication generally needs an explicitly broadened policy version and re-adjudication, even when its headline dose/species match. The existing published series may not contain enough new cores.

These are **lower bounds on class-bearing scaffold deficits**, not promises that adding those numbers of compounds will make validation work. A new scaffold can bear both classes; actual grouped folds still must contain both classes in training and testing. Extra analogues from an existing core do not fill the deficit.

## 2. Starting files and approval precedence

| File in `reference_inputs/biology/` | Purpose |
|---|---|
| [adoption_ledger.csv](reference_inputs/biology/adoption_ledger.csv) | Thirty-two second-pass compound/axis decisions, including original versus adopted proposals, unresolved reasons and source locators |
| [legacy_adoption_ledger.csv](reference_inputs/biology/legacy_adoption_ledger.csv) | Historical assay proposal adoption and explicit exclusions |
| [second_pass_observations.csv](reference_inputs/biology/second_pass_observations.csv) | All 119 study/condition observations, source DOI and treatment context |
| [accepted_activity_features.csv](reference_inputs/biology/accepted_activity_features.csv) | Eighty accepted policy-specific activity rows with chemistry, context and citations |
| [activity_model_support.csv](reference_inputs/biology/activity_model_support.csv) | Actual class/scaffold support checks across four representations; no fitted activity model |
| [reviewed_group_membership.csv](reference_inputs/biology/reviewed_group_membership.csv), [descriptor_summary.csv](reference_inputs/biology/descriptor_summary.csv) | Reviewed biological descriptions and selected-herbicide comparator structures |
| [origin_labels.csv](reference_inputs/biology/origin_labels.csv), [policy label files](reference_inputs/README.md) | Seven-column schema; keep each activity policy separate |
| [li_source_crosswalk.csv](reference_inputs/biology/li_source_crosswalk.csv), [identity_holds.csv](reference_inputs/biology/identity_holds.csv) | Three explicit Li source gaps and the frozen 7b hold |
| [original_assay_evidence_history.csv](reference_inputs/biology/original_assay_evidence_history.csv) | Original 154-compound / 157-observation assay history; raw IDs and values remain preserved |
| [additional_literature_leads.csv](reference_inputs/biology/additional_literature_leads.csv) | Further source leads, including the separate 2021 foxtail-leaf work; not accepted activity labels |

Current acceptance is established by the **adoption ledgers, human declaration and accepted policy files**, not an old source file's `NOT_FOR_TRAINING` or pending-signoff wording. Conversely, `HUMAN-` in a filename does not make unknown outcomes known: M2020, T2024 and D2015 policy CSVs contain no known activity labels. Old templates remain intentionally unchanged.

## 3. The first research assignment

Produce a policy/cohort plan and an initial literature screen before doing extensive transcription.

1. Inspect existing active and low-response structures by scaffold. Identify which candidate papers could supply genuinely new cores, rather than more derivatives of the same core.
2. Select one coherent comparison question. If proposing a broader Li-/He-like assay cohort, require compatible species, growth stage, application route, dose, duration, endpoint and response rule, and define a new eligible-publication scope before combining studies. A 150 g/ha visual-injury assay is not the same as a 1,500 g/ha fresh-weight assay.
3. Search for primary experimental papers that report the **full tested series**, including weak/null results, controls and methods. Avoid collecting only compounds highlighted as active in abstracts.
4. Triage candidates for exact identity, source access, actual plant testing, a usable low-response definition, and new scaffold contribution. Origin evidence can be researched in parallel; an active/low-response compound need not be natural to contribute to an assay model, but natural occurrence is separately required for the natural subgroup.
5. Transcribe the highest-value studies completely. Return rejected/unresolved leads too, so the next researcher does not repeat the same failed searches.

Suggested search patterns are query templates, not assertions that any hit is suitable:

```text
("natural product" OR allelochemical OR phytotoxin) (radicle OR seedling)
("inactive" OR "weak activity" OR "no inhibition")

"Amaranthus retroflexus" "postemergence" "150 g" inhibition
"Amaranthus retroflexus" "1500" "fresh weight" herbicidal
"natural compounds" phytotoxicity "solvent control" dose response
```

Follow primary papers' references and supplementary tables. Search names/synonyms and original compound numbers, not only ChEMBL IDs. Use legal publisher/library/repository access. Time-box an inaccessible lead after two retrieval routes and an initial roughly 45-minute search, log the gap, then continue elsewhere.

### Leads already available, with limits

- **Kobayashi & Ito 1998**, [DOI 10.3719/weed.43.341](https://doi.org/10.3719/weed.43.341): recovered methods/results underpin the five author-category positives. “Relatively active” compounds are not accepted negatives. Review any broader assay data only under a written suitable policy; do not make “not very active” mean inactive.
- **Li 2006**, [DOI 10.1021/jf061976j](https://doi.org/10.1021/jf061976j), and **He 2011**, [DOI 10.1021/jf104247w](https://doi.org/10.1021/jf104247w): good starting points for source-specific methods and full series, but their current scaffold families are sparse. Searching related literature must not quietly change the accepted dose/endpoint policy.
- **Okamoto 1991**, [DOI 10.1271/bbb1961.55.2737](https://doi.org/10.1271/bbb1961.55.2737): original ordinal 0–5 injury values, not measured 80%/100% inhibition; replication is not reported in the inspected source. Existing four positives do not provide negatives.
- **Characterization and phytotoxicity of ophiobolins produced by Bipolaris setariae**, 2021, [DOI 10.47371/mycosci.2020.11.002](https://doi.org/10.47371/mycosci.2020.11.002): a source lead for green-foxtail detached-leaf lesion responses, including weak/no-lesion conditions. Punctured and intact leaves, species, doses and lesion endpoints form a **separate proposed policy**. These congeners may add little scaffold diversity and must not become Amaranthus negatives by transfer.
- The 200-compound dietary identity list is not a negative-label dataset. Food occurrence, benignity assertions and lack of activity reports do not establish tested plant low response.

## 4. Extract evidence before assigning labels

Use one record per study × compound/form × treatment × species × endpoint × assessment time. Repeated doses, sites, formulations or leaf treatments need separate records, even if the final label will later be summarized.

Capture the following:

| Category | Fields to record |
|---|---|
| Identity | Existing/new compound ID; source compound number/name; exact drawing or machine-readable structure; stereo/regiochemistry; free acid/salt/ester; purity; isolate versus purchased reagent versus formulation; database key only as a cross-check |
| Natural occurrence | Primary organism/tissue or culture, extraction/isolation/characterization evidence, exact structure/form link, source location; distinguish occurrence from exclusive biosynthetic attribution |
| Assay | Publication/assay ID, organism/cultivar, stage, substrate/medium, pre/post emergence or detached leaf, treatment/application and dose basis, exposure/assessment duration, endpoint |
| Controls and replication | Untreated and vehicle/formulation blank controls, control response, biological versus technical replication, randomization, sample counts and experimental unit |
| Response | Original value, unit, qualifier, ordinal grade/band, uncertainty, statistical method, dose-response pattern, conflicting results and source footnotes |
| Provenance | DOI/URL, source file/hash, page/table/figure/row/treatment, extraction/checker/date, primary versus cited observation and access limitations |

In the 1998 solution assay, three dishes of 20 seeds means three dish-level replicates, not automatically 60 independent replicates; soil assays have four cups of five seeds. Do not invent exact effect sizes from undigitized figures. If digitization becomes necessary, preserve the image, method, uncertainty and explicit distinction from tabulated values.

For a compound seen in multiple studies, retain every observation and the conflicts. Do not vote across incompatible assay policies to create one universal label.

## 5. Accepted rules and rules that must not be invented

| Policy | Supported classification and scope |
|---|---|
| `HUMAN-K1998-TWO-SPECIES-VERY-ACTIVE-1MM-v1` | Authors' very-active reagent category at 1 mM, lettuce day six and millet day four. No accepted low-response boundary; other categories remain unknown. Final DMSO/vehicle uncertainty is retained. |
| `HUMAN-LI2006-AR-150G-POST-BOUNDS-v0.1` | Amaranthus retroflexus, two-leaf postemergence foliar application, 150 g a.i./ha, day-15 visual response. Author `>80%` band active, `<50%` bounded low response; intermediate/missing/conflicting unknown. Keep strict bounds, not exact values. |
| `HUMAN-HE2011-AR-1500G-POST-BANDS-v0.1` | Amaranthus retroflexus, 2–3-leaf foliar application, 1,500 g a.i./ha, 20-day fresh-weight response. Grades A/B active; D bounded low response; C unknown. A=90–100, B=75–89, C=50–74, D≤50; shared boundary wording does not make C negative. |
| `HUMAN-OKAMOTO-1991-UPLAND-10G-AI-PER-A-v0.1` | Amaranthus lividus pre-emergence upland pot, 10 g a.i./are, two weeks, ordinal 0–5 response. Grades 4/5 active, 0/1 bounded low response, 2/3 unknown under the adopted policy; currently only four positives are available. Preserve unreported replication as a limitation. |

`inactive` is the existing machine-schema word for a **bounded, policy-specific low response**. It does not mean no herbicidal activity at every dose or in every plant.

For a new policy, write species/stage, chemical/tested form, dose and basis, exposure mode/duration, endpoint, control/quality requirements, positive rule, low-response rule, gray-zone/conflict handling and uncertainty treatment **before evaluating candidate outcomes or model scores**. A qualified scientific teammate should review that definition. Quantitative “no important effect” claims need an appropriate prespecified margin and uncertainty/power reasoning; failure to reject a null difference is not equivalence.

A different policy can support a useful descriptive cohort now. It cannot be mixed with the four existing policies merely to fill sample size. If a policy is revised, version it and re-adjudicate affected old observations; do not carry labels over automatically.

## 6. Resolve specific identity gaps as a separate task

| Source | Existing gap | Evidence needed |
|---|---|---|
| Li **7b / CHEMBL2253255** | Paper N-allyl versus frozen N-cyclopropyl constitutional isomer | Original scheme/photo and spectra/SI; exact source result row; qualified structural review. Same formula is not identity. |
| Li **7w / CHEMBL2253236** | Source substituent row unreadable in prior text extraction | Legible original structure/table/SI and complete source-to-canonical comparison |
| Li **KIH-6127 / CHEMBL2253237** | Connectivity agreement but geometry unresolved | Tested stereoisomer/form and original source specification; connectivity-only match is insufficient |

Preserve old structures and held observations. If a correction is established, return a **new versioned mapping/structure decision**, rationale, source hash and reviewer, and identify every affected measurement. Do not edit the original frozen SMILES or transfer activity to a hypothetical isomer. The current global hold validator enforces 7b; the two other Li gaps also remain excluded by the adoption ledger and require source-specific handling.

These three fixes alone will not solve scaffold diversity. Work on genuinely new chemical families in parallel.

## 7. Turn evidence into a model-ready handback

Create `work/<initials>-<date>-<run>/biology/` with:

| Output | Required content |
|---|---|
| `literature_screen` | Query/date, source/title/DOI, access state, tested compounds, eligible endpoint/policy, available controls/null results, scaffold novelty and include/exclude/unresolved reason |
| `compound_identity` | IDs, exact source structure/form/stereo, SMILES/InChIKey, source locator, identity/origin decision, rationale and reviewer/date |
| `study_observations` | All fields from section 4, stable observation IDs and original responses; one row per condition |
| `policy_decisions` | Policy ID/version, complete definition, scientific rationale, accepted/proposed status and reviewer/date |
| `proposed_labels_<policy>.csv` | Exactly seven columns below, one unique compound row per cohort, supported references/context, unknowns preserved |
| `scaffold_support` | Deduplicated eligible compounds, class counts, distinct class-bearing scaffolds, actual five-fold support status, exclusions/holds and publication diversity |
| `summary.md` | New usable evidence by policy, actual diversity gain, conflicts/unresolved leads, source access gaps and next source to inspect |

The seven-column interface is unchanged:

```text
compound_id,natural_origin,origin_reference,herbicidal_activity,activity_reference,activity_context,activity_policy
```

Allowed origin values are `natural`, `synthetic`, `unknown`; allowed activity values are `active`, `inactive`, `unknown`. Known origin needs its reference. Known activity needs a reference, explicit assay context and a shared policy ID. Natural occurrence and activity are independent. Documented commercial synthesis does not automatically establish absence of natural occurrence; the existing manufacturing-comparator group is not a blanket synthetic-origin label.

Keep evidence and approval history in companion tables. Duplicate/orphan IDs, known conflicts on the same canonical structure and mixed known activity policies must fail validation. Provide source observations even when a compound-level decision remains unknown.

### Check support before fitting

A model cohort needs at least five compounds and five scaffold groups **in each class**, plus both classes in every actual train/test split. This is a minimum gate, not a sufficient sample size for strong generalization. Murcko scaffolds group related structures; all acyclic molecules use one `ACYCLIC` group in the current implementation. Additional stereoisomers or substituted analogues may not add independent cores.

With the full checkout, the following optional preflight computes chemistry and checks support **without fitting a model**. Replace both paths. Each compound input row needs a unique `compound_id` and `smiles`; validate source identity before this computational check.

```bash
uv run --project analysis --locked python - <<'PY'
import csv, sys
import numpy as np
sys.path.insert(0, 'analysis')
from labels import attach_labels
from structure import structure_features
from ablations import _cohort, _splits
from verification_release import reject_held_activity

def read(path):
    with open(path, newline='') as handle:
        return list(csv.DictReader(handle))

compounds = read('YOUR_WORK_DIRECTORY/compounds.csv')
labels = read('YOUR_WORK_DIRECTORY/proposed_labels_ONE_POLICY.csv')
reject_held_activity(labels, {'CHEMBL2253255'})
# Also preserve other unresolved source-specific holds recorded in companion decisions.
features = [{'compound_id': r['compound_id'], **structure_features(r['smiles'])}
            for r in compounds]
rows = _cohort(attach_labels(features, labels), 'activity_target')
y = np.array([r['activity_target'] for r in rows], dtype=int)
groups = np.array([r['scaffold'] for r in rows])
for value in (0, 1):
    print('class', value, 'compounds', int(np.sum(y == value)),
          'scaffolds', len(set(groups[y == value])))
status, splits = _splits(np.zeros((len(rows), 1)), y, groups, 5)
print('five-fold support:', status, 'folds:', len(splits))
PY
```

This checks the formula-eligible cohort used in matched diagnostics. Other representations can have different eligibility; report those differences. It does not certify labels or resolve held identities. `structure_models.evaluate` is **not** a read-only support checker when support succeeds: it fits models.

The old `validate_activity_proposal.py` is useful only for the complete original 154-ID cohort and its frozen hold audit; it rejects extended cohorts. New/expanded cohorts need generic schema/conflict/hold checks and tested integration. The current adoption builder also requires exact original worksheet coverage; adding rows to that workbook is not a general new-compound importer.

### When a new model is justified

Once scientific decisions are documented and class/scaffold gates pass, an integrating analyst can run the existing structural workflow on one policy in a fresh directory:

```bash
uv run --project analysis --locked python analysis/screen.py \
  --compounds YOUR_WORK_DIRECTORY/compounds.csv \
  --labels YOUR_WORK_DIRECTORY/reviewed_labels_ONE_POLICY.csv \
  --output analysis/outputs/REPLACE_WITH_NEW_RUN_DIRECTORY
```

Validate holds and scientific acceptance first; code accepting citation text does not certify the science. Preserve the held-out evaluation, fold-local preprocessing and frozen representation settings. Report F1/precision/recall, balanced accuracy, AUROC, confusion counts, baseline, scaffold/publication composition and exclusions. Coefficients must have their input scale and target direction. OOB importance variability is not a formal significance test.

Do not lower the fold count, switch to random splits, pick thresholds/features on held-out results or merge assays simply to make a model run. If several compatible publications contribute, assess publication-held-out or external validation as well; a publication-specific chemical series can create source bias. No candidate score or high cohort-classification F1 substitutes for independent activity evidence.

## 8. Completion criteria and decisions that can wait

A useful first return contains a justified target policy, an auditable screened-literature list, exact source-linked observations and identities, proposed decisions with unknowns intact, and actual scaffold-diversity gains. It need not contain a fitted model. Have a qualified teammate check pivotal identity, negative-label and policy decisions; record the review rather than seeking another blanket approval from the project owner.

Leave access gaps and unresolved conflicts explicit and continue independent work. Broader chemical imports, more classifier families, binding/protein analyses and formal censored-data models are deferred until they answer a supported question. Do not overwrite frozen evidence, edit the unchanged `GOALS.md`, commit ignored research documents, push or publish results as part of this assignment.
