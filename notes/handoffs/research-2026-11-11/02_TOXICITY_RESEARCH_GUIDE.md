# Research guide A: comparable toxicity evidence

**Assignment:** turn source-linked but incompletely documented toxicity records into defensible study-level comparisons. Start with the [project handoff](01_PROJECT_HANDOFF.md). This guide can be followed from the portable package without the full repository; optional integration commands require the authorized checkout.

## 1. The deliverable and the order of work

Return a new working folder containing:

1. A source-acquisition log and saved permitted source files with hashes.
2. Context extraction and proposed eligibility records for all **41 aquatic observations**.
3. Context/eligibility records for all **16 rat LD50 cases**.
4. Decisions for the **26 priority overlap pairs**, or explicit unresolved reasons.
5. A brief results note listing supported additions, exclusions, unresolved items, exact/bounded counts and integration changes needed.

Begin with natural-overlap aquatic studies, then high-yield rat studies, then overlap adjudication while those papers are open. Do not start by manually reviewing all 18,992 candidate pairs.

A completed assignment may conclude that a value remains unusable. Do not convert missing exposure information into a guessed duration or approve an observation merely to increase coverage.

## 2. Your starting files

| File in `reference_inputs/toxicity/` | How to use it |
|---|---|
| [aquatic_observations.csv](reference_inputs/toxicity/aquatic_observations.csv) | All 41 identity-approved core-policy rows, locators, concentrations, qualifiers and context gaps |
| [policy_coverage.csv](reference_inputs/toxicity/policy_coverage.csv), [sensitivity.csv](reference_inputs/toxicity/sensitivity.csv) | 28 trout / 13 Daphnia; additional reported-context subset zero / one |
| [rat_ld50_review.csv](reference_inputs/toxicity/rat_ld50_review.csv) | Sixteen rat cases with raw units/value text, source reference and exclusion reasons |
| [ecotox_native_context_excerpt.json](reference_inputs/toxicity/ecotox_native_context_excerpt.json) | All 57 relevant native source records; decode their `test_json`, `result_json`, `reference_json`, `species_json` and `chemical_json` |
| [source_reference_index.json](reference_inputs/toxicity/source_reference_index.json) | Twenty publication leads with authors, year, title, DOI where present and counts |
| [rat_priority_overlap_pairs.json](reference_inputs/toxicity/rat_priority_overlap_pairs.json) | Twenty-six unchanged candidate pair records |
| [epa_rat_overlap_counterparts.json](reference_inputs/toxicity/epa_rat_overlap_counterparts.json) | Fourteen EPA records on the other side of those pairs, with raw context JSON |
| [retained_epa_observations.json](reference_inputs/toxicity/retained_epa_observations.json) | Existing 43 exact / 25 censored rat baseline observations |
| [historical_ld50_compounds.csv](reference_inputs/toxicity/historical_ld50_compounds.csv), [historical_censored_bins.csv](reference_inputs/toxicity/historical_censored_bins.csv) | Existing medians and bound-compatible bins; read-only reference |
| [approved_crosswalk.csv](reference_inputs/toxicity/approved_crosswalk.csv), [source_policy_coverage.csv](reference_inputs/toxicity/source_policy_coverage.csv) | Approved identity mapping and assessed zero-hit coverage; Acacetin has no results |

Native JSON strings preserve missing source values such as `NR` and `NC`. Their presence is not zero and does not mean a study was necessarily inadequate; the primary paper may contain information the database omitted.

The source-reference appendix below is copied from the frozen database, **not a new bibliographic or full-text verification**. Check that the retrieved publication and exact table/organism/treatment match the record. A paper may quote a value from an earlier study; trace that lineage rather than counting a secondary citation as a new experiment.

## 3. First assignment: recover aquatic context by publication

### First three papers

