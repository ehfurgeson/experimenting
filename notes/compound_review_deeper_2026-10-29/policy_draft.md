# Proposed activity and origin policies — researcher screening v0.1

**Status: UNAPPROVED.** Drafted 2026-10-29 by AI-assisted literature screening for discussion with the scientific research lead. **No known activity or origin labels are authorized for use in training by this draft.** `reviewed_labels.csv` therefore keeps all activity and origin categories `unknown`; `PROVISIONAL_labels_NOT_FOR_TRAINING.csv` is a separate candidate-decision worksheet, not accepted ground truth. The original `handoff_manifest.json` and original uploaded files are unchanged.

## Activity: proposed narrowly scoped 1991 upland Amaranthus ordinal-pot assay

- **Policy ID:** `PROPOSED-OKAMOTO-1991-UPLAND-10G-AI-PER-A-v0.1` (not accepted).
- **Scientific reviewer / acceptance date:** pending; research lead to accept/reject and provide new versioned ID.
- **Claim and limits:** effect on germinating/sown *Amaranthus lividus* in the **specific 1991 pre-emergence upland-pot study**, not generalized herbicidal potential or field-use efficacy.
- **Eligible publication / assay:** Okamoto et al. 1991, *Agric. Biol. Chem.* 55:2737–2743, DOI https://doi.org/10.1271/bbb1961.55.2737; ChEMBL assay `CHEMBL3079324` ONLY, **subject to identity verification**. Original primary PDF: https://www.jstage.jst.go.jp/article/bbb1961/55/11/55_11_2737/_pdf/-char/en, methods p.2738 and Table VI p.2743.
- **Species:** The source reports *Amaranthus lividus* (Table VI column **e**). Kew lists it as a synonym of *A. blitum* subsp. *oleraceus*, the ChEMBL assay taxon: https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:316346-2. Species synonymy is documented, not presumed.
- **Stage, application, duration:** seeds sown 0.5–1 cm deep in clay-loam upland soil; aqueous wettable-powder dilution sprayed onto soil surface, 10 **g active ingredient per are (g a.i./a)**, greenhouse ~25 °C; visually evaluated after two weeks. Do not equate this with leaf spraying or post-emergence use. Preserve original application units.
- **Endpoint:** author's **ordinal injury/killing grade 0–5**, with 0 normal growth and 5 complete killing; 1–4 intermediate. The ChEMBL records `80%` and `100%` are **scale conversions of score 4 and 5**, not experimentally measured percentage inhibition. The source scores must be recovered from Table VI.
- **Proposed candidate positive:** original score **4 or 5** at the specified condition, clearly linked to exact source compound. Proposed candidate negative: original score **0 or 1**, if the scientific lead accepts that ordinal boundary and adequate quality evidence is available. Original scores **2 or 3**, missing, uncertain or conflicting = `unknown`. These thresholds are proposed for review only; they do **not** establish an approved biological policy.
- **Equality / inequalities:** compare only the original ordinal score, not `80%`, `100%`, or interpolated decimals. A value from other modes, doses, species or endpoints cannot be pooled.
- **Control and quality requirements pending:** source describes ordinal scale but inspected methods do not identify a sufficient replication count; a scientific reviewer must decide whether this evidence quality is acceptable and inspect original tabulation/replicate notes. When inadequate, leave `unknown`.
- **Identity requirements pending:** inspect original Fig. 1 for alachlor/metolachlor and Table II for source compounds **11** and **35**, including possible cis/trans material. Do not transfer evidence across salt, form, stereoisomer or unconfirmed drawing matches. Four candidate scores from Table VI are: alachlor 5; metolachlor 4; compound 35 (reported as pethoxamid in ChEMBL) 5; compound 11 5.
- **Multiple measurements:** do not pool 1991 with other studies. Discordant observations require explicit adjudication, otherwise `unknown`.
- **External validation:** hold out this publication as a group if used in a later study; all four candidates come from one publication, not four independent validations.
- **Known limitations:** no human scientific approval, exact source-to-ChEMBL structures not yet signed off, and replicate adequacy not confirmed. Consequently **zero approved active/inactive labels**.

## Separate source-specific interpretation review: He et al. 2011 (NOT a second labeling policy)

