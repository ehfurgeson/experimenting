# Structural screening and reviewed labels

[Component quickstart](../README.md) · [Repository documentation](../../docs/README.md)

Commands below run from the repository root. Real-data examples require the local inputs described in the [data guide](../../docs/data.md).

## Structural evaluation ordering

`structure_models.evaluate` sorts eligible unique canonical structures before
splitting or fitting. Reordering the same compound records preserves the model
report, scaffold assignments, probabilities and exported out-of-fold row order
in the same locked environment. When several compound IDs share a structure,
the lexicographically smallest ID represents it; conflicting known target
labels still raise `ValueError`. Alias records must contain consistent chemistry.
This does not make different dependency versions numerically identical or
normalize tautomers, salt parents or stereoisomers.

Run the focused checks with
`uv run --project analysis pytest analysis/tests/test_structure_models.py -q`.


## Structural analysis environment

The locked analysis environment includes RDKit (SMILES chemistry, Morgan
fingerprints and the bundled Ertl SA scorer) and scikit-learn (fold-local
preprocessing, PCA and regularized classification). These dependencies belong
to analysis; cached toxicity retrieval keeps its existing environment.
Run `uv sync --project analysis --locked` from the root, then
`uv run --project analysis pytest analysis/tests/test_structure_environment.py -q`.


## Formula composition

`formula.formula_features` returns distinct element count, total atom count,
counts and fractions for C/H/N/O/P/S/F/Cl/Br/I/B/Si, and other-atom count.
Only complete flat neutral formulas are accepted, including repeated tokens.
Missing formulas have `missing` status; invalid symbols, charges, isotopes,
groups and hydrate notation have `unsupported` status and all-null features.
Unsupported inputs are retained for review. Formula describes composition;
isomers can share every formula feature.
Run `uv run --project analysis pytest analysis/tests/test_formula.py -q`.


## Structural screening descriptors

`structure.structure_features(smiles)` derives formula composition, RDKit
molecular weight, Crippen logP, TPSA, donors/acceptors, rotatable bonds, rings,
fraction sp3, a radius-2 2048-bit chiral Morgan fingerprint, canonical SMILES,
InChIKey, Murcko scaffold and bundled Ertl synthetic accessibility (1 easy–10
hard). Identity strings are audit keys, never numeric predictors.
Single-component carbon structures are supported; missing/invalid SMILES,
mixtures, radicals and unsupported chemistry retain status and null features.
No largest-fragment selection or salt neutralization is implicit.

