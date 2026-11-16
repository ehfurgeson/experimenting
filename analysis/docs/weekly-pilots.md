# Weekly research pilots

These workflows advance the two tracks in the local research goals. They produce
exploratory comparisons and review evidence, preserving the distinction between
source selection and independently reviewed biological groups.

## EPA-first acute rat oral LD50

From the repository root, use an empty output directory outside input directories:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked python analysis/weekly_toxicity.py \
  --hazards experiments/data/epa_hazard.parquet \
  --crosswalk experiments/data/epa_identity_crosswalk.parquet \
  --traits analysis/data/compound_traits.parquet \
  --output analysis/outputs/weekly-toxicity-<date>-<run>
```

Inputs use the existing EPA hazard/crosswalk and compound-trait contracts; the
hazard table is inventoried before selection metadata is attached. Only approved
compound/DTXSID pairs enter comparison. The existing cache is selection-conditioned;
its source-first traversal does not establish population-wide discovery. Inventory
rows outside the supplied selection are counted explicitly and retained unresolved.
Optional `--labels` accepts the existing seven-column reviewed-label file, requiring
one activity policy. Supplying labels asserts their independent approval; provisional
review exports must never be supplied. Source groups alone leave biological labels
unknown. No API key or live requests are used.

`evidence.csv` retains every hazard row with exclusion/duplicate/exact/censored
status, original context JSON and citation. Eligibility requires explicitly measured
experimental acute rat oral LD50 with compatible mg/kg units, positive finite value,
valid qualifier and no recognized formulation/mixture flag. Unknown study type is
excluded. Other mammalian species, daily doses and predictions are excluded.

Duplicates require the same compound, reference, exposure context, qualifier and
normalized value. DOI is preferred over reference text; unreferenced records collapse
only when identical within a source. Different-reference duplicates cannot be
resolved automatically. Distinct exact values are retained with a discordance flag;
compound medians, minima/maxima and record counts expose their spread. These medians
are descriptive across the retained acute contexts, not meta-analysis estimates.

`compounds.csv` assigns each exact-value compound one vote in pooled linear
interpolated tertiles: low <= q1, medium q1 < value <= q2, high > q2. Ties stay together,
so groups need not have equal sizes. Identical cutoffs are reported explicitly;
no exact results yields empty cutoffs. Low LD50 means greater acute toxicity, not
low hazard. Censored bounds remain in the evidence export and compound counts but
never estimate cutoffs or enter primary bin denominators. Cutoffs describe this
cohort only and are not regulatory categories.

`groups.csv` supplies exact-compound denominators/proportions; the manifest records
policies, input/code/lock/output hashes and source inventory counts. SVG figures and
an interactive HTML distribution show the preliminary comparison. Selection groups
remain explicitly named `selected_herbicide` and
`unreviewed_natural_product_selection` unless reviewed origin/activity support
`natural_active` or `natural_tested_low_response`.

## Completion boundaries

A literature lead is not an accepted activity label. Dietary benignity is not tested
plant inactivity. The existing five-fold class/scaffold checks gate any biological
model; unsupported cohorts produce a readiness gap rather than a favorable fallback.
The model diagnostics contract is in [diagnostics-review.md](diagnostics-review.md).
Research bundles remain ignored and existing frozen results are never overwritten.

## Literature-led structural pilot

The curated discovery resource `analysis/resources/weekly_literature.json` records
15 names from four primary publications, with source locators and assay-specific
caveats. It is an AI-assisted screen, not an approved label file. The 2024 field
study provides context-dependent low-response leads; absence of an accepted
plant-negative group is reported explicitly. Citral mixtures are excluded from
this single-structure pilot. Natural occurrence mentioned by an efficacy paper
still requires independent isolation/structure review.

Acquire new PubChem name resolutions/validated properties and primary-source pages
explicitly, preserving per-request status (including publisher 403 responses):

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked python analysis/weekly_literature.py \
  fetch --snapshots analysis/outputs/weekly-literature-sources-<date>-<run>
```

Then build offline into a new directory:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked python analysis/weekly_literature.py \
  build --snapshots analysis/outputs/weekly-literature-sources-<date>-<run> \
  --selection analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet \
  --output analysis/outputs/weekly-literature-<date>-<run>
