# Preliminary automated dietary-candidate review

[Analysis](../README.md) · [Candidate sources](compound_sources.md#dietary-comparator-review-pilot--2026-11-04)

`triage_dietary.py` prioritizes the existing candidate review worksheet using
explicit, versioned rules and saved evidence. It does **not** assign safety,
natural-origin or plant-activity truth, train a model, or recommend consumption.
“Provisional dietary shortlist” means lower review burden within this bounded
screen. It does not mean benign at high doses, suitable as a plant-negative, or
free of warnings outside the scanned sources.

## Acquire and reproduce

From the repository root, using the locked analysis environment:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis python analysis/triage_dietary.py --review analysis/outputs/dietary-review-2026-11-04-final/review.csv --fetch --snapshots analysis/outputs/dietary-triage-sources-new
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis python analysis/triage_dietary.py --review analysis/outputs/dietary-review-2026-11-04-final/review.csv --snapshots analysis/outputs/dietary-triage-sources-new --output analysis/outputs/dietary-triage-new
```

The first command is explicit online acquisition. For each unique CID it requests
PubChem PUG View **Safety and Hazards** and **Toxicity**. It also retrieves one
food-use document per distinct source URL. The current eCFR pages blocked direct
automated access, so the acquisition deliberately requests official **2025 annual
CFR XML** from GovInfo for the relevant sections (volume 2 for part 168; volume 3
for the other pilot sections). FDA GRAS notices use their source HTML pages.
The annual edition is a food-use lead, not proof of current legal requirements;
check the current eCFR before accepting a decision.

Each numbered JSON snapshot retains the request key, URL, kind, UTC acquisition
time, HTTP status, complete response body and transport-error class where present.
HTTP retries handle transient errors. Explicit failures remain evidence gaps;
a failed individual request does not silently disappear or become “no hazard”.
An interrupted acquisition must be completed in a new directory or carefully
reconciled before offline analysis. The offline step requires the complete
expected key set, including failed responses, rejects duplicate/unknown keys and
mismatched URLs/kinds, and verifies successful PubChem record CIDs. Malformed
PubChem records, unrecognized food documents and absent sections remain gaps.
Nonempty output directories and output ancestors of inputs are rejected.
No source worksheet, snapshots, frozen outputs or human decisions are overwritten.

## Policy and evidence axes

The default [policy JSON](../resources/dietary_triage_policy.json),
`dietary-triage-v1`, contains a dated set of **curated primary-source leads** and
five lexical text screens. The curated summaries were checked against their
linked agency sources; they are authored review leads, not automatically extracted
medical conclusions. The live source fetch does not reacquire those supplemental
agency references; their summaries, URLs, checked date and contextual quantities
are retained separately in `curated_leads.csv` and the hashed policy file.

1. **Food-use support.** A successful official XML/GRAS document must be recognized
   and the compound name or declared alias found in its text. Fructose/HFCS and
   maltose/malt-syrup references remain `mixture_scope`. Name occurrence only
   confirms a named conditional-use lead: it does not adjudicate stereoisomer,
   actual dose, population, duration, occurrence or the full source conditions.
2. **GHS handling/systemic/aquatic axes.** Only explicit `GHS Hazard Statements`
   fields supply codes. Acute systemic, aspiration, mutagenic, carcinogenic,
   reproductive and target-organ code families trigger review. Reproductive-code
   suffixes such as H360FD are preserved. Skin/eye/respiratory handling and aquatic
   codes are reported separately. The complete code list and statements remain
   inspectable. Codes can be supplier/contributor reports with variable or minority
   classifications; contradictory “Not Classified” text does not erase a warning.
   These records do not establish dietary toxicity at an exposure or plant response.
3. **Toxicity text leads.** The five pattern groups scan only **Human Toxicity
   Excerpts, Populations at Special Risk, and Interactions** for serotonergic
   interactions, methionine/homocysteine terms, specific susceptible populations,
   organ-disease contexts and gastrointestinal tolerance. Matching passages are
   flagged for review regardless of polarity. A match may describe a null finding,
   a co-exposure, contamination, historical evidence, another species mentioned
   in the passage, or an unrelated context. No negation, causality, exposure or
   species inference is performed. Unmatched text is not automatically cleared.
4. **Known source/selection concerns.** Original holds and identity overlaps remain
   flags. Free fatty acids require separate review from dietary fats; organic
   acids require pH/concentration review; sugars need dose/anomer checks; polyols
   except glycerol receive dose-tolerance review. Existing identity agreement is
   required for the provisional shortlist.
5. **Population/dose-specific agency leads.** These include arginine supplement
   restrictions, phenylalanine/PKU, fructose/sorbitol susceptibility, lactose
   intolerance, polyol limits, xylitol dog toxicity and registered herbicide use.
   Contextual numbers are not combined or treated as equivalent safety thresholds:
   sorbitol 50 g/day and mannitol 20 g/day are US food-label warning triggers;
   erythritol 0.5 g/kg body weight/day is EFSA's 2023 ADI; arginine above 9 g/day
   is a specific adult supplement warning context. None is a recommended dose or
   a plant-inactivity threshold. See each policy entry's primary source and context.

## Triage precedence

| Category | Rule | Interpretation / next action |
| --- | --- | --- |
| `exclude_presumed_plant_negative` | Curated registered-herbicide-active lead | Caprylic/capric acid cannot be assumed inactive merely from food use; keep distinct dietary and plant questions |
| `priority_review` | Any hold, overlap, scoped-family/population flag, systemic GHS trigger or toxicity-text hit | Inspect exact source passages, compound form, dose and population; a flag is not proof of harm |
| `evidence_gap` | No priority flag, but food/hazard/toxicity support missing | Acquire evidence; do not interpret missing records as reassurance |
| `provisional_dietary_shortlist` | Named food-use lead, prior identity agreement, records/fields present and no policy trigger | Start human dietary-context review here; high-dose safety and plant activity remain unknown |

Priority flags take precedence over gaps, but `evidence_gaps` are always retained.
A zero count in the standalone gap category therefore does not imply complete
coverage. Numerical scores/probabilities were deliberately avoided: these rules
have not been calibrated against an adjudicated review set. No supervised safety
classifier or exhaustive literature review is implied.

## Products and review

- `triage.csv`: one row per candidate, triage category, reasons, flags, gaps,
  handling/systemic/aquatic codes, source coverage, next action and unknown safety/
  plant labels. Existing `decision`, `reviewer` and `decision_reference` fields
  are copied as human provenance; triage does not override them.
- `pubchem_extracts.csv`: source text, section/field, contributor/reference metadata,
  request URL and acquisition time. All selected toxicity information is retained;
  only the declared heading/pattern subset feeds lexical flags.
- `text_flags.csv`: exact unadjudicated matched passages and signal names.
- `curated_leads.csv`: authored agency-source summaries with dates, URLs and
  explicitly contextual quantities/units/types. These differ from automatic text hits.
- `README.md`: computed category counts, provisional shortlist and complete review queue.
- `manifest.json`: policy ID, counts, exact source/policy/code/lock/product hashes
  and dependency versions. A complete manifest identifies the finished output bundle.

All high-dose-safety and plant-activity output labels remain `unknown`. A human
must review exact identities, conditions, natural occurrence and primary evidence,
then sign a versioned decision copy under a declared policy. Provisional candidates
must not silently enter training. To claim tested plant inactivity, obtain suitable
plant assays. Evaluate sensitivity/specificity of the triage rules against a
researcher-adjudicated set before trusting them as a screening instrument.

Focused offline checks:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis pytest analysis/tests/test_triage_dietary.py -q
```

The [follow-up notebook](../../notes/notebooks/findings.py) displays the
frozen triage results, coverage gaps, source-linked leads and required decisions.
Its category filter narrows the review queue; the candidate selector displays
curated agency leads and the exact automatically matched passages separately.
The notebook verifies product hashes, cohort/category counts and the absence of
automatically accepted biological labels before showing the review. A missing
triage bundle stops only this optional section; the earlier model analysis can
still be read. The static HTML preserves the default view; Python-backed filters
require the live notebook.

The [human verification checklist](verification-checklist.md#b-verify-the-dietary-comparison-candidates)
specifies how to review the underlying sources and record exact identity,
occurrence, dose/population/time and restricted decisions. The local editable pack
is separate from the frozen triage and does not become a training input automatically.
