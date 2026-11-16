# Project handoff

**As of 11 November 2026.** Audience: research colleagues continuing the evidence review and analysis. Read this once, then use the [toxicity guide](02_TOXICITY_RESEARCH_GUIDE.md) or [biological evidence guide](03_BIOLOGICAL_EVIDENCE_GUIDE.md).

## 1. The question and the current answer

The project seeks natural compounds with herbicidal properties, describes the chemistry that distinguishes them from conventional herbicides, and compares toxicological evidence. A broader objective concerns known natural-product–protein interactions; a validated binding workflow has not been completed and is outside these two assignments.

The intended biological comparison has three groups: natural active, natural low-response under a defined assay policy, and conventional-herbicide comparators. We can describe reviewed natural active examples now. We cannot yet make a validated three-class activity classifier or a general “natural is safer” conclusion.

Keep five concepts separate:

| Concept | What supports it | What it does not establish |
|---|---|---|
| Chemical identity | Exact source-to-structure/form mapping | Natural occurrence, efficacy or safety |
| Natural occurrence | Primary isolation/characterization evidence for the same structure | Manufacturing route or safety |
| Plant activity | A response under a stated species/dose/duration/endpoint policy | Dose-invariant or universal herbicidal activity |
| Toxicity evidence | Comparable organism/exposure/endpoint measurements | Risk without exposure information |
| Cohort classification | A model distinguishing the selected groups | Biological activity, protein binding or natural origin as a universal property |

Rough work-completion estimates are **Track 1 75%, Track 2 80%, overall three-group comparison 55%**. These are planning judgments, not confidence levels or formal milestone scores.

## 2. What has been completed

### Data pipeline and descriptive analysis

- Maintained acquisition/processing workflows for cached PubChem, EPA and bounded ChEMBL evidence, with identity decisions, raw snapshots, normalization, qualifiers, eligibility reasons and provenance.
- A prepared purposive selection of **176 compounds: 60 selected herbicides and 116 selected natural products**, derived from 178 original input rows. Selection membership is not independently reviewed origin/activity truth.
- Seven endpoint types and eight comparison policies for evidence availability, including separate broad-fish/trout LC50 policies. Missing assessment, evidence availability, measured doses, BMD/BMDL and stored predictions remain distinct. Earlier random-split/availability classifiers are historical context, not the current structural performance claim.
- Molecular distributions and exploratory comparisons. RDKit computes formula features, 11 descriptors, radius-2 2,048-bit chiral Morgan fingerprints and Murcko scaffolds. Formula representation has 27 features. Mixtures/salts may be model-ineligible without invalidating a separately approved whole-form identity.

### Structural models and interpretation

The current historical matched cohort has **171 eligible unique structures: 55 selected herbicides and 116 selected natural products**. Five-fold scaffold grouping prevents a scaffold crossing a training/test boundary. The baseline fits imputation, constant removal, scaling, 95%-variance PCA and L2 logistic regression within training folds. Raw-formula logistic retains standardized original columns; raw Morgan logistic/forest use unscaled bits without PCA.

Completed diagnostics include fixed and nested regularization experiments, feature-block combinations, halogen removal/recomputed composition, shuffled-label controls, scaffold-fold sensitivity, individual held-out errors, standardized coefficients, held-out permutation and forest tree-specific OOB permutation. Nested C selection uses inner scaffold folds, never outer-test outcomes.

| Cohort/target | Formula raw F1 | Formula PCA F1 | Raw Morgan logistic F1 | Raw Morgan forest F1 |
|---|---:|---:|---:|---:|
| Historical 171-compound selection membership | 0.9143 | 0.8972 | 0.8687 | 0.8687 |
| New 30-compound reviewed-cohort membership | 0.8421 | 0.8421 | 0.6667 | 0.6000 |

The **new** contrast has **19 approved natural-occurrence examples versus 11 documented commercial-herbicide manufacturing comparators**. The latter are target 1. It is still a purposive cohort classifier: natural occurrence and commercial manufacture can coexist. Its scores are not improvements/deteriorations relative to the different 171-compound task. Halogen-only/presence F1 is 0.9000 on the new cohort.

Separate full-cohort forest OOB F1 values are **0.9038 historically and 0.9000 for the new cohort**. OOB omits a row per tree, not its structural family; it is weaker separation than scaffold holdout. Ten-repeat OOB importance SD is descriptive, not a p-value or formal significance test. Coefficients and importance are model associations, not causal chemical effects.

Saved reports are included under [reference_inputs/models](reference_inputs/README.md). No fitted estimator objects are included in this compact package.

### Human-reviewed biological evidence

The second-pass workbook and the owner's explicit human-review declaration were adopted into new versioned datasets. We have **19 approved natural-occurrence labels**: 15 literature compounds and four earlier ophiobolins. The second pass contains **119 study/treatment observations**; original packets had 81. Human approval is recorded separately from preserved historical AI-only/pending wording.