```

Database SMILES/InChIKey agreement permits provisional descriptor calculations,
not source-identity or origin/activity approval. Unresolved identities remain in
`literature_evidence.csv` and are excluded from descriptors. All activity/origin
labels remain unknown. `source_packets.json` records publication-level context;
join using `source_id`. Preserve downloaded paper/SI files separately with URL,
retrieval time and hashes when automated HTML access fails.

Descriptor points and group medians/IQRs compare provisional literature identities
with supported unique selected herbicide structures. Exact full-key selection
overlaps are removed and listed in the manifest. Molecular weight is g/mol, logP
is RDKit calculated, TPSA is square angstroms, HBD/HBA are counts, and halogen
presence is binary (its mean is prevalence). Each descriptor supplies its own n.
The chart shows individual compounds with independent panel scales; the summary
CSV supplies medians and IQRs. This purposive comparison supports description,
not population inference or an accepted three-group biological claim. No biological
classifier is fitted by this workflow.

## Verified cross-track walkthrough

`weekly_report.py` verifies each upstream bundle's recorded research input/output
hashes before building a standalone HTML walkthrough, coefficient fold summaries,
model F1 figure and literature/LD50 and ECOTOX/literature overlap tables:

```bash
UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis --locked python analysis/weekly_report.py \
  --toxicity analysis/outputs/weekly-toxicity-<date>-<run> \
  --literature analysis/outputs/weekly-literature-<date>-<run> \
  --models analysis/outputs/weekly-models-<date>-<run> \
  --ecotox analysis/outputs/weekly-ecotox-<date>-<run> \
  --evidence analysis/outputs/weekly-literature-sources-<date>-<run> \
  --output analysis/outputs/weekly-research-<date>-<run>
