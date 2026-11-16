# Exact steps for human verification

[Analysis](../README.md) · [Detailed label contract](label_review_guide.md) ·
[Deeper-review assessment](deeper-assay-review.md) · [Dietary triage](dietary-triage.md)

These steps turn existing review leads into auditable decisions. They do not
require running a model. Separate **plant response**, **dietary exposure/safety**,
**natural occurrence** and **study-group membership**. A compound can satisfy more
than one role; none automatically determines the others.

## New release: resolve this hold first

The [5 November release assessment](verification-release.md) supersedes the older
conditional activity of **Li 7b / CHEMBL2253255** with an unresolved identity hold:
the reported source allyl substituent differs from the frozen cyclopropyl group.
Obtain the original structure/R-group table and SI, record the exact source page,
and ask a chemistry reviewer to adjudicate before assigning either activity label.
Do not overwrite frozen structures or silently transfer the response. Next check
Li 7w and the KIH-6127 geometry difference, then visually confirm the other 21 Li
assignments. External database matches and agreeing activity bands are insufficient.

Use `analysis/validate_activity_proposal.py` with the latest frozen hold audit
(command in the release assessment) in addition to human sign-off. The old pack's
schema validator does not enforce this newly discovered hold. Existing editable
worksheets have been preserved; record new source decisions in dated working copies.

## Start with the prepared working copies

The editable local pack is
`analysis/outputs/manual-verification-2026-11-05/` (absent from a fresh clone).
Original source packages and frozen result bundles were not changed.

| Open this file inside the pack | Use it for |
| --- | --- |
| `assays/li2006_source_mapping.csv` | 24 source compound/table checks; start here |
| `assays/he2011_source_mapping.csv` | 58 source compound/table checks; review separately |
| `assays/structure_drawings/li2006_*.svg`, `he2011_*.svg` | Seven computed reference sheets showing all 82 frozen SMILES, labeled with ChEMBL/activity IDs |
| `assays/evidence_log_reference.csv`, `study_source_index_reference.csv` | Earlier AI-assisted annotations and source navigation; not human sign-off |
| `assays/policy_working.md` | Unapproved policy proposals to discuss and version with the research lead |
| `assays/reviewed_labels.csv` | Exact seven-column working copy; all 154 activity/origin labels start unknown |
| `dietary/triage_reference.csv` | Automated prioritization and reasons for the 40 dietary candidates |
| `dietary/review.csv` | Editable dietary identity, occurrence, exposure and decision worksheet |
| `sources/` | Save legally obtained papers, supplementary information (SI) and cited source excerpts |

Open CSVs as UTF-8 tables. Preserve IDs, SMILES, original cached values and column
names. Reference sheets are drawings of supplied SMILES, **not verified paper
structures**. Initialization/drawing manifests record starting bytes; edits to
working decision files are expected. Save dated versions of completed reviews.
The notebook does not treat these editable files as accepted evidence.

## A. Verify the plant-assay results

**Start with Li 2006**, the smaller 24-compound batch. He 2011 is a separate
58-compound batch. Do not fill either from the provisional labels alone.