| ECOTOX reference | Why first | What to resolve |
|---|---|---|
| **990**, Marking 1970, juglone | Six trout records from the approved natural-active group | Actual exposure duration versus 96 h observation, controls, fish/test conditions, six distinct treatments and primary result cells |
| **19294**, Stroh et al. 1998, essential oils/carrier | One eugenol trout record | Exact ingredient/product versus carrier, dose basis, exposure duration, carrier controls, relevant salmonid species |
| **80404**, Kamaya et al. 2005, benzoic acids | Eight Daphnia rows, including approved-natural benzoic/salicylic acids | Actual 48 h exposure protocol, controls, immobilization endpoint, pH/medium and compound-specific table mappings |

Together these cover **15 of the 41 records**, including all nine approved-natural overlaps. Next inspect reference **12170** (11 fluridone records), **924** (five glyphosate records) and **4070** (one glyphosate record) to improve comparator context. Finish the remaining references in the appendix.

### Work through one paper completely

1. Locate the publisher/DOI record, library full text or legitimate author manuscript. Confirm author, year and title. Save the source or its stable link, retrieval date, access outcome and file SHA-256. Check for corrections/retractions and follow the measurement's original source if the paper is secondary.
2. Match the exact chemical and tested form, organism, table row, concentration slot and reported endpoint to each source result. The approved chemical mapping is already done; a new contradiction still must be logged rather than overwritten.
3. Extract the protocol once, then attach it to every applicable treatment using explicit IDs. Do not apply a fish protocol to a Daphnia result merely because both appear in one paper.
4. Resolve actual exposure duration independently of observation/assessment time. “LC50 at 96 h” alone is not a verified description of continuous 96 h exposure. Record static, renewal or flow-through conditions and renewal schedule where reported.
5. Extract concentration analysis: measured versus nominal/unmeasured, sampling times, chemical stability and active ingredient/product/acid-equivalent basis. Preserve original units and qualifiers before proposing conversions.
6. Record controls and study conditions: untreated and matched vehicle controls, control mortality/immobilization, vehicle composition, replication units, animal numbers, life stage/size, temperature, pH, water hardness and other medium details. “20 animals” is not necessarily 20 independent replicates.
7. Record the reported estimate and uncertainty: equality, inequality, interval/range, confidence interval, estimation method and any graphical-only result. `=` means an uncensored reported estimate, not zero statistical uncertainty.
8. Propose a disposition with a source locator and a second check for consequential mappings/conversions. Keep “not reported,” “not accessible,” “ambiguous” and “contradicts database” distinct.

### Comparison rules

Keep trout **mortality LC50** and Daphnia **immobilization EC50** separate. The frozen Daphnia code combination is effect `ITX`, measurement `IMBL`; `IMM` means immunological. Both may use mg/L, but they measure different organism/effect contexts.

Keep measured/unmeasured exposure, concentration basis, formulation, exposure type, medium and actual exposure duration in separate strata. Do not average across the six juglone records and call that one universally comparable toxicity value. pH, age and temperature may still matter even after these fields match. Any relaxation needs an explicit sensitivity scenario, not a silently pooled primary result.

For a lower bound such as `EC50 > x`, retain the bound. Do not substitute `x` into a median. A range is not an exact midpoint. Preserve distinct source result IDs even when numbers agree.

## 4. Second assignment: evaluate the 16 rat LD50 cases

Use this publication-level schedule:

| Ref. | Cases | Main question |
|---|---:|---|
| **119928**, Boyd & Carsky 1969 | 5 | Chlorpropham gavage with protein-diet conditions; confirm acute administration, dose denominator/form and experimental groups; `g/kg bdwt` currently unsupported |
| **101989**, Boyd & Krupa 1970 | 3 | Diuron gavage and protein-deficient diets; distinguish each diet group and acute versus repeated exposure |
| **73113**, Worth 1970 | 3 | Benefin/trifluralin chapter; locate original experimental table, substance/form, acute design and body-weight doses, including the censored result |
| **93388**, Gorzinski et al. 1987 | 2 | 2,4-D acute/pharmacokinetic/subchronic sections; identify which experiment supplied each value, route and acid-equivalent basis |
| **102055**, Hodge et al. 1967 | 1 | Diuron oral/metabolism paper; current row is dietary exposure and concentration basis `F`; establish what 3.4 g/kg means before treating normalized 3,400 mg/kg as an acute body-weight dose |
| **105511**, Elo et al. 1988 | 1 | Identify the original LD50 source and route/form in a cerebrovascular study; confirm whether the value is primary or cited |
| **35008**, Ambrose et al. 1972 | 1 | Propanil; inspect raw `+ 1384` against the original table and qualifier before proposing a numeric parse |

