# Second-pass compound-by-compound review — study-family evidence deepening

**Date:** 2026-10-29  
**Scientific approval:** not obtained. **NOT suitable as ground-truth model labels.**

## Coverage and what was actually verified

All **154 distinct frozen ChEMBL molecule IDs** and **157 observation records** were carried forward. A per-compound audit row was created for every compound. The source review was organized around **all 14 original papers**, because 58 compounds share one 2011 publication, 24 share a 2006 publication, and 25 share a 2009 publication. This study-family review is more systematic than searching isolated IDs, but it **does not constitute individual compound-to-source-structure verification for 154 compounds**, nor an exhaustive natural-origin database review for all molecules. Sparse search results for ChEMBL identifiers alone do not establish a biological conclusion.

Evidence levels differ: original primary open J-STAGE PDF in the previous pass (1991), 2026 primary PMC ophiobolin paper, full reproduced text of 2006 phthalazinone, 2010 PPO, 2011 triazine and 2011 phosphonate papers, original ACS/Elsevier abstracts for other papers. A reproduced OCR/text rendering is not equivalent to visually auditing the publisher's original PDF structures or table columns. The original 2009 BMCL 25-observation results table is still inaccessible here. The 14-source index lists the accessed evidence level.

## Quantified **conditional**, unapproved assay-specific screening

| Source-specific context | Count | Conditional active | Conditional inactive/low response | Gray zone or none | Key qualifications |
|---|---:|---:|---:|---:|---|
| Okamoto 1991, pre-emergence Amaranthus lividus, ordinal 0–5, 10 g active ingredient/are | 4 | 4 | 0 | 0 | Four source scores 4/5 or 5/5, original paper Table VI; source-structure identity remains pending |
| Li 2006, Amaranthus retroflexus post-emergence, 150 g active ingredient/ha, 15 days | 24 | 14 | 10 | 0 | Original paper ++ >80%, - <50%; compound/table crosswalk pending |
| He 2011, Amaranthus retroflexus post-emergence, 1500 g active ingredient/ha, 20-day greenhouse trial | 58 | 29 | 21 | 8 | Grades A/B (=75+), D (<=50), C (50–74) gray-zone; NOT point % values |
| Remaining assay contexts | 68 | — | — | 68 | No source-specific policy screened to conclusion; original assay tables mostly unavailable |
| **TOTAL** | **154** | **47** | **31** | **76** | 47/31 are **CONDITIONAL NOT APPROVED** |

IMPORTANT: These are **three different assay definitions and three separate proposed policies**, not a validated homogeneous supervised target. The inactivity category applies **only to the specific assay, exposure and threshold**. In `conditional_assay_screen_NOT_FOR_TRAINING.csv`, the `unknown` value means graded intermediate and `not_assessed` means no proposed screening rule for that study. Neither is a negative.

## Source-method improvements

**Li et al. 2006**, DOI https://doi.org/10.1021/jf061976j, primary text mirror https://www.lookchem.com/FreePDFArticle/143613-10-9.htm: explicit visual ++/>80, +/50–80, -/<50 score bands; Amaranthus two-leaf stage, postemergence 150 g ai/ha, 15 days, untreated and DMF control, no DMF effect. This contextualizes 24 strict ChEMBL inequalities; none is a precise point estimate. The original full image/compound mapping remains unresolved.

**He et al. 2011**, DOI https://doi.org/10.1021/jf104247w, mirror https://www.lookchem.com/FreePDFArticle/1299293-66-5.htm: greenhouse 2–3-leaf foliar spray, acetone and Tween 80, 1000 L/ha, three completely randomized replicates, fresh weight relative to control, grade bins A/B/C/D. All 58 frozen data values remain intact; numeric band-edge codings are flagged explicitly. Primary PDF/SI source-to-structure matching is outstanding.

**Jiang et al. 2010**, DOI https://doi.org/10.1021/jf9026298, mirror https://www.lookchem.com/FreePDFArticle/1202578-92-4.htm: source preliminary trial used 150 g ai/ha, eight top compounds were further evaluated at lower rates, with three replicates, untreated and solvent controls, Amaranthus dicot two-leaf stage, and visual effects 15 days after treatment. The specific 75 g/ha ChEMBL rows must be cross-checked against correct compound/table cell: original abstract's 37.5 g dose applies to selected lead, not the entire series.

