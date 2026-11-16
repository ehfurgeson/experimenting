# Source-linked rat review, 2026-11-12

Local-only AI experimental work; no human scientific review, frozen inputs or
baseline edits. Primary paper: Gorzinski et al., Fundam. Appl. Toxicol.9:423–435,
1987, DOI10.1016/0272-0590(87)90025-X. PDF mirrored by24d.info, not retrieved from
publisher. Identity checked against first page and source reference. SHA256:
8c9ca688757250abc954294545473c77e75044ba167e00f8e0cb263c384306c5.
Authors are Dow laboratory investigators; paper notes industry-task-force support.
Corrections/retraction history was not exhaustively verified.

## What worked

- Successful PDF retrieval with signature/content checks. Scanned PDF has no native
  text; Poppler/Tesseract absent. Rendered13pages with existing temporary PyMuPDF
  environment, visually read printedpp423–427 and rechecked enlargedTable1/p426.
  Empty native-text files are not an extraction result.
- `curate.py` transcribes14 material/sex cells:13 uncensored material-tested LD50s
  with95% confidence limits,1 noncalculable female isooctyl bounded statement
  (`>720–<864`) retained verbatim without a midpoint/scalar. Named salts/esters are
  not automatically assigned canonical acid identity.
- Two pending acid cases match primaryTable1 at95% active content:
  result1055251 male607mg acid-equivalent/kg body weight; material639(555–736).
  result1147683 female726mg ae/kg; material764(663–879). Source reports single-dose
  oral young-adultFischer344rats,5animals/sex/dose,corn oil,~18hfasting and2week
  observation. Do not import explicit gavage wording from the different
  pharmacokinetic subsection. Acute administration technique is not named.
- Both are provisionally eligible under a separately declared **single-dose oral,
  source-reported acid-equivalent** experiment; remain unresolved under the
  conservative explicit-gavage/capsule rule. Primary controls are not established
  by borrowing subchronic concurrent-control metadata. No admission to baseline.
- Native dietary/DT and2wk exposure metadata conflict with Table1 single-dose
  methods. Keep originals, return source facts/conflict; do not silently overwrite.
  Observation2wk exists natively and now normalizes to336h after committed
  elapsed-week support. Normalized native exposure2wk is retained only as a
  conflicting source field, not primary continuous exposure.
- Four priority overlap pairs now have AI-experimental `different_observation`
  decisions: EPA counterparts are15mg/kg-day,91-daydietaryLOELs (female thyroid,
  male relative organweight), unlike acute LD50. The existing importer accepts and
  exports all4 in new `analysis/outputs/rat-source-reconciliation-2026-11-12/`.
  Remaining22prioritypairs are unreviewed; fullqueue18,992pairs remains intact.

## Source arithmetic discrepancies

`conversion-audit-v1/` checks displayedTable1footnotec:
MWratio% × active% × materialLD50 /10,000. Acid rows agree within rounding.
Two female ester entries fail the displayed arithmetic by much more than1mg/kg:
Butoxyethanol ester reports565 versus529.327056 from printedinputs; butyl ester
reports519 versus472.0968. Enlarged original table visually confirms transcription.
Do not correct the primary values, blame a specific typo, normalize them into a
new dose, or adopt those ester conversions. All reported values stay unchanged
with explicit companion flags. Other11 computablecells agree within1mg/kg;
sourceinputs have limited displayed precision. No CI is derived for acid equivalent.

## Sensitivity arithmetic, not a harmonized toxicity comparison

Historical EPA baseline:43exact +25censored records;49compound summaries, of which
34 have exact medians and15 only censored support. For2,4-D it retains one375mg/kg
WHO summary with unresolved primary lineage/material/sex/dose basis.

`primary_basis_strata.csv` keeps new material-tested and acid-equivalent points
separate, confidence limits only on the former. In deliberately relaxed mixed-
basis sensitivities, adding607/726 as separate rows shifts2,4-D's median375→607.
Taking their descriptive paper-level median666.5 first gives combined520.75.
These expose reporting/sex weighting assumptions, not independent experiments or
a validated effect estimate. Neither resolves the375value's basis/lineage.
All34compound bins and tertilecutoffs1080/3400mg/kg stay unchanged;25bounds are
preserved. No new compound with harmonized toxicity, natural-product rank or model.
Frozen medians/cutoffs untouched. A first assertion incorrectly assumed the49-row
compoundfile contained only34exact-median rows; fixed before output creation,
explicitly retaining15bounds-only compounds and25censored observations.

## Reproduction and checks

`fetch.py` needsnetwork. `curate.py`, `conversion_audit.py`, `sensitivity.py` and
`verify.py` run offline through lockedanalysisenvironment fromreporoot. Choose new
outputversions before rerunning curation/sensitivity. `rendered/`has13pagePNGs;
temporaryPyMuPDF was used only forreading. No PDFauthoring or OCR claims.
The reconciliation command is in trackedcheckpoint. `verification.json` checks
14sourcecells/13uncensoredmaterialestimates,2flaggedconversions,2case/sex mappings,
4adoptedpairdecisions,3arithmetic scenarios,25preservedbounds and45hashes.
These verify internal consistency and retained values, not independent source
review. Week-normalization change separately passes1076pipelinetests,299analysis
tests andpipelineRuff. Remaining14ratcases,22prioritypairs,primarylineage and
independent review remain open.