`screening_rules` counts Lipinski violations (MW >500, logP >5, HBD >5,
HBA >10) and **Tice-inspired proxy** violations (MW outside 150–500, logP
>3.5, HBD >3, HBA outside 2–12, rotatable bonds >12). Boundaries are inclusive.
These use RDKit definitions, not the original paper's descriptor calculators.
The proxy ranges follow the primary [2022 screening study](https://www.mdpi.com/2073-4395/12/7/1635);
see [Tice's original paper](https://doi.org/10.1002/1526-4998(200101)57:1%3C3::AID-PS269%3E3.0.CO;2-6).
They are descriptors, not activity labels, safety tests or hard filters.
Run `uv run --project analysis pytest analysis/tests/test_structure.py -q`.


## Reviewed compound labels

`labels.attach_labels(compounds, labels)` validates independent natural-origin
and herbicidal-activity records keyed by unique `compound_id`. Optional CSV
fields are `natural_origin` (`natural`, `synthetic`, `unknown`),
`origin_reference`, `herbicidal_activity` (`active`, `inactive`, `unknown`),
`activity_reference`, `activity_context`, and `activity_policy`.
Known origin needs a citation. Known activity needs a citation, assay context
(species, dose, duration and endpoint) and a shared reviewed policy identifier.
A negative means experimentally inactive under that policy, not universally
nonherbicidal. Missing/unknown labels remain null. Natural means documented
natural occurrence, independent of manufacturing route.

Unknown fields, orphan/duplicate IDs, invalid values, conflicting labels for
identical structures and mixed activity policies raise `ValueError`. References
are required text; the validator does not verify their scientific conclusions.
Selection membership is a separate diagnostic target; no selection category
supplies activity or origin ground truth automatically.
Run `uv run --project analysis pytest analysis/tests/test_labels.py -q`.


## Expanded activity cohort preflight

New compounds do not fit the frozen 154-ID proposal validator. Inspect a new
single-policy cohort without fitting or fetching data:

```bash
uv run --project analysis --locked python analysis/activity_preflight.py \
  --compounds YOUR_WORK/compounds.csv --labels YOUR_WORK/labels_ONE_POLICY.csv \
  --holds YOUR_WORK/identity_holds.csv --holds YOUR_WORK/additional_holds.csv \
  --output analysis/outputs/NEW_PREFLIGHT_DIRECTORY
```

Compound CSV/Parquet inputs use the same identity checks as `screen.py`. Labels
must have exactly the seven review columns; missing compound labels remain
unknown. All duplicate/orphan IDs, conflicting canonical labels and mixed known
activity policies fail. Supply at least one hold CSV with `compound_id` (a
header-only file explicitly represents no holds). Each listed ID is treated as
held regardless of other columns; supply current unresolved holds only. Include
the adoption-ledger source gaps as well as the original global identity audit.
Known activity on a held ID or its canonical alias fails. Holds outside the
input cohort are reported; absent held structures cannot be compared to aliases.
Holds are caller-supplied, hashed inputs, not independently verified approvals.
Input hashes are captured before reading and checked again after inspection.
If compounds, labels or holds change during the check, the command fails before
creating output rather than attributing results to a different input version.

The fresh output directory contains `support.csv` with class/scaffold counts and
lower-bound deficits for all four representations, `members.csv` with exclusions
and deterministic canonical representatives, `folds.csv` with actual train/test
membership when supported, and `manifest.json` with input/code/lock/product hashes
and package versions. Five-fold grouping and seed match the screening workflow;
`supported` means both classes occur in each actual partition. No estimator is
fitted, no feature-variation gate is checked, and scientific approval is not
verified. Five class-bearing scaffold groups per class are necessary but not
sufficient. Canonicalization does not normalize tautomers or salt parents.

Focused checks: `uv run --project analysis --locked pytest
analysis/tests/test_activity_preflight.py -q`.

## Scaffold-held-out structural models

`structure_models.evaluate(rows, target, representation)` compares `formula`,
`descriptors`, `morgan`, and `combined` chemistry representations. Formula-only
models test whether elemental composition helps discriminate the selected
groups; they still need valid structures for scaffold assignment.
The estimator uses training-fold median imputation, training-constant removal,
standardization, PCA retaining 95% training variance, and L2 logistic regression
(C=1, balanced class weights). All settings are fixed in advance. No toxicity,
availability flag, ID, source or group label enters the predictor matrix.

Deterministic five-fold stratified group validation keeps each Murcko scaffold
in one fold. Identical canonical structures count once per target; conflicting
targets raise `ValueError`. Missing labels and unusable structures are excluded
with counts. Each class needs five compounds and five scaffold groups, and each
actual train/test partition must contain both classes. Otherwise results retain
an explicit support status, null metrics and no fitted model. Constant training
features yield `no_training_variation`; invalid configurations raise `ValueError`.

Results include out-of-fold predictions, confusion counts, balanced accuracy,
ROC-AUC, average precision, precision/recall, accuracy and a majority baseline
fitted independently in each fold. A separate full-sample estimator is available
only after evaluation succeeds. Its scores are exploratory and uncalibrated;
no model-selection search, external validation or reliable performance claim
is implied. Scaffold partitions are stricter than the old random splits, but
are not proof of prospective generalization.
Run `uv run --project analysis pytest analysis/tests/test_structure_models.py -q`.


## Offline structural screening workflow

Run independently of the toxicity presentation, using a fresh output directory:

```bash
uv run --project analysis python analysis/screen.py \
  --compounds analysis/data/compound_traits.parquet \
  --output analysis/outputs/structure-review
```

Inputs may be CSV or Parquet and require unique nonempty `compound_id` values.
SMILES is read from `canonical_smiles`, `smiles`, or `connectivity_smiles` in
that priority order. `chemical_group` supplies only the selection diagnostic.
Optional `molecular_formula` and `inchikey` are checked against derived chemistry;
conflicts get `identity_mismatch` and are excluded from modeling but retained in
exports. Formula model predictors use the formula derived from SMILES, ensuring
consistent features across cached and new compounds. Missing cached descriptors
are not needed; all chemical predictors are computed locally.

Add `--labels reviewed_labels.csv` to evaluate reviewed activity and origin.
Use the generated `label_review_template.csv` as the schema, preserving existing
reviewed records separately (the template is intentionally all unknown).
Add `--candidates natural_candidates.csv` for new compounds with their own IDs
and SMILES. Candidate scores use only reviewed activity models, never selection
models. Scoring requires successful scaffold validation but is still exploratory;
no automated “performs well” threshold or deployment approval is implied.
Identical labeled structures get `already_labeled_structure`. Scores include
maximum training Morgan Tanimoto similarity and whether the scaffold was seen;
these are context indicators, not validated applicability cutoffs. Invalid or
unsupported candidates and unavailable activity models produce explicit status
rows with null probabilities. Candidate IDs must be disjoint from training IDs.

Products under `--output`:

| File | Contract |
|---|---|
| `structural_features.parquet`, `.csv` | Every input compound, status, identity checks, structural features and labels; fingerprint list in Parquet only |
| `structure_models.csv` | Twelve target/representation reports, including unsupported targets |
| `out_of_fold.csv` | Held-out predictions, labels, scaffold, fold and fold-specific baseline |
| `label_review_template.csv` | Unknown-label review worksheet keyed by compound ID |
| `candidate_features.parquet` | Every candidate and computed features, when candidates are supplied |
| `candidate_scores.csv` | Candidate/representation activity scores or explicit blocked states |
| `manifest.json` | Input/code/lock/product hashes, package versions, settings and reports |

The command never fetches data. It rejects nonempty output directories and
output ancestors of input paths with `ValueError`, preventing stale products or
source overwrites. Inputs and the existing presentation outputs remain intact.
Run `uv run --project analysis pytest analysis/tests/test_screen.py -q`.


## Complete formula identity checks

`formula_composition` preserves every parsed element in a canonical audit string.
Formula identity comparison uses that string, including uncommon elements, rather
than the reduced numerical feature vector. This distinguishes Ge from Sn even
though both contribute to the same `other_atom_count` predictor. Equivalent
repeated tokens compare equally. The audit string never enters model features.
Run `uv run --project analysis pytest analysis/tests/test_screen.py -q`.


## Compound expansion sources

[Compound expansion evidence](compound_sources.md) records checked
acquisition routes for HRAC/WSSA herbicides, COCONUT, LOTUS and KNApSAcK natural
products, plus ChEMBL/PubChem plant-bioactivity leads for real positive/negative
labels. Database occurrence and herbicidal activity stay separate. Broad
natural-product ingestion remains deferred until reviewed activity labels and
independent validation support meaningful screening.


## Researcher label handoff

The [compound label research guide](label_review_guide.md) explains the
154-compound ChEMBL worksheet, independent origin/activity labels, required
citations and assay context, policy decisions, conflicting outcomes and schema
validation. It maps each label row to frozen measurements and structures and
provides a compound-by-compound research workflow. The local handoff pack under
`analysis/outputs/chembl-researcher-handoff-2026-10-29/` contains evidence packets,
a navigation index, an unchanged working label copy, an observation-level log
and an unapproved policy draft. It supplies research context without assigning
scientific labels or changing the frozen template.