There are **80 activity decisions across four separate policies**, not 80 interchangeable training examples:

| Accepted policy | Active | Bounded low-response (`inactive` in schema) | Active-bearing scaffolds | Low-response-bearing scaffolds |
|---|---:|---:|---:|---:|
| K1998 two-species very-active category, 1 mM | 5 | 0 | 3 | 0 |
| Okamoto 1991 upland ordinal assay | 4 | 0 | 1 | 0 |
| Li 2006 postemergence, 150 g a.i./ha | 11 | 10 | 3 | 2 |
| He 2011 postemergence, 1,500 g a.i./ha | 29 | 21 | 2 | 2 |

**No activity classifier passes the existing five-fold support requirements.** The problem now is independent chemistry and compatible negative evidence, not an uncompleted blanket approval.

The five approved K1998 natural active compounds are 3-phenylpropionic acid, 2-hydroxyphenylacetic acid, coumarin, juglone and trans-cinnamic acid. This means the authors' very-active reagent category at 1 mM, with lettuce at day six and millet at day four. It is not an exact quantitative vehicle-controlled efficacy estimate. Their medians are MW 150.177 g/mol, calculated logP 1.7038 and TPSA 37.3 Å², versus 279.1135, 2.90424 and 62.73 for 58 supported selected-herbicide comparators. Fourteen other approved natural compounds remain activity-unknown under K1998; the natural low-response group is empty.

Important corrections already made:

- Formulated-product outcomes in 2020 are not isolated-ingredient activity labels.
- Nonsignificant 2024 field differences do not establish equivalence/low response. Site, rate and formulation effects remain separate.
- Sarmentine activity remains unknown because methods/table concentrations disagree, 10 versus 20 mg/mL; a product/active-ingredient explanation is plausible but unconfirmed.
- Retracted Walker 2003 evidence is excluded. Independent Farag 2022 evidence supports trans-cinnamic-acid occurrence. Other independent sources replace the anomalous salicylic-acid isolation citation and support free pelargonic acid.
- Three Li source gaps persist: **7b / CHEMBL2253255** constitutional isomer; **7w / CHEMBL2253236** unreadable source substituent; **KIH-6127 / CHEMBL2253237** unresolved geometry. Their affected observations are not rescued by general approval.

A separate 200-compound dietary-comparator identity audit and earlier 40-candidate triage exist. Dietary use/benignity assertions do not provide tested plant inactivity. These are leads, not a ready negative class.

### EPA rat oral LD50 comparison

From 5,814 cached hazard rows across 88 source chemicals, the bounded policy retained **43 exact and 25 censored acute rat oral LD50 observations**. There are **34 exact compound medians**, plus **15 censored-only compounds**. Historical pooled tertile cutoffs remain **1,080 and 3,400 mg/kg**, with ties retained. “Low” means low LD50, hence greater acute lethal toxicity; these are descriptive bins, not regulatory risk categories.

Reviewed natural overlaps are coumarin (K1998 active; exact median 520 mg/kg), salicylic acid (activity unknown; 891), benzoic acid (activity unknown; 2,565), and trans-cinnamic acid (K1998 active; censored-only). One exact active natural example cannot support a safety ranking. Bounds retain compatible observation bins; they are not imputed points or compound-median labels. Sensitivity subsets and documentation gaps are explicit.

### ECOTOX expansion and explicit identity approval

The official frozen September 15, 2026 archive contains 18,551 chemicals, 725,635 tests and 1,250,611 results. It was inventoried, dictionary decoded and bounded to **104 source chemicals**, prioritizing nine literature overlaps. All 104 mappings are now explicitly human-approved. **103 compounds have results; Acacetin has zero results**, retained as assessed-zero coverage.

The complete selected export has **49,760 tests, 79,171 native results and 79,302 concentration slots**. A result can have multiple slots; slots are not independent experiments. Identity-only reimport preserved all scientific fields and source IDs. There are 3,267 complete bounded parses and 76,035 review slots; unsupported information remains visible.

Canonical core-policy exports now contain:

| Policy | Records | Compounds | Measured/unmeasured | Additional reported-context subset |
|---|---:|---:|---|---:|
| Trout mortality LC50, 96 h observation | 28 | 7 | 6 / 22 | 0 |
| Daphnia immobilization EC50, 48 h observation | 13 | 11 | 1 / 12 | 1 |

There are **39 exact values and two lower bounds**. Observation duration is not automatically exposure duration. The additional subset requires reported exposure type/control type and matching exposure/observation duration; it does not itself establish study quality. Nine reviewed-natural records fail this additional check. pH, temperature, age, primary-versus-secondary reporting and other conditions still need investigation.

