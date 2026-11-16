# Project glossary

Maintained orientation, reviewed 2026-11-02. Exact data/label schemas belong to the
tracked pipeline and analysis contracts.

| Term | Meaning in this repository |
| --- | --- |
| ACCase | Acetyl-CoA carboxylase; HRAC Group 1 target in the source tables |
| ALS / AHAS | Acetolactate synthase / acetohydroxyacid synthase; HRAC Group 2 target |
| Allelochemical | Chemical influencing another organism; candidate relevance does not establish efficacy or safety |
| BMD / BMDL | Benchmark dose / its lower confidence bound; model-derived points of departure, not stored TEST predictions |
| CASRN | Chemical Abstracts Service Registry Number |
| CID | PubChem Compound Identifier |
| DTXSID | EPA DSSTox Substance Identifier |
| LD50 / LC50 | Dose / concentration associated with 50% lethality under the stated test conditions |
| EC50 | Concentration associated with the specified 50% effect; interpretation requires the assay/response definition |
| NOAEL / LOAEL | No observed / lowest observed adverse effect level |
| NOEC / NOAEC | No observed effect / adverse effect concentration; not interchangeable with dose-based endpoints |
| HRAC | Herbicide Resistance Action Committee; source groupings describe mode/site of action |
| InChIKey | Hashed chemical identity representation; useful for matching, never an ordinal model predictor |
| SMILES | Text representation of chemical structure |
| QSAR | Quantitative structure–activity relationship; meaningful only for a declared biological target/endpoint and validated domain |
| Selection target | Diagnostic label distinguishing curated input groups; not independently reviewed activity or origin |
| Reviewed activity | Evidence-based activity label under a cited, explicit biological policy |
| Natural origin | Separately reviewed occurrence/provenance label; not synonymous with selection group or safety |
| Coverage / availability | Whether saved evidence passes the configured extraction/eligibility rules, with full selected denominators |
| Scaffold-held-out | Structural groups remain in separate evaluation folds; training preprocessing stays within the training partition |
| Manifest | Record of exact inputs/code/environment/settings/products and hashes, with scope depending on the workflow |
| Binding / functional inhibition | Related but distinct experimental evidence; neither should be inferred from whole-plant activity alone |
| Hazard / risk | Toxicity under specified conditions / potential harm considering exposure and other context |

See [evidence conventions](evidence-and-identities.md),
[structural interpretation](structure-and-activity.md) and
[binding evidence](binding-and-targets.md) for the relevant distinctions.