**Zhao et al. 2011**, DOI https://doi.org/10.1021/jf203383s, mirror https://www.lookchem.com/FreePDFArticle/1342304-71-5.htm: Nankai 1.5 kg/ha fresh-weight experiment and Syngenta glasshouse 1000 g/ha visual-effect experiment and separate 96-well test are **different protocols**. The ChEMBL 1 kg/ha preemergence records appear most consistent with glasshouse Table 2, but exact column/compound mapping requires visual validation. The Norflurazone entry is `Not Determined`, never inferred negative.

**2009 BMCL cyanoacrylate 25-row batch**, DOI https://doi.org/10.1016/j.bmcl.2009.04.048, PMID 19406637: original abstract confirms compounds were designed and synthesized and studied in multiple biological assays, but an original table was not located. **12 cached zeros are not newly assigned as negatives**. A 0% response at 1.5 kg/ha would be policy-specific at most, even after confirming the source.

**Other explicit caveats:** DOI 10.1021/jf803632t and DOI 10.1021/jf0636519 report **375 g/ha** in publisher abstracts, whereas some frozen assay descriptions say **375 kg/ha** (five observations total). Frozen CHEMBL3047983 says 150 kg/ha but the exact source unit is still unverified. DOI 10.1021/jf301829m abstract highlights 150 g ai/ha while its associated frozen record says 75 g/ha; this may be a different dose within that study rather than transcription error. CHEMBL3053086 reports detached-leaf necrosis **in mm**, not percentage whole-plant growth inhibition; two entries lack numeric responses. CHEMBL452197 and CHEMBL95764 have distinct assay contexts, not interchangeable replicates.

## Natural origin review

The four ophiobolins from *Drechslera gigantea* have stronger primary occurrence evidence from:

1. Evidente et al. 2006 J. Agric. Food Chem. DOI https://doi.org/10.1021/jf052843l
2. Evidente et al. 2006 *Phytochemistry* DOI https://doi.org/10.1016/j.phytochem.2006.07.016
3. Carbone et al. 2026 J. Nat. Prod. DOI https://doi.org/10.1021/acs.jnatprod.5c01414 (open https://pmc.ncbi.nlm.nih.gov/articles/PMC13036769/)

Names: ophiobolin A/CHEMBL522808; 6-epi-ophiobolin A/CHEMBL2252910; 3-anhydro-6-epi-ophiobolin A/CHEMBL2393053; ophiobolin I/CHEMBL469706. The **names** have multiple consistent independent isolations, but the exact stereochemistry/form crosswalk to the frozen SMILES has not been approved. No additional `natural` or `synthetic` labels were justified by this search. Named industrial agrochemicals are not automatically classified synthetic under the proposed natural-*occurrence* claim.

## Current release decisions and key constraints

- **Authoritative reviewed_labels.csv:** 154 herbicidal_activity=`unknown`; 154 natural_origin=`unknown`. Existing context and citation support preserved.
- **Provisional original file:** four `active` ordinal candidates and four `natural` occurrence candidates on different rows.
- **Two new provisional single-policy CSVs:** Li 2006 14/10 proposed active/low-response; He 2011 29/21 proposed active/low-response. Do not merge these columns or interpret as approved training data.
- **Expanded evidence_log.csv:** 157 source observations, 157 `in_progress`, 0 `reviewed_known`. Original 16 source fields unchanged, all additional metadata recorded in review columns.
- **compound_by_compound_deep_audit.csv:** all 154 compounds with frozen structure, assays, source access, next exact-structure check and disposition.
- **study_source_index.csv:** 14 separate original papers, count and access level.

Next highest-value research is obtaining original PDF/SI diagrams and results tables for Li 2006 and He 2011 (82 observation rows), then validating chemical structures and postemergence source columns. These source-specific conditional data could become scientifically useful only with an explicit approved policy, quality checks, and independent paper/scaffold split. More literature searches by bare ChEMBL ID alone are unlikely to resolve original-source compound numbering.