1. **Get the original paper and SI.** Use university-library access, a legitimate
   repository, interlibrary loan or an author copy. Save the PDF/SI in `sources/`.
   Li: [10.1021/jf061976j](https://doi.org/10.1021/jf061976j), assay
   `CHEMBL3066645`; He: [10.1021/jf104247w](https://doi.org/10.1021/jf104247w),
   assay `CHEMBL3050362`. Abstracts and text mirrors help locate evidence but do
   not replace the missing structure/table pages. If unavailable, record that gap.
2. **Match one molecule to its original source compound number.** Open its row
   in `*_source_mapping.csv`, the matching SVG sheet and the paper/SI structure.
   Check atom connections, substituent positions, charge, chemical form and any
   stereochemistry. If the paper uses a common core plus an R-group table, expand
   that row's substituents; matching only the common core is insufficient. A shared
   name/formula or similar drawing is also insufficient.
   Ask a chemistry reviewer if uncertain. Fill `source_compound_number`,
   `structure_page_or_SI` and `structure_match` (`matched`, `unresolved` or
   `conflict`). Keep unresolved/conflicting decisions unknown.
3. **Find that compound's exact result cell.** Locate the correct plant species
   and pre-/post-emergence column at the relevant dose. Record `result_table_page`,
   `table_row` and `table_column`. Save a cited excerpt showing the compound number,
   relevant column headings and table footnotes; add its `saved_evidence_path`.
4. **Transcribe the original response exactly.** Put the paper's symbol, letter
   grade, inequality or value in `source_response_exact`. Li's proposed mapping
   concerns `++`/`>80%` and `-`/`<50%`; He concerns A/B/C/D bands. Confirm those
   meanings from the original table/legend. Do not turn a band edge into an exact
   measured percentage or silently replace the frozen ChEMBL value.
5. **Check methods and quality.** Fill `species_stage`,
   `application_rate_and_units`, `application_mode`, `duration`, `controls` and
   `replication` from the methods/table/SI, with page references. Check the proposed
   Li 150 g ai/ha, 15-day post-emergence context and He 1500 g ai/ha, 20-day
   context against the originals. “ai” means active ingredient. Record missing
   replication or controls as **not reported**, and contradictions in
   `conflicts_or_missing_details`; do not guess or silently repair g/kg units.
6. **Agree the label rule with the research lead.** Evidence collection above can
   proceed now. Before accepting labels, agree the species, exposure, endpoint,
   quality requirements, positive/low-response thresholds, gray zone and treatment
   of conflicts. Record reviewer/date and a versioned policy in `policy_working.md`.
   The existing Li and He proposals remain unapproved. Low response at one rate
   means only low response under that policy, not universal plant inactivity.
7. **Make and sign the row decision.** Fill `proposed_decision` (`active`,
   `low_response` or `unknown`), `accepted_policy_id` only after approval,
   `human_reviewer`, `human_review_date` and `scientific_approval_reference`.
   A second reviewer/research lead should be able to reproduce the match, source
   response and decision without relying on the cached label. Insufficient source,
   identity or quality evidence stays unknown. Repeat for **every** candidate.
8. **Transfer only accepted decisions to a versioned label file.** Use
   `assays/reviewed_labels.csv` for **one accepted policy at a time**; save separate
   versioned files for Li and He. Preserve all 154 original IDs, leaving out-of-scope
   rows unknown. For an accepted known activity, fill `activity_context`,
   `activity_reference` (DOI/page/table/row/column/source compound plus assay/activity
   IDs), `activity_policy` and `herbicidal_activity`. The importer's `inactive`
   value can represent accepted policy-specific low response; its restricted
   meaning must remain in the policy/context. Do not import `low_response` as a
   new categorical value. Keep reviewer/sign-off details in the mapping/log files,
   not extra columns in the seven-column label file.
9. **Validate without fitting.** Run the prepared validator from the repository
   root using the command below. It checks the exact seven columns, all original
   IDs, required support fields, one-policy rule and identity-label conflicts.
   Read the printed counts; `None` means unknown, not inactive. Passing this check
   is not scientific approval or proof of assay comparability. Do not use
   `screen.py --labels` on provisional files.

```bash
analysis/.venv/bin/python analysis/outputs/manual-verification-2026-11-05/validate_labels.py
```

For a separately saved policy-specific label version, add
`--labels path/to/your_versioned_labels.csv`. The broader
[label guide section 9](label_review_guide.md#9-validate-the-worksheet-without-fitting-a-model)
explains the schema-check boundary. The prepared validator reads the frozen
structure features; it does not retrieve records, fit a model or edit a file.

A completed assay row needs an exact structure/source match, exact result location,
recorded exposure and quality information, an accepted rule, and a traceable signed
decision. If any requirement fails, a documented unknown is a valid outcome.

## B. Verify the dietary comparison candidates

1. **Define the claim and dose.** Agree what “benign at a high consumable dose”
   means for this study: population/species, oral amount with units, chemical form,
   frequency, duration and endpoints. Specify whether the target is a human dietary
   comparison, a non-target toxicity comparison or plant inactivity. There is no
   universal safe dose or generic non-toxic label established by this project.
2. **Begin with the 12 provisional dietary candidates.** Open
   `dietary/triage_reference.csv`; use it as a queue. Start with a small pilot such
   as glycine and L-alanine, then apply the same checks to every proposed comparator.
   Prioritization is not acceptance; examine flagged/excluded cases separately.
3. **Confirm exact identity and occurrence.** Compare the PubChem CID, SMILES and
   InChIKey with the substance in the food-use/safety source. Check free compound
   versus salt/ester, stereoisomer and anomer. For the professor's plant/animal
   requirement, find an exact-compound occurrence reference with a named organism
   and fill `natural_occurrence_reference`. Food use or manufacture alone does not
   establish natural occurrence; fungal occurrence is a separate source role.
4. **Read the underlying exposure evidence.** Follow the source URLs and the
   notebook's agency/text drill-downs. Prefer the original study or authoritative
   assessment over a PubChem summary alone. Record the amount, units, tested
   population, route, duration, chemical form, endpoint and adverse-effect limits.
   A food-use allowance, labeling trigger, ADI and supplement caution are different
   evidence types. Do not treat a labeling threshold as a universally safe dose.
5. **Resolve applicability and flags.** Check whether the evidence actually covers
   the declared amount/population/time. Keep susceptible populations, interactions,
   other-species toxicity, formulation/purity and evidence gaps visible. Separate
   isolated free-acid exposure from dietary fats and pure sugars from mixture
   references. A text match may describe a null result or unrelated exposure:
   read the whole source context before accepting or rejecting the candidate.
6. **Record a bounded decision.** In `dietary/review.csv`, fill `dose_value`,
   `dose_unit`, `population_species`, `route_duration`, `decision_reference`,
   `reviewer` and `decision`. Use explicit wording such as “candidate supported
   for the stated human dietary comparison” or “needs further evidence”; state
   restrictions and record approval date in the decision. Do not simply write
   “non-toxic.” Leave `high_dose_safety`/`plant_activity` unknown until their own
   declared evidence requirements are met. Do not fabricate human sign-off.
7. **Keep plant activity independent.** Even an accepted dietary comparator needs
   a suitable tested plant assay to become a plant-negative training example.
   Capric/caprylic acids must not be assumed inactive from food use. Resolve the
   proline overlap before assigning study roles or splitting datasets.

## C. Verify natural-active / allelopathic candidates separately

For the four ophiobolin leads, check each frozen structure against original
isolation/characterization diagrams, including stereochemistry; record organism,
source compound number and primary citation. Assess the detached-leaf activity
under its own endpoint/policy. It is not a whole-plant percentage response.
For an **allelopathic** role, also document the relevant organism–plant effect
under an agreed definition; natural occurrence or phytotoxicity alone does not
establish that ecological role. Human dietary safety is another independent claim.

## D. What must happen before the next model run

- Accept and version the relevant label/evidence policy and identity crosswalk.
- Resolve shared structures and contradictory observations; keep unknowns explicit.
- Add independent negative-bearing chemistry/publications. Li has only two
  low-response-bearing scaffolds; He's known subset has two total scaffolds. Both
  fail current three-/five-fold scaffold checks even if every proposed row is verified.
- Predeclare training/validation groups and reserve independent compounds/publications.
- Then compare formula and fingerprint logistic/forest models under the same
  validation design. Assess ranking, classification, calibration and chemical-domain
  limits for the declared endpoint. General toxicity needs its own measured labels.

For the professor's three-group hypothesis, define study roles before comparison.
Naturally occurring herbicides and human dietary compounds can overlap other roles;
no inherent numerical “middle” follows from three names. Test an independent
allelopath group's scores or declared class contrasts rather than forcing an order.