2011 DOI https://doi.org/10.1021/jf104247w, Table 1 and Methods: responses were **letter-grade bins**, not exact measurements. Grades were **A = 90–100%; B = 75–89%; C = 50–74%; D = ≤50%** at **1500 g active ingredient/ha** in greenhouse. The frozen assay `CHEMBL3050362` carries 58 records: 18 at `=90` (A), 11 at `=75` (B), 8 at `=50` (C), and 21 at `<=50` (D). The numeric entries generally denote category edges and **must not** be interpreted as precise 90%, 75% or 50% observations. Full-article text reproduction: https://www.lookchem.com/FreePDFArticle/1299293-66-5.htm; original publisher https://pubs.acs.org/doi/10.1021/jf104247w. A future policy must separately establish source compound mapping, pre/post table-column mapping, controls, quality and class rules. No labels currently assigned to this batch.

## Natural-origin: proposed documented fungal isolation rule

- **Policy ID:** `PROPOSED-DOCUMENTED-NATURAL-ISOLATION-v0.1` (not accepted).
- **Positive `natural` claim:** structure is demonstrated to occur as an identified, isolated product from a named organism, supported by a traceable primary isolation/characterization paper; named structure must be reconciled to the frozen molecule ID, absolute stereochemistry and chemical form.
- **`synthetic` claim:** requires a separately agreed operational definition and **affirmative provenance evidence** supporting that classification. A synthesis method, commercial pesticide identity, absence of an occurrence record, or missing LOTUS/COCONUT hit **does not**, by itself, establish nonoccurrence in nature. Consequently **zero synthetic candidates** from this screening.
- **Laboratory-synthesized natural products:** still qualify as `natural` if natural occurrence of the **same structure** is affirmatively documented.
- **Exact structure:** verify stereocenters, double-bond geometry, salts/esters and molecular form; a shared trivial name or chemical class alone is insufficient. If not verified, candidate remains provisional.
- **Four natural candidates:** ophiobolin A (`CHEMBL522808`), 6-epi-ophiobolin A (`CHEMBL2252910`), 3-anhydro-6-epi-ophiobolin A (`CHEMBL2393053`), and ophiobolin I (`CHEMBL469706`). All four are named in 2006 fungal isolation https://doi.org/10.1021/jf052843l (compounds 1–4 respectively) and re-isolated/identified in 2026 https://doi.org/10.1021/acs.jnatprod.5c01414 (known compounds 4,5,6,8 respectively). Full 2026 text: https://pmc.ncbi.nlm.nih.gov/articles/PMC13036769/. ChEMBL/PubChem identity links are preserved per row in the log. Full structural mapping against drawings and stereochemistry remains a final check.
- **Reviewer/date/status:** AI-assisted source screening 2026-10-29; human scientific reviewer and acceptance **pending**. Do not treat candidates as finalized known labels.

## Additional source-quality alerts

