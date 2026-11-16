# Third-pass structure and primary-source verification (2026-11-05)

**Scope:** frozen ChEMBL_37 worksheet, **154 distinct compounds, 157 observations, 14 assays/publications**. This release *extends* the 2026-10-29 deep audit without modifying original ChEMBL evidence. It is an AI-assisted research audit, **not** a human-reviewed gold-standard labeling dataset. **Final, approved activity/origin labels: 0** because the supplied policy remains explicitly unapproved. Some assays remain accessible only by abstract, and compound-to-original-table verification is incomplete. No claim of having completely verified all 154 molecules is made.

## New, technically reproducible results

1. RDKit 2025.09.4 parsed **154/154** SMILES. All 154 yield unique full InChIKeys. The frozen chemical data remain unchanged.
2. **Four natural fungal ophiobolins match PubChem *full* InChIKeys including stereochemistry**: CHEMBL522808 ophiobolin A, CHEMBL2252910 6-epi-ophiobolin A, CHEMBL2393053 3-anhydro-6-epi-ophiobolin A, CHEMBL469706 ophiobolin I. Primary publications explicitly report their isolation from cultures of fungi in 1987/1989/2006/2021/2026 (where relevant); distinguish named source compound from broader chemical genus. PubChem cross-check supports chemical structures; primary isolation studies support natural occurrence. Re-read source figures for final signed-off stereo provenance. All four were previously candidates; identity evidence is substantially stronger now.
3. **Eleven synthetic-provenance pesticide names** have full InChIKey agreement against University of Hertfordshire PPDB. These are ametryn, alachlor, atrazine, norflurazon, sulfentrazone, metolachlor, acifluorfen, clacyfos, pethoxamid, 2,4-D and glyphosate. PPDB explicitly designates synthetic origins; this does not prove that no naturally occurring organism could ever make the molecule. The project's definition of `synthetic` must be approved before labels are finalized.
4. **Pyriminobac-methyl/KIH-6127** (CHEMBL2253237) matches PPDB on InChIKey **connectivity only**, not the entire InChIKey: frozen ChEMBL `USSIUIGPBLPCDF-JMIUGGIZSA-N` includes E/Z geometry whereas PPDB reference `USSIUIGPBLPCDF-UHFFFAOYSA-N` leaves that stereo unspecified. It is a named reference herbicide, not a novel 2006 phthalazinone. Marked partial, not exact.
5. Original Li et al. 2006 (`10.1021/jf061976j`) source text enables a detailed source-number crosswalk for **7a–7w plus reference KIH-6127**. ChEMBL categorical **13 active + 10 low-response novel compounds plus one active comparator** agree with the narrative >80% / <50% band classification in the paper at 150 g a.i./ha post-emergence against *Amaranthus retroflexus*. The 13 named source high-response compounds are 7a–7d, 7h, 7k, 7o, 7q–7u, 7w. This is agreement of biological *bands*, not independently verified data precision.
6. **Critical apparent source-to-ChEMBL identity discrepancy for 7b / CHEMBL2253255.** Paper Table 1 R substituent is `CH2CHCH2`, i.e. allyl (N-CH2-CH=CH2); the manuscript's 7b proton NMR signals (4.68 d 2H, 5.14–5.18 m 2H, 5.93–5.70 m 1H) are consistent with allyl. Frozen ChEMBL has *N-cyclopropyl* (`...nn(C4CC4)...`), a constitutional isomer with same molecular formula. **Do not transfer 7b activity to ChEMBL CHEMBL2253255 until the source drawing/SI and curation mapping are checked.** Other 2006 individual assignments are source-substituent consistent but still require independent visual figure validation. The 7w substituent is not fully accessible in the extracted source Table 1.
7. **Independent primary natural-product studies**: Peña-Rodríguez & Chilton 1989 DOI `10.1021/np50065a046` isolated four related toxins from *Bipolaris sorghicola*, including **3-anhydro-ophiobolin A**, which is **not in the frozen 154**. Their endpoint was area of necrosis (leaf spot after 72 h), not weed growth inhibition percent. The 2021 paper at `https://pmc.ncbi.nlm.nih.gov/articles/PMC9157744/` isolated five compounds from *Bipolaris setariae*. **3-anhydro-ophiobolin A and 6-epi-ophiobolin A** were most phytotoxic to green foxtail leaves, whereas ophiobolin I was weak or absent for this assay; the article also reports **synergy**. No universal activity/inactivity label may be inferred. Ophiobolin derivatives must undergo **non-target/ecotoxicity review** independently of their fungal origin.
8. Ten additional natural-product leads beyond the frozen set are documented in `new_out_of_worksheet_compound_leads.csv` alongside 3-anhydro-ophiobolin A (**11 total**). This includes ophiobolin B/J/E, 8-epi-ophiobolin J, maydispenoid A, new gigobolins A–C; new gigobolins' reported anticancer effects are **not evidence of herbicidal action**. These are discovery leads, not training labels.

## Assay methodological integrity and unresolved work