The queue lacks an explicit acute test-type code for every case. **Do not infer acute context from a title alone. Conversely, do not permanently reject a study just because the database says `NC`: full primary methods can establish context through a documented overlay.**

A proposed addition must support experimental **acute rat oral LD50**, exact tested identity/form, interpretable body-weight dose, original qualifier, appropriate treatment conditions and source location. Gavage/capsule, dietary concentration and repeated daily intake are not interchangeable.

Unit handling requires dimensional reasoning:

- `g/kg body weight` to `mg/kg body weight` has factor 1,000 after confirming both denominators and the chemical basis.
- `mg/kg diet` is concentration in feed, not dose per animal body weight. Do not convert it to a bolus dose by a unit label alone.
- Acid-equivalent and formulated-product doses require the tested form and conversion basis. Do not assume all `mg/kg` values describe the same material.
- An approximate sign, inequality or footnote must not be stripped to manufacture an exact value.

Propose **eligible**, **out of scope**, or **unresolved**, with all reasons. None of the 16 cases has been added automatically. The historical 34 medians and 1,080/3,400 mg/kg cutoffs stay frozen; an expanded cohort needs separately named summaries and any new tertiles.

## 5. Third assignment: study-overlap adjudication

The full queue has 18,992 pairs. The packaged 26-pair subset touches pending rat records; no current queue pair touches the retained 68 EPA baseline observations or 41 admitted aquatic records. This prioritization does not detect every possible duplicate: missing publication metadata, secondary citations and within-ECOTOX reporting remain blind spots.

For each priority pair, compare the primary publication lineage, exact compound/form, species/sex/strain, dose basis, route, duration, endpoint, diet/vehicle, actual experiment/table cell, response/qualifier and uncertainty. Automatic `match_count` is an agreement count, not confidence; false flags may reflect naming or unit differences. In particular, the current route-match heuristic is not an exhaustive gavage resolver.

Use these states:

| Decision | Required evidence |
|---|---|
| `same_observation` | Demonstrably the same original experiment/result reported twice; specify which ID to retain and why |
| `different_observation` | A documented difference establishing distinct experiments/conditions |
| `unresolved` | Available evidence cannot establish identity or difference |
| `unreviewed` | Not yet examined |

Same paper, same compound or same number alone is insufficient. Keep different diet groups, species, times, concentration slots and genuinely independent experiments separate. Do not collapse reporting chains through contradictory pair decisions; the importer rejects IDs simultaneously retained and dropped. Return a cluster-level explanation if the pair format cannot represent your proposed resolution.

The existing duplicate-decision importer expects these exact fields:

```text
pair_id,decision,retain_id,reviewer,review_date,decision_reference
```

Copy `pair_id` unchanged from the queue. A reviewed same/different decision needs reviewer, ISO date and supporting citation/locator. `retain_id` for `same_observation` must be one of that pair's IDs. Cross-source collapse requires approved identity; that requirement is now met for this cohort, but the observation decision still needs evidence.

## 6. What to write and how to hand it back

Create `work/<initials>-<date>-<run>/toxicity/` with the following logical files. Markdown tables, JSON or a plain spreadsheet are acceptable for research collection; include a machine-readable export when returning structured decisions.