- Assays `CHEMBL3051568` (DOI https://doi.org/10.1021/jf803632t; 3 records) and `CHEMBL3066743` (DOI https://doi.org/10.1021/jf0636519; 2 records) describe `375 kg/ha` in cached ChEMBL text, while the respective publisher abstracts report **375 g/ha**. The original records are unchanged; confirm paper methods prior to correction.
- Assay `CHEMBL3047983` likewise describes `150 kg/ha`, but primary-source methods have NOT been checked, so **do not silently change its units**.
- `CHEMBL3053086` is a leaf-puncture necrosis **mm** endpoint with two missing values, not percent whole-plant growth inhibition. Do not pool with the 1991 assay.
- `CHEMBL3066645` carries strict `>80%` / `<50%` data. Preserve those inequalities; they are not an approved binary threshold policy.

## Pending sign-off checklist

1. Research lead reviews the intended target and quality criteria; accept/reject narrow 1991 rule with an approved version number.
2. A chemistry reviewer confirms each proposed structure against source figures, names and stereochemistry.
3. Resolve replication/controls and source-specific endpoint transcription issues, especially 58 categorical values and 4 ordinal values.
4. Accept/reject the natural-origin definition and each isolation-to-structure crosswalk independently.
5. Only then transfer accepted candidate labels into `reviewed_labels.csv`, documenting approvals in `evidence_log.csv`; validate importer and structural cross-validation support before training.


## Extended, assay-specific screening proposals — v0.2 (NOT APPROVED)

These two alternatives MUST NOT be combined in the same approved training label CSV, and must not be pooled with Okamoto 1991. The `conditional_assay_screen_NOT_FOR_TRAINING.csv` file is a cross-policy triage index, **not** a seven-column import file. The two `PROVISIONAL_*_NOT_FOR_TRAINING.csv` files are separate, source-specific **hypothetical** label candidates. They retain one source-specific activity policy each. Every proposed per-compound classification still requires original paper row/structure matching and scientific signoff.

### `PROPOSED-LI2006-AR-150G-POST-BOUNDS-v0.1` — 24 candidates

- Intended claim: `Amaranthus retroflexus` whole-plant growth inhibition in the exact Li et al. 2006 greenhouse trial (DOI 10.1021/jf061976j), after *post-emergence* spraying at 150 g active ingredient/ha, dicotyledon two-leaf stage, assessed visually at 15 days.
- Original method: approximately 20 seeds per pot, formulated 100 g/L emulsified concentrate in DMF/Tween-80; untreated and DMF-solvent control, with solvent control no herbicidal effect. Replication count remains unverified. Original paper full-text reproduction: https://www.lookchem.com/FreePDFArticle/143613-10-9.htm, herbicide assay and Table 1.
- Original data representation: `++` means `>80%`, `+` means between 50 and 80%, and `-` means `<50%`. ChEMBL strict inequalities must be preserved exactly.
- *Conditional* candidate if corresponding source cell verified: `>80%` => `active` (**14** ChEMBL rows); `<50%` => `inactive` (**10** rows). Any 50–80%, conflicting or missing data => `unknown`. This is a **source- and threshold-specific** definition of low response, not proof of universal inactivity.
- Approval blockers: source original structure/compound letter to frozen ChEMBL ID crosswalk; exact Table 1 row/AR/post column; replicate adequacy; operational significance of selected strict thresholds and species restriction.

### `PROPOSED-HE2011-AR-1500G-POST-BANDS-v0.1` — 50 conditional candidates, 8 gray-zone

- Intended claim: `Amaranthus retroflexus` whole-plant 20-day greenhouse growth/fresh-weight response at 1500 g active ingredient/ha, with compound applied postemergence to foliage at 2–3-leaf stage (He et al. 2011, DOI 10.1021/jf104247w).
- Original method: acetone/Tween 80 spray carrier at 1000 L/ha; three replications in a completely randomized design; fresh-weight relative to controls. Original paper text reproduction: https://www.lookchem.com/FreePDFArticle/1299293-66-5.htm, methods p.4804 and Table 1 p.4806.
- **Important:** Table 1 is grades not percentage point estimates: A=90–100%; B=75–89%; C=50–74%; D=50% or lower. Because C and D share boundary 50% in reported wording, do not treat grade C's exact zero-width boundary as proof of inactivity.
- *Conditional* candidate under a hypothetical 75%/50% extreme-band rule: grades A and B => `active` (**29**); D => `inactive` (**21**); C => `unknown` (**8**). The D classification assumes low-response threshold `<=50` is scientifically adopted.
- Approval blockers: PDF/SI Table 1 compound row-to-ChEMBL canonical SMILES, original Amaranthus `post` column, source-grade transcription, full control definition, high 1500 g/ha exposure ecological meaning, appropriate threshold choice.

### Other assay families

The other eleven ChEMBL assay IDs (including CHEMBL3079324, which already has its own narrow proposed policy above) remain distinct from these two source-specific files. A 75-g/ha response is **not** equivalent to the 1500-g/ha measurement, and an `inactive` at one rate is not a claim of zero activity at every rate. The unreviewed dose-rate conflict for CHEMBL3047983 and differing glyphosate/other comparator protocols require paper-level validation.

### Further natural-origin provenance

A separate 2006 original isolation/characterization paper, *Phytochemistry* DOI https://doi.org/10.1016/j.phytochem.2006.07.016, also reports ophiobolin A, 6-epi-ophiobolin A, 3-anhydro-6-epi-ophiobolin A, and ophiobolin I from cultured *Drechslera gigantea*. This adds independent natural-occurrence evidence for the four `natural` candidates (2006 J. Agric. Food Chem.; 2006 *Phytochemistry*; and 2026 *J. Nat. Prod.*). Exact stereo/form identity remains a check; it does not justify other compounds as `synthetic`.

### Handoff rules

- Main `reviewed_labels.csv`: **all 154 activity and origin labels still unknown** until human signoff.
- `PROVISIONAL_labels_NOT_FOR_TRAINING.csv`: previous four activity and four natural proposals retained.
- New assay-specific source candidate CSVs: 24 and 50 conditional outcomes only; NOT accepted/verified.
- `evidence_log.csv`: 157 original rows, source columns immutable; 157 study-family `in_progress` records, 0 `reviewed_known`.
- `compound_by_compound_deep_audit.csv`: exact one row per molecule with study source, cached evidence, quality flags, policy-screening status, identity next action and evidence discovery link. This is *not* proof of 154 independently verified literature primary tables or 154 successful natural-product searches.
