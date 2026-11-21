# Structural analysis policies

## Accepted-data experiments

The user's 17 November 2026 continuation explicitly accepts all acquired data and
authorizes full experimental freedom. The [accepted-sprint workflow](accepted-sprint.md)
implements a separate experimental scope rather than rewriting prior evidence.
Within that scope, source-form, context and independent-review holds no longer
block experiments. Accepted assumptions remain machine-readable alongside original
source fields. Unknown numerical outcomes are not invented, censoring remains
explicit and measured versus teacher-derived targets remain distinguishable.
Exploratory pooled plant models and alternative split sensitivities are authorized;
their evaluation must report actual study/chemical overlap and endpoint context.
The earlier workflow policies below continue to describe their original releases.

Topic index (policy rationale; workflow commands live in the component guides):

- [Source-identity holds](#source-identity-holds)
- [Analysis dependencies](#analysis-dependencies)
- [Formula completeness](#formula-completeness)
- [Structural heuristics](#structural-heuristics)
- [Independent origin and activity](#independent-origin-and-activity)
- [Dimensionality reduction and validation](#dimensionality-reduction-and-validation)
- [Offline screening products](#offline-screening-products)
- [Complete composition identity](#complete-composition-identity)
- [Canonical evaluation ordering](#canonical-evaluation-ordering)
- [Structural stress comparisons](#structural-stress-comparisons)
- [Frozen evidence review exports](#frozen-evidence-review-exports)
- [Feature-block comparison controls](#feature-block-comparison-controls)
- [Inner scaffold selection of regularization](#inner-scaffold-selection-of-regularization)

## Analysis dependencies

Chemistry and machine learning dependencies live in the analysis environment.
The retrieval package does not require RDKit or scikit-learn. The bundled RDKit
SA scorer includes its fragment score data; runtime does not download models.
The locked environment test executes both chemistry and PCA operations.

## Formula completeness

Flat neutral formulas are parsed in full before any feature is emitted. All
118 element symbols are recognized, with a fixed common-element feature list
and an aggregate for other atoms. Unknown or unsupported syntax is not repaired
or partially interpreted. Zero means an element is absent from a valid formula;
null means composition is unavailable. Formula features cannot distinguish
connectivity, origin, herbicidal activity or stereoisomers on their own.

## Structural heuristics

Descriptors are recalculated from SMILES consistently for training and future
candidates, without toxicity, source-coverage or database identifiers as inputs.
Lipinski concerns oral drug absorption; it is retained as an exploratory
feature. Tice addresses agrochemical transport and whole-organism activity,
not demonstrated herbicidal action. Published implementations differ in logP
and hydrogen-bond definitions; our thresholds are explicitly a named proxy,
not a reproduction of the original Tice calculation. SA is the RDKit bundled
Ertl–Schuffenhauer fragment/complexity heuristic, not a synthesis route, cost,
yield, availability or sustainable-manufacturing prediction. No threshold is
used to discard candidates.

All acyclic compounds share one scaffold group, conservatively preventing
acyclic analogues crossing folds. Salts/mixtures remain review rows; curated
parent normalization is future work. No tautomer normalization is claimed.
Charged structures may yield unsupported flat formulas while retaining usable
structural descriptors. Formula and structure statuses remain independent.

## Independent origin and activity

Natural occurrence and herbicidal action overlap. A natural herbicide is both
natural and active; a mutually exclusive herbicide/natural label discards this
fact. Existing selection membership remains a diagnostic of curation, not
proof of herbicidal activity. Reviewed positives and explicit tested negatives
must follow one activity policy. Unknown activity is excluded from supervised
training; missing evidence never supplies a negative. Citations and context
are mandatory but need human scientific review before training: schema
validation alone cannot establish comparable assays or a meaningful threshold.
Conflicting identities/labels must be reconciled explicitly, never last-write-wins.

## Dimensionality reduction and validation

PCA retains 95% variance using only training rows. Formula, descriptor and Morgan
ablations expose whether elemental composition or connectivity supplies useful
signal; the combined model is not automatically preferred. PCA may discard
low-variance activity signal and is not supervised feature selection. Fixed
L2 regularization and balanced class weights limit model flexibility without
searching this small selection for favorable hyperparameters. Standardizing
Morgan bits gives rare substructures more weight; compare ablations rather
than interpreting PCA directions as causal chemistry.

Scaffolds, including the single acyclic group, never cross evaluation folds.
We do not fall back to random splitting when scaffold support fails. The split
algorithm may fail the per-fold class-support guard even when another partition
exists; this conservative state is reported rather than cherry-picking seeds.
Identical canonical structures count once; no broader tautomer, salt-parent or
stereoisomer equivalence is inferred. Every reported metric comes from held-out
rows; the separate full-data fit never contributes evaluation predictions.
Candidate scores need external validation and calibration before deployment.

## Offline screening products

Structural analysis consumes cached traits or direct structure lists without
requiring toxicity or retrieving anything. It writes a fresh output directory
and hashes inputs, source code, dependency lock, versions and products. The
source formula and InChIKey are audit checks, not extra identifiers masquerading
as descriptors. Conflicting identities remain visible and cannot train models.
A compound without valid SMILES remains a review row; formula-only validation
still needs a structure to define its scaffold.

Candidate scoring is restricted to reviewed activity fits after held-out
validation succeeds. We make no automatic performance acceptance claim and do
not persist pickled estimators. Every rerun fits from explicit hashed inputs.
Uncalibrated scores and nearest-neighbor/scaffold context are exploratory; low
similarity, new scaffolds and biased training selections require follow-up.
The default directory stays under ignored analysis outputs. Full database
snapshots and generated products must not be committed.

## Complete composition identity

Predictor vectors intentionally aggregate uncommon elements; their equality
cannot establish formula identity. Identity checks use complete canonical
composition, distinct from model features. This preserves all 118 supported
elements in auditing without inflating the fixed common-element predictor list.

## Canonical evaluation ordering

Structural evaluation orders unique canonical identities lexicographically
before scaffold splitting and every fitted transform. The smallest compound ID
represents same-structure aliases, so input traversal does not choose the audit
identity. Conflicting labels remain errors. This makes equivalent reordered
inputs produce the same evaluation evidence within the locked environment,
including floating-point predictions and exported row order. A fixed random seed
alone does not establish this ordering contract.

This assumes alias chemistry was prepared consistently; it does not reconcile
manually supplied conflicting descriptors or infer broader chemical equivalence.
Input hashes still describe the exact files, so reordered CSVs retain distinct
manifest hashes. Existing generated results require an explicit rerun to adopt
canonical ordering; they are never rewritten automatically.

## Structural stress comparisons

Model representation comparisons use a shared formula-eligible cohort so that
chemistry exclusions cannot silently change the denominator between models.
Canonical identity deduplication and target conflict validation occur before
label shuffling. All four representations receive the same permuted target
vector for each recorded seed; transformations and fitted models are refitted
inside every evaluation fold. Unknown labels remain excluded.

The diagnostic matrix is fixed: five-fold common cohort, three-/ten-fold
sensitivity, removal of the largest scaffold group, then a specified number of
shuffled-label controls. It does not search seeds or choose the most favorable
partition, representation or score. Empty and unsupported cohorts retain explicit
status rows. The largest scaffold is selected by count with a lexicographic tie
break; that group's omission diagnoses composition sensitivity, not external
performance on the excluded chemistry. Controls are descriptive and no empirical
p-value is computed from a small or incomplete permutation set.

These checks cannot repair selection bias or supply missing reviewed activity
labels. Different fold counts change both training size and validation grouping;
variation between them is a sensitivity result, not a confidence interval.
Generated diagnostics remain local and include input, code and environment hashes.

## Frozen evidence review exports

Assay review material is rebuilt from validated raw snapshots rather than
untracked preparation scripts or previously generated tables. Source identity,
UTC retrieval time, one database version, complete page counts and globally
unique activity IDs are required before publication of any export. Consumed
bytes are hashed before parsing. Every activity retains its complete raw JSON
record alongside selected readable columns, so unknown fields and missing versus
numeric values remain recoverable. The raw snapshot path/hash also references
the complete assay and publication records.

A source molecule ID supplies one candidate. Missing structures can be enriched
from a consistent available record for the same ID; conflicting nonempty SMILES
are rejected rather than chosen by traversal order. No chemical normalization
or cross-ID structure merging is inferred. Multiple assay observations remain
separate rows. Missing/invalid structure strings stay in the review pool for the
existing structural preparation stage to assess.

Review evidence and supervised labels remain distinct. A generated worksheet
starts with unknown activity/origin, blank citations and no activity policy.
No source value, inequality, comment, citation or assay name is automatically
converted into a known training label. CSV blanks have no scientific meaning;
the raw record retains the original null/type information. Schema and snapshot
validation cannot establish comparable biology or confirm publication methods.
Single-version checking does not imply that separately retrieved API responses
form a transactional snapshot. Filesystem failures may leave partial exports;
only a completed, hash-verified manifest identifies a finished review directory.

## Feature-block comparison controls

Structural ablations fix the eligible cohort and outer scaffold partitions
before comparing feature combinations. Formula eligibility supplies the common
chemistry boundary; every remaining predictor must be finite. No imputation,
random-split fallback or representation-specific row filtering is allowed.
Canonical identity deduplication does not infer broader chemical equivalence.
All four original baselines use their existing scaled PCA/logistic-regression
settings. New profiles change only included blocks and which blocks receive PCA.

Preserving formula outside PCA is tested both with the remaining descriptors/
fingerprints projected jointly and with PCA applied only to fingerprints. A
formula/fingerprint-only block profile separates that question from descriptors.
Each branch fits exclusively on outer training compounds; held-out transforms
use those fitted parameters. Preserved raw features are standardized, including
constants that become zero; projected blocks require training variation. No
profile silently drops a failed fold or chooses another seed.

Dimensions, training scores and held-out scores are recorded to expose the
tradeoff in retaining raw features. These profile changes can alter feature
weighting as well as information retention; a score change alone does not
establish that PCA discarded causal biological signal. No best-profile search,
production replacement, full-data scoring model or activity-validation claim
is performed by this diagnostic command.

## Inner scaffold selection of regularization

Regularization experiments reserve the same five outer scaffold folds for
assessment and use three inner scaffold folds within each outer training set.
All preprocessing is fitted inside the inner training partition before testing
C. Reusing its transformed arrays across C is valid because the feature
transformation has no dependence on C. Each inner fold contributes equally to
mean balanced accuracy; a fixed 1e-12 tie tolerance favors stronger regularization.
The fixed grid spans C=0.01 to C=100 and is not extended after viewing outer scores.

Every outer fold receives its own C, refitted using only outer training data.
There is no global C chosen from outer results, random-split fallback, seed
search, imputation or replacement of the production model. All inner candidate
scores remain available for audit. Unsupported inner class/scaffold partitions
invalidate that nested comparison, and failed projected training variation also
prevents partial outer prediction output.

Nested selection protects assessment from C tuning; it does not turn comparisons
of nine profiles on one purposive selection into independent model confirmation.
A grid-boundary selection does not establish an optimal C beyond that grid.
Differences from fixed-C results can also reflect selection variability in small
inner samples. Activity prediction still requires its own reviewed labels and
independent biological validation.

## Dietary reference candidates do not supply plant-negative truth

The 2026-11-04 dietary-source pilot retains source food-use references and
machine-checked PubChem identities separately from researcher-reviewed exposure
and activity decisions. Candidate generation may use common food/nutrient names;
CID/SMILES/InChIKey values must come from saved authoritative identity responses.
All model targets remain null. Food use, lack of a warning, GRAS status and human
consumption cannot be promoted automatically to general nontoxicity or tested
plant inactivity. Caprylic/capric acids provide a concrete food-use/herbicide
counterexample. Preserve holds and overlap flags, and require versioned human
review before using these candidates as biologically labelled controls.

## Automated review remains a triage layer

`dietary-triage-v1` can prioritize candidate review from saved food-use documents,
explicit GHS codes, bounded human-toxicity/interaction text matches and dated
curated agency-source leads. A provisional shortlist is permitted as a lower
review-burden category; it must not become a safety or activity training label.
GHS handling hazards, dietary exposure, susceptible populations and plant response
remain separate axes. Missing sections remain gaps, contributor classification
conflicts remain visible, and text matches have no inferred polarity or causality.
Preserve original holds, overlaps, human decisions and all source snapshots.
Warning triggers, ADIs and supplement cautions retain distinct numeric contexts;
none supplies a universal consumable-dose or plant-negative threshold.

## Source-identity holds

A source-to-structure conflict takes precedence over an older conditional activity
scenario. Preserve the original observation and historical scenario, export an
explicit hold overlay, and keep the current accepted activity unknown. Matching
formula or matching biological band is insufficient to resolve molecular identity.
The 5 November 2026 Li 7b discrepancy motivates this guard; it is not an approved
structural correction. An illustrative alternative must never inherit the response.

A proposal checker enforces frozen audit holds before activity assignment; passing
its schema/cohort checks does not approve policy or evidence. Resolution requires
source drawings/SI, a recorded human decision and a new versioned correction/audit.
The generic label importer is not a sign-off service and does not automatically
consult local holds. See the [release contract](verification-release.md).

## Weekly pilot acute LD50 policy — 2026-11-10

Use explicitly measured acute rat oral mg/kg LD50, approved EPA identities and
one median of retained exact observations per compound for the bounded pilot.
Pooled linear-interpolated tertiles are exploratory cohort-relative bins, preserving
ties and reporting collapsed cutoffs. Censored values remain separate. Broad
mammalian availability policies remain unchanged. Group membership requires
independent origin/activity review; source selection and dietary status cannot
establish negative activity. See [pilot contract](weekly-pilots.md) for duplicate
handling, provenance and interpretation limits.


## Separate bulk experimental and external-model releases (2026-11-12)

The [A/B protocol](modeled-evidence.md) retains measured outcomes and outside-model
estimates in separate physical tables and target cohorts. Bulk provider identities
are provisional and cannot alter approved crosswalks or human labels. Source
references and repeated consortium outputs are not independent studies or votes.
Embedded teacher experimental values require original-source review before A
admission. Unknown teacher overlap allows agreement analysis, not independent
validation. The first release uses structure-derived features; a both-X-and-y
measured cohort remains unsupported. Combined pathway C requires a later design
decision after separate evaluation, and no combined fit is authorized by this
workflow.

## Import inventory counts

Delimited-table counts exclude the header and report blank records and
nonblank records with unexpected widths separately. Workbook counts include
headings and metadata rows and exclude cells containing only formatting.
An archive member name includes its container chain for traceability.
Recorded use is assessed from repository evidence, with version differences
and direct use of local bytes assessed independently.

## Public toxicity reconstruction

The public-only reconstruction uses the same exact-dose and CATMoS aggregation
as the frozen release. It preserves source qualifiers and separates the
provisional measured A targets from the CATMoS teacher B targets. No modeled
values enter the A targets. The reconstruction has no original selection,
manually reviewed identity decisions, or CTX TEST cache.

## NICE context linkage

Exact linkage uses a valid single-component full key and holds conflicts with
ICE identifiers. An unambiguous DTXSID can supply an identifier-only lead when
the source omits structure. Mixtures and unreadable or conflicting source
structures stay on hold. The descriptive reader preserves unevaluated
expressions, cached cells and populated unheaded cells as tokens. The original
acute-oral parser retains its stricter admission rules. These workbook matches
are descriptive evidence and preserve the source-specific endpoints and units.

## Standalone ECOTOX discovery

The ecological source inventory can run without a local adopted-label bundle.
In archive-only mode all observations retain their review status and refer
back to the native test, species, result and reference. No adopted policy
or training label is reconstructed from the archive.

## NPASS production context

The four production tables keep producer, inducer, elicitor, engineering and
symbiont fields under their original source definitions. A successful join
requires an eligible NPASS full structure in the requested cohort. The result
retains the provenance and association type and leaves natural occurrence,
independent corroboration and activity for separate review.

## COCONUT cohort-indexed validation

The optional cohort-only scan limits recomputation to the provider connectivity
blocks under consideration. Any eligible full-key match requires agreement
between the provider key and recomputed key. Skipping other provider blocks
preserves eligible matches while leaving those records unqualified.

## ToxValDB source subsets

Endpoint screening accepts an explicit, unique subset of version-pinned
ToxValDB workbooks. Each workbook keeps its native evidence and table locator.
Adding source tables leaves the endpoint and study-lineage gates in place.

## NICE archive evidence roles

ClassyFire supplies predicted structural taxonomy for matched identities.
cHTS counts are coverage indexed by DTXSID and endpoint. A count says
nothing about response direction or assay quality. Interpreting activity
requires reviewing the assay, flags, cytotoxicity and chemical QC together.

## Public panel identity and scoring

The public HRAC workbook provides herbicide-use groups. Literal names
and explicitly separated aliases link to source structures, retaining
ambiguities and original tested-form review status. For CATMoS name links
the input structure precedes the standardized QSAR parent. Reviewed panel
rows additionally require agreement between the recorded and recomputed
full key. Forest outputs use group-held-out predictions for training-cohort
members and clearly labeled exploratory full-fit estimates for other rows.

## Public evidence intersection

The plant subset uses an unambiguous source DTXSID link, a positive scalar
concentration, an available control context and an explicit response scale.
It assigns the existing high and low response bands to eligible ECOTOX points
with endpoint NR. Threshold-derived endpoints such as NOEC, censored responses
and bounds on exposure remain available in the source inventory. The bins on
EPA leads describe qualifying exact source reports with conflicts retained.
Catalog, taxon/reference association and herbicide use remain separate evidence.
Structural profiles are descriptive and use each full key once within a group.