| Output | Required fields/content |
|---|---|
| `sources` | source ID, author/year/title/DOI, retrieved URL, access state/date, local filename/hash, primary-versus-secondary lineage, correction/retraction result |
| `context_decisions` | snapshot/source result/measurement/test IDs; field being reviewed; original value/unit; proposed value/unit; status; source hash; page/table/row/treatment; rationale; extractor and checker/date |
| `rat_eligibility` | measurement ID; primary study; acute administration and observation times; species/sex/strain; route; chemical/dose basis; raw and proposed normalized value/qualifier/unit; eligible/out-of-scope/unresolved; reasons and locator |
| `duplicate_decisions` | Exact six importer columns above, plus optional companion evidence notes |
| `summary.md` | records reviewed, supported additions, unresolved counts, changes in coverage under each context rule, files changed, integration needs and highest-value remaining source |

Suggested statuses for context fields: `verified_from_primary_source`, `not_reported`, `access_gap`, `ambiguous`, `contradiction`. Record one coherent field decision per stable key. For test-level facts spanning several results, list all affected IDs and reject inconsistent overlays rather than using “last edit wins.”

Example structure, with placeholders rather than asserted values:

```json
{
  "measurement_id": "COPY_EXISTING_ID",
  "field": "exposure_duration",
  "original": {"value": null, "unit": null},
  "proposed": {"value": null, "unit": null},
  "status": "not_reported",
  "source_file_sha256": "SOURCE_HASH",
  "source_locator": "methods page / table / treatment",
  "rationale": "What was checked and why this remains unresolved",
  "reviewer": "REVIEWER",
  "review_date": "YYYY-MM-DD"
}
```

### Existing commands versus missing integration

Research overlays are **not** automatically consumed by the current importer. Do not edit native `test_json`, raw result values or frozen dictionaries to make a row pass. A tested overlay reader and a new versioned context/eligibility analysis are needed before recovered information affects admitted measurements. It must preserve raw fields, carry source/review provenance, expose contradictions, and separate original from source-adjudicated eligibility.

With the full checkout, the existing EPA duplicate sensitivity can consume reviewed pair decisions:

```bash
uv run --project analysis --locked python analysis/expansion_toxicity.py \
  --baseline analysis/outputs/weekly-toxicity-2026-11-10 \
  --ecotox analysis/outputs/ecotox-selected-approved-2026-11-11 \
  --crosswalk analysis/outputs/ecotox-identities-approved-2026-11-11/approved_crosswalk.csv \
  --decisions YOUR_WORK_DIRECTORY/duplicate_decisions.csv \
  --output analysis/outputs/REPLACE_WITH_NEW_RUN_DIRECTORY
```

Replace both placeholder paths; output must not already exist. This command does **not** ingest new rat observations or source-context overlays.

There is also an integration gap for aquatic duplicate decisions: `expansion_toxicity.py` computes exclusions from the supplied decisions but writes the original candidate states into its queue export; `ecotox_comparison.py` reads queue states and has no direct decisions argument. A new reconciliation run alone is not proof that aquatic reviewed exclusions propagated. The integrating analyst must preserve/adopt explicit decisions and test end-to-end removal before claiming post-adjudication aquatic summaries. Do not repair this by editing a frozen queue.

### Completion and stop rules

A useful complete first pass has 41 aquatic context records, 16 rat dispositions and 26 pair dispositions, each verified or explicitly unresolved with locators/access logs. Ask a qualified teammate to check consequential conversions, source mappings and same-observation decisions. Escalate scientific contradictions through the written record, not silent edits.

Time-box unavailable papers after two legitimate retrieval routes and an initial approximately 45-minute search; log the exact missing source and move to another paper. Do not bypass access controls or contact authors on someone else's behalf without authorization. No new endpoint pooling, imputation, label assignment, model training, push or publication follows from completing this research log.

## 7. Publication appendix

The following references and counts are extracted from the frozen native records supplied with this package. Full-text verification is your assignment. Rows whose titles mention another organism may contain comparative or cited values; verify the actual target experiment and lineage.