- The frozen ChEMBL `100` / `80` values in the **1991** herbicide study are normalized **ordinal 0–5** scores and must not be treated as precise response percentages.
- The **2011** He et al. phosphonate study uses A–D categorical inhibition ranges. The previous 47 active and 31 inactive totals **across three proposed assay-specific screen rules** are conditional only; source-specific structure and raw table verification remains unfinished for many molecules.
- The 2009 paper `10.1016/j.bmcl.2009.04.048` does not have an accessible, independently checked primary compound-by-compound table in this pass. **Do not call its zero-valued rows verified inactive**.
- The 2006 phthalazinone paper's R table text was flattened by HTML extraction; no claim that the source images/SI were visually matched for *every* analogue. The 7b inconsistency is a reproducible source **red flag**, not an adjudicated database correction.
- The four natural ophiobolins have *validated database-level stereo structure matches* plus *named primary isolation evidence*. This is not proof that each isolate's paper stereochemical figure directly matched the particular ChEMBL drawing; that last check remains signoff work.
- PPDB `synthetic origin` distinguishes manufactured products from directly obtained fungal isolates. If the project's natural/synthetic policy is instead exclusive biosynthetic occurrence, additional negative-occurrence evidence would be needed and absence of an occurrence record must **not** turn into a synthetic label.

## Files and interpretation

- `independent_structure_origin_crosschecks.csv`: **16** independent external structure checks (4 natural + 12 herbicide references, 15 full matches and one connectivity-only).
- `li_2006_24_compound_source_crosswalk.csv`: source compound number, parent R substitution, frozen ChEMBL band, paper band, statuses and correction flag; do not mistake matching band for proof of same compound identity.
- `all_154_compound_verification_matrix.csv`: single-row-by-row audit of all 154 compounds, reporting exact crosschecks, remaining evidence and the critical hold.
- `evidence_log_with_verification.csv`: prior 157-row log plus the additional 2026-11-05 independent structure/origin/source mapping fields; original source fields retained.
- `PROPOSED_ORIGIN_FULL_STRUCTURE_MATCHES_NOT_FOR_TRAINING.csv`: **15** proposed origins with full external chemical identity agreement; **policy not approved**.
- `new_primary_study_provenance.csv`, `new_out_of_worksheet_compound_leads.csv`: primary isolation and additional candidates.
- `reviewed_labels.csv`: unchanged valid unknown / unknown labels until policy approval and source issue resolution.
- `conditional_assay_screen_NOT_FOR_TRAINING.csv`: previous scenario screening retained as historical context, **not** approved labeled ground truth; **CHEMBL2253255 row now superseded by explicit critical hold**.
- `policy_draft.md`, `researcher_guide_source.md`, `compound_evidence_packets.md`: retained initial reference context, not silently edited.

## Recommended next audit sequence

**Priority 0:** check original PDF/SI printed 7b structure against ChEMBL CHEMBL2253255, and report clear mismatch to ChEMBL if confirmed; preserve all raw snapshots unchanged. **Priority 1:** scientific lead approves assay-specific and origin-specific policies. **Priority 2:** paper-table crosswalk for He et al. 2011's 58 original molecule rows, using original SI/PDF. **Priority 3:** 2009 cyanoacrylate 25 molecule table and structural drawings; 2011 2,4-D/clacyfos source and all other assay groups. **Priority 4:** curate new out-of-worksheet 3-anhydro-ophiobolin A, independent herbicidal endpoints, toxicity and environmental persistence. No broad safety claims can be made from herbicidal activity or natural origin alone.

## Citable primary and structural references

- Li et al. 2006, `https://doi.org/10.1021/jf061976j`; full text `https://www.lookchem.com/FreePDFArticle/143613-10-9.htm` (methods, Table 1, 7b 1H NMR, activity narrative).
- Evidente et al. 2006, `https://doi.org/10.1021/jf052843l` (four naturally isolated ophiobolins).
- Peña-Rodríguez & Chilton 1989 `https://doi.org/10.1021/np50065a046`; direct PDF link in `new_primary_study_provenance.csv` (natural isolated compounds, 72-hour lesion assay).
- Sugawara et al. 1987, `https://pmc.ncbi.nlm.nih.gov/articles/PMC304811/` (ophiobolin I crystallography).
- Zhao et al. 2021, `https://pmc.ncbi.nlm.nih.gov/articles/PMC9157744/` (green foxtail phytotoxicity, synergy, isolation).
- Carbone et al. 2026, `https://pmc.ncbi.nlm.nih.gov/articles/PMC13036769/` (new natural-products isolation; anticancer focus).
- Pesticide Properties Database `https://sitem.herts.ac.uk/aeru/ppdb/en/` (synthetic origin and InChIKeys for named products).
- PubChem NCBI CID pages for natural compounds in `independent_structure_origin_crosschecks.csv`.

**Scope warning:** this is explicitly not a toxicity dataset and not a model-training release. Natural origin, herbicidal potency, human toxicity, ecological toxicity and target selectivity are separate attributes requiring different assays.