```

Repeat `--evidence` for preserved PDF/source bundles and archived input-version
bundles. The latter may satisfy a historical **input** hash only when their
recorded output file reproduces the exact expected SHA256; such resolutions are
listed in the new report manifest. Output tampering is always rejected. Historical
code hashes remain separate from research-byte verification. New literature
acquisitions freeze `acquisition_resource.json` in their own snapshots directory,
so later source annotations cannot invalidate acquisition provenance.

The 10 November checkpoint includes a separately preserved acquisition resource
whose hash matches the earlier immutable manifest; later PDF annotations have a
new resource hash. The final walkthrough uses the `-final` synthesis and
`-reviewed` literature bundle; earlier pilot runs remain preserved. The report
summarizes selection diagnostics and pending biological review, not a completed
three-group activity model.

## Expansion: study reconciliation and LD50 sensitivity

`expansion_toxicity.py --baseline <weekly-toxicity> --ecotox <selected-ecotox>
--crosswalk <source-decisions.csv> --output <new-directory>` verifies both bundle
manifests and freezes the historical 1,080/3,400 mg/kg boundaries. It exports
individual censored-observation compatible bins, exact-value compound medians,
within-compound study ranges, context missingness and aquatic context admission
by measured/unmeasured and concentration-basis strata. No censored threshold
becomes a point estimate or a compound-median label. Scenario-specific tertiles
are separately named; no historical boundary is overwritten.

The documented-context sensitivity requires a reference, sex, strain and explicit
positive elapsed study duration. An empty subset is a supported insufficiency
result, not a reason to relax criteria. The historical exact, reviewed-duplicate,
unresolved-overlap-excluded and documented-context scenarios have independent
counts and denominators. No new canonical ECOTOX records enter rat oral estimates
until the source identity and rat oral study context are approved/eligible.

`study_overlap_review.csv` supplies DOI/exact-normalized-title plus chemical-hint
candidate pairs with separate species, route, endpoint, duration and result checks.
Equal values and shared papers do not prove study identity. No rows are collapsed
by default. Optional `--decisions <csv>` can exclude a duplicate only for an
explicit pair, retained member, `same_observation` decision, reviewer/date and
source reference; cross-source collapse additionally requires source identity
approval. Contradictory retention decisions fail. Review decisions are recorded
assertions rather than automatic verification of scientific approval.

The exported `study_overlap_review.csv` now carries each supplied decision's
state, retained ID, reviewer, date and reference. Unmentioned pairs remain
unreviewed. This allows `ecotox_comparison.py` to consume adopted decisions from
a newly built reconciliation bundle; older frozen queues remain unchanged.
No direct decision file is required by the downstream comparison. Rebuild the
reconciliation first when review changes. Duplicate pair IDs and contradictory
retain/drop chains fail before queue publication.

## Expansion: compound evidence and approval handoff

`evidence_review.py` uses the separate versioned
`analysis/resources/expansion_review.json`; the original pilot resource is unchanged.
The resource records 15 origin reviews, source locators, access limitations and
81 study/condition observations. Values transcribed from tables remain distinct
from qualitative author categories, ordinal bands and undigitized plots.
Solution/soil, species, dose, site, formulation, timing, controls and replication
remain observation-level fields. The recovered 1998 methods use three dishes of
20 seeds in solution and four cups of five germinating lettuce seeds in soil.
Source response figures are not automatically digitized into numerical labels.

Acquire sources explicitly with `python analysis/evidence_review.py fetch --output
<new-source-directory>`. It freezes the acquisition resource and logs each URL,
HTTP status, time, file hash and access gap. Build offline with
`python analysis/evidence_review.py build --literature <reviewed-weekly-literature>
--sources <source-directory> --holds <frozen-identity-holds.csv> --output <new-directory>`.
The locked analysis environment and repository-root working directory apply.

Products include compound packets, separate study observations, 32 origin/activity
approval worksheet rows, policy proposals, per-policy class/scaffold support,
database structure-reference drawings and an exact preserved identity-hold copy.
Drawings represent database SMILES, not verified original paper structures.
The seven-column `reviewed_labels.csv` remains entirely unknown and compatible
with existing label readers. The existing 154-compound validator is unchanged.
No source scraping, name agreement or proposal can assign scientific approval;
approval state edits in this proposal-building resource are rejected.

Proposed activity policies remain separate: 1998 lettuce 1 mM/six-day qualitative
response, 2020 Amaranthus one-day death efficacy, 2024 UPV four-week base-treatment
weed coverage, and 2015 pigweed injury. Per-policy support counts are hypothetical,
not validation results. No estimator is fitted. The 2024 low-response proposals
apply only to named formulation/site/dose conditions, not universal inactivity.
The sarmentine methods/table dose disagreement (10 versus 20 mg/mL) forces an
unknown activity proposal. Natural-occurrence leads distinguish primary isolation,
GC-MS characterization, abstracts, unresolved chemical form and source-identity
issues. Access failures and unverified spectra remain explicit review gaps.

## Expansion walkthrough

`expansion_report.py --ecotox <selected-bundle> --toxicity <sensitivity-bundle>
--review <compound-review> --sources <primary-source-cache> --cohort <frozen-cohort>
--output <new-directory>` verifies all five bundle manifests before synthesizing
`walkthrough.html`. It links the approval worksheet, source observations, compound
packets, complete ranked overlap queue and censored-bound bins. Aquatic estimates
are explicitly source-context matches with identity approval pending, separated
by exposure analysis. No source slots are described as independent experiments.

The report rejects input metadata claiming accepted labels or fitted biological
models: this expansion is a proposal/review handoff. Historical cutoffs and baseline
figures remain in their original bundles. Raw sources, unsuccessful publisher
responses and the original 1998 PDF remain preserved; byte verification is separate
from scientific source approval. The 11 November checkpoint uses the
`expansion-ecotox-2026-11-11-context-verified`, `expansion-toxicity-2026-11-11-final`,
`expansion-review-2026-11-11-verified` and `expansion-walkthrough-2026-11-11-verified` bundles.

The verified review adds explicit source-name structure reconstructions, source
locators and full-key comparisons, separate from original drawing/spectral review.
All 15 match the database identities. Any mismatch creates an identity hold and
forces both origin and activity proposals to unknown. Free-acid/ester, tested
formulation and source stereochemistry/analytical confirmation remain independent
review questions. The final source cache explicitly includes the original 2020
and 2024 efficacy PDFs as well as the recovered 1998 source and occurrence leads;
its acquisition resource is preserved separately from later annotations.

## Primary rat-source review follow-up

The [2026-11-12 source review](rat-source-review-2026-11-12.md) resolves two
pending result-cell mappings and adopts four experimental different-observation
decisions in a new reconciliation run. It keeps material and acid-equivalent
doses separate, flags native dietary metadata and two other source conversion
discrepancies, and retains the original 43 exact/25 censored baseline. Relaxed
mixed-basis sensitivities do not establish harmonized new admissions or ranks.