There are **16 rat LD50 records in a context-review queue**, none added to the historical baseline. The broader overlap queue has **18,992 candidate pairs**, not established duplicates. No same-observation decisions were adopted. Newly prepared handoff triage finds **26 pairs touching the pending rat records, zero touching the currently retained 68 EPA observations, and zero touching the 41 admitted aquatic records**. That is a queue-intersection result, not proof that missing-reference or within-source duplicates do not exist.

## 3. What to do next and who owns it

| Lead | Immediate assignment | First useful return |
|---|---|---|
| Toxicity researcher | Recover source protocols for the 41 aquatic/16 rat records, prioritize the three natural-overlap aquatic papers and seven rat references | Source-linked context overlays, rat eligibility proposals, 26-pair adjudication log |
| Biological researcher | Find negative/low-response results across new independent scaffolds under compatible policies; resolve the three specific Li gaps where feasible | Study-level evidence, exact structures, policy-separated proposed labels and scaffold-support report |
| Integrating analyst | Validate returned overlays/labels, implement any missing ingestion support, rerun only affected analyses in fresh directories | Versioned results, tests, figures and updated notebook |

Do not spend the next work period changing classifier families, expanding all databases indiscriminately or relabeling every unknown. Source context and independent negative chemistry are the limiting inputs.

## 4. Authoritative files and operating rules

The compact [reference inputs](reference_inputs/README.md) are sufficient to start research. Current full-repository bundles, relative to the repository root, are:

| Purpose | Current bundle under `analysis/outputs/` |
|---|---|
| Adopted biology and policy labels | `human-review-adopted-2026-11-11-final/` |
| Reviewed biological descriptions and LD50 annotations | `human-reviewed-progress-2026-11-11-complete/` |
| Historical selection models / new reviewed-cohort models | `weekly-models-2026-11-10/` / `reviewed-cohort-models-2026-11-11-final/` |
| Approved ECOTOX mappings | `ecotox-identities-approved-2026-11-11/` |
| Complete canonical ECOTOX results | `ecotox-selected-approved-2026-11-11/` |
| Refreshed overlap queue / sensitivity | `ecotox-approved-reconciliation-2026-11-11/` |
| Current aquatic comparison and rat queue | `ecotox-approved-comparison-2026-11-11-verified/` |
| Frozen rat baseline | `weekly-toxicity-2026-11-10/` |
| Historical 154-compound feature cohort / hold audit | `chembl-review-screen-2026-10-29-final/` / `verification-release-audit-2026-11-05-final/` |

The latest teaching notebook is `notes/notebooks/presentation_essentials.py`, with a same-name HTML copy. All 74 cells executed successfully at the checkpoint. Software verification was **248 analysis tests and 1,057 pipeline tests passed**; this is historical software verification, not independent biological validation.

Use adoption ledgers and accepted policy files for current decisions. Historical templates intentionally remain unknown. Files with `HUMAN-` names for M2020, T2024 and D2015 still have no known activity labels; a filename is not approval. Generic context text in unresolved records of the original `policies.json` is not an authoritative protocol for those studies.

Preserve stable compound IDs, source result/measurement IDs, raw values/units/qualifiers, page/table/treatment locators and review history. Never overwrite frozen inputs, labels, manifests or output directories. Some immutable native exports share storage; write separate overlays or real working copies. Keep work and documentation in ignored directories. Do not edit `notes/GOALS.md`, force-add `notes/`, push the local branch or publish this package without separate authorization.

## 5. Access, verification and independent work

No Python is needed for literature review. Work under `work/<initials>-<date>-<run>/` and follow the return schema in your guide. Every unresolved item needs a reason and the next evidence that would resolve it. Routine transcription, retrieval and within-policy proposals can proceed without the owner. A qualified teammate can review consequential decisions; record reviewer/date and the scope of the decision. New policies or resolved identity conflicts require explicit documented scientific review before label/model promotion.

For code work, use the authorized checkout at local branch `feat/weekly-research-pilots`, checkpoint `b771c87`, and keep pipeline/analysis locked environments separate. A clone alone lacks ignored caches and may lack these unpushed commits. Do not put credentials in a collaborator package.

Verify this portable package from its root using standard Python:

```python
import hashlib, json
from pathlib import Path
root = Path.cwd()
inventory = json.loads((root / "PACKAGE_INVENTORY.json").read_text())
for item in inventory["files"]:
    actual = hashlib.sha256((root / item["path"]).read_bytes()).hexdigest()
    assert actual == item["sha256"], item["path"]
print("Package hashes match")
```

This checks transferred bytes, not scientific correctness. Original manifests use absolute paths; retain them unchanged and map locations during verification rather than rewriting their provenance. The compact excerpts do not replace full caches for a complete rebuild.

Read the applicable research guide next. It specifies what can be completed directly and where a tested integration change is still needed.