| ECOTOX ref. | Citation / retrieval lead | Aquatic / rat records |
|---|---|---|
| 101989 | Boyd,E.M., and V. Krupa (1970). **Protein-Deficient Diet and Diuron Toxicity**. J. Agric. Food Chem.18(6): 1104-1107 [DOI](https://doi.org/10.1021/jf60172a015) | 0 / 3 |
| 102055 | Hodge,H.C., W.L. Downs, B.S. Panner, D.W. Smith, E.A. Maynard, J.W.,Jr. Clayton, and R.C. Rhodes (1967). **Oral Toxicity and Metabolism of Diuron (N-(3,4-Dichlorophenyl)-N',N'-Dimethylurea) in Rats and Dogs**. Food Cosmet. Toxicol.5(4): 513-531 [DOI](https://doi.org/10.1016/S0015-6264%2867%2983153-5) | 0 / 1 |
| 105511 | Elo,H.A., H. Hervonen, and P. Ylitalo (1988). **Comparative Study on Cerebrovascular Injuries by Three Chlorophenoxyacetic Acids (2,4-D, 2,4,5'-T and MCPA)**. Comp. Biochem. Physiol. C Comp. Pharmacol.90(1): 65-68 [DOI](https://doi.org/10.1016/0742-8413%2888%2990098-9) | 0 / 1 |
| 106981 | Mendes,C.D., J.L. Pereira, and F. Goncalves (2007). **Acute and Chronic Effects of Stam Novel Flo (Commercial Solution) and Its Active Ingredient Propanil in Daphnia magna**. Fresenius Environ. Bull.16(5): 537-542 No DOI in the frozen record; search exact title/author/year. | 1 / 0 |
| 108323 | Palma,P., V.L. Palma, R.M. Fernandes, A.M.V.M. Soares, and I.R. Barbosa (2008). **Acute Toxicity of Atrazine, Endosulfan Sulphate and Chlorpyrifos to Vibrio fischeri, Thamnocephalus platyurus and Daphnia magna, Relative to Their Concentrations in Surface Waters from the Alentejo Region of Portugal**. Bull. Environ. Contam. Toxicol.81(5): 485-489 [DOI](https://doi.org/10.1007/s00128-008-9517-3) | 1 / 0 |
| 11504 | Alexander,H.C., F.M. Gersich, and M.A. Mayes (1985). **Acute Toxicity of Four Phenoxy Herbicides to Aquatic Organisms**. Bull. Environ. Contam. Toxicol.35(3): 314-321 [DOI](https://doi.org/10.1007/BF01636516) | 1 / 0 |
| 119928 | Boyd,E.M., and E. Carsky (1969). **The Acute Oral Toxicity of the Herbicide Chlorpropham in Albino Rats.  Effect of Diets Containing Varying Amounts of Protein**. Arch. Environ. Health19(5): 621-627 [DOI](https://doi.org/10.1080/00039896.1969.10666900) | 0 / 5 |
| 12170 | Hamelink,J.L., D.R. Buckler, F.L. Mayer, D.U. Palawski, and H.O. Sanders (1986). **Toxicity of Fluridone to Aquatic Invertebrates and Fish**. Environ. Toxicol. Chem.5(1): 87-94 [DOI](https://doi.org/10.1002/etc.5620050112) | 11 / 0 |
| 13154 | Marchini,S., L. Passerini, D. Cesareo, and M.L. Tosato (1988). **Herbicidal Triazines: Acute Toxicity on Daphnia, Fish, and Plants and Analysis of its Relationships with Structural Factors**. Ecotoxicol. Environ. Saf.16(2): 148-157 [DOI](https://doi.org/10.1016/0147-6513%2888%2990029-2) | 2 / 0 |
| 167254 | Pereira,J.L., C.D. Mendes, and F. Goncalves (2009). **Acute and Chronic Effects of a Mixture of Formulated Pesticides and Its Corresponding Active Ingredients in Daphnia magna**. Fresenius Environ. Bull.18(7b): 1281-1288 No DOI in the frozen record; search exact title/author/year. | 1 / 0 |
| 18805 | Howe,G.E., R. Gillis, and R.C. Mowbray (1998). **Effect of Chemical Synergy and Larval Stage on the Toxicity of Atrazine and Alachlor to Amphibian Larvae**. Environ. Toxicol. Chem.17(3): 519-525 [DOI](https://doi.org/10.1002/etc.5620170324) | 1 / 0 |
| 19294 | Stroh,J., M.T. Wan, M.B. Isman, and D.J. Moul (1998). **Evaluation of the Acute Toxicity to Juvenile Pacific Coho Salmon and Rainbow Trout of Some Plant Essential Oils, a Formulated Product, and the Carrier**. Bull. Environ. Contam. Toxicol.60(6): 923-930 [DOI](https://doi.org/10.1007/s001289900716) | 1 / 0 |
| 35008 | Ambrose,A.M., P.S. Larson, J.F. Borzelleca, and G.R.,Jr. Hennigar (1972). **Toxicologic Studies on 3',4'-Dichloropropionanilide**. Toxicol. Appl. Pharmacol.23:650-659 [DOI](https://doi.org/10.1016/0041-008X%2872%2990106-8) | 0 / 1 |
| 4070 | Anton,F.A., E. Laborda, and M. De Ariz (1994). **Acute Toxicity of the Herbicide Glyphosate to Fish**. Chemosphere28(4): 745-753 [DOI](https://doi.org/10.1016/0045-6535%2894%2990228-3) | 1 / 0 |
| 73113 | Worth,H.M. (1970). **The Toxicologic Evaluation of Benefin and Trifluralin**. In: W.B.Deichmann, et.al.(Eds.), Pesticides Symposia.  Inter-American Conferences on Toxicology and Occupational Medicine, University of Miami, Miami, FL:263-267 No DOI in the frozen record; search exact title/author/year. | 0 / 3 |
| 80404 | Kamaya,Y., Y. Fukaya, and K. Suzuki (2005). **Acute Toxicity of Benzoic Acids to the Crustacean Daphnia magna**. Chemosphere59(2): 255-261 [DOI](https://doi.org/10.1016/j.chemosphere.2004.11.003) | 8 / 0 |
| 89626 | Wan,M.T., C. Buday, G. Schroeder, J. Kuo, and J. Pasternak (2006). **Toxicity to Daphnia magna, Hyalella azteca, Oncorhynchus kisutch, Oncorhynchus mykiss, Oncorhynchus tshawytscha, and Rana catesbeiana of Atrazine, Metolachlor, Simazine, and Their Formulated Products**. Bull. Environ. Contam. Toxicol.76(1): 52-58 [DOI](https://doi.org/10.1007/s00128-005-0888-4) | 2 / 0 |
| 924 | Wan,W.T., R.G. Watts, and D.J. Moul (1989). **Effects of Different Dilution Water Types on the Acute Toxicity to Juvenile Pacific Salmonids and Rainbow Trout of Glyphosate and Its Formulated Products**. Bull. Environ. Contam. Toxicol.43(3): 378-385 [DOI](https://doi.org/10.1007/BF01701872) | 5 / 0 |
| 93388 | Gorzinski,S.J., R.J. Kociba, R.A. Campbell, F.A. Smith, R.J. Nolan, and D.L. Eisenbrandt (1987). **Acute, Pharmacokinetic, and Subchronic Toxicological Studies of 2,4-Dichlorphenoxyacetic Acid**. Fundam. Appl. Toxicol.9(3): 423-435 [DOI](https://doi.org/10.1016/0272-0590%2887%2990025-X) | 0 / 2 |
| 990 | Marking,L.L. (1970). **Juglone (5-Hydroxy-1,4-Naphthoquinone) As a Fish Toxicant**. Trans. Am. Fish. Soc.99(3): 510-514 [DOI](https://doi.org/10.1577/1548-8659%281970%2999%3C510:JHAAFT%3E2.0.CO%3B2) | 6 / 0 |
