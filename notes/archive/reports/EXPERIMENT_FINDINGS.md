# Experiment findings: herbicide and natural-product traits

**Document status:** Historical scientific checkpoint, 2026-10-21. Reviewed for organization 2026-11-02.

Earlier acute-only selection/evidence findings; later seven-endpoint and structural checkpoints are in analysis/FINDINGS.md. Do not update old figures in place.

Current guidance: [topic note](../../current/project-state.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context.

Contents of the historical record:

- [The selection](#the-selection)
- [Identity review: 23 names needed a decision](#identity-review-23-names-needed-a-decision)
- [EPA identity: 136 of 176 compounds approved](#epa-identity-136-of-176-compounds-approved)
- [The headline finding: the gap is in measured evidence, not in anything else](#the-headline-finding-the-gap-is-in-measured-evidence-not-in-anything-else)
- [ToxCast: a difference in the assays, and a difference in the response](#toxcast-a-difference-in-the-assays-and-a-difference-in-the-response)
- [The aquatic endpoints are sparse in both sources](#the-aquatic-endpoints-are-sparse-in-both-sources)
- [The chemistry does differ](#the-chemistry-does-differ)
- [What the classifiers say](#what-the-classifiers-say)
- [What is not yet done](#what-is-not-yet-done)

Date: 2026-10-21. Scripts and data are in `experiments/` (gitignored).
For maintained reproduction commands use the [cached-analysis guide](../../../analysis/docs/cached-analysis.md); the figures below retain their original checkpoint context.

## The selection

**178 compounds: 62 herbicides and 116 natural products.** All 176 unique
queries were retrieved from PubChem with zero failures, and 176 resolved to a
CID with a full trait row.

- The herbicides come from the "Representative Herbicide(s)" column of
  `herbicide_target_tables/Herbicide target table - HRACdb.csv`, one row per
  compound, with its HRAC group.
- The natural products are the allelochemicals the Allelopathy book names
  explicitly, plus the four the professor asked for. The full provenance
  table, with the source line for every name, is in
  `notes/CURATED_COMPOUNDS.md`.

## Identity review: 23 names needed a decision

Twelve names were changed to a form PubChem resolves, four of them to an
explicit CID because the name is ambiguous, and **eleven named allelochemicals
have no PubChem record at all** and are outside the selection. Every retrieved
compound's InChIKey is in the trait table, so its identity can be checked.

## EPA identity: 136 of 176 compounds approved

| | herbicides | natural products | total |
| --- | ---: | ---: | ---: |
| approved | 49 | 87 | 136 |
| needs_review | 10 | 14 | 24 |
| unresolved | 1 | 15 | 16 |

The 24 review cases are almost all **connectivity-only matches**: the EPA
substance shares the connection layer of the InChIKey but not the full key, so
it differs in stereochemistry, tautomer, or protonation. The policy sends those
to review rather than approving them, which is why diclofop-methyl and
sethoxydim are not approved while pinoxaden is. The 16 unresolved compounds
have no defensible EPA identity, and 15 of them are natural products.

## The headline finding: the gap is in measured evidence, not in anything else

| Trait | Herbicide median | Natural-product median | 95% CI of the difference | AUC |
| --- | ---: | ---: | --- | ---: |
| PubChem annotations | 85 | 3 | [51, 95] | 0.81 |
| Complete extracted measurements | 3 | 0 | [2, 4] | 0.73 |
| EPA hazard records | 103.5 | 6 | [76, 128] | 0.89 |
| EPA hazard experimental records | 80.5 | 3.5 | [49, 100] | 0.84 |
| EPA distinct endpoints | 16 | 4 | [6, 14] | 0.82 |
| EPA distinct species | 5 | 2 | [2, 4] | 0.85 |
| EPA **measured** properties | 39 | 14 | [13, 41] | 0.65 |
| EPA **calculated** properties | 59 | 59 | [0, 1] | 0.58 |
| ToxCast assays with a result | 692 | 382 | [229, 353] | 0.82 |
| ToxCast target families | 38 | 17 | [13, 23] | 0.74 |

The clearest single result is the last pair of rows. EPA's **calculated**
properties are available for exactly the same number of compounds in both
groups, because a model computes them whether or not anyone has measured
anything. EPA's **measured** properties are nearly three times as common for
the herbicides, and the hazard records are more than an order of magnitude
more common. The difference between the two groups is not in the chemistry and
not in what is computable. It is in what has been measured.

## ToxCast: a difference in the assays, and a difference in the response

The herbicides are tested in nearly twice as many assays (median 692 against
382, AUC 0.82), and they reach 38 distinct target families against 17.

But the **number** of inactive assays is the same for both groups (147 against
134, p = 0.69). The difference is in how large a share of the assays each
group is tested in comes back inactive:

| | herbicide | natural product |
| --- | ---: | ---: |
| median inactive share of the assays tested | 0.226 | 0.316 |

The difference is -0.090 with a 95% interval of [-0.154, -0.017] and a
permutation p of 0.0035, and the AUC of 0.278 means a random natural product
has a *higher* inactive share than a random herbicide about 72% of the time.

**This is the most interesting result in the analysis, and it is also the one
that must be read most carefully.** Three explanations are consistent with
it:

1. The natural products are genuinely less active in the assays they appear
   in.
2. The herbicides are tested in a larger and more demanding assay panel, so
   the denominator of inactive results is wider.
3. Selection: a compound enters the panel because someone was interested, and
   the natural products that entered were often the more interesting ones.

The data here cannot separate those three. Distinguishing them needs either a
matched assay panel (the same assays for both groups) or a model that
conditions on which assays a compound was tested in. That is the natural next
experiment, and the trait table now has the per-compound assay counts to
support it.

## The aquatic endpoints are sparse in both sources

| Definition | PubChem, with data | EPA hazard, with data |
| --- | ---: | ---: |
| mammalian oral LD50 | 69 | 76 |
| fish LC50 | 8 | 0 |
| rainbow-trout 96-hour LC50 | 4 | 0 |
| Daphnia 48-hour EC50 | 0 | 0 |

EPA hazard adds mammalian evidence and no aquatic evidence: 5,742 of its
5,814 records for this compound set are mammals, 4 are fish, and 1 is a plant.
**A correction to the earlier reading of this analysis:** the aquatic
comparisons are sparse rather than empty. Four herbicides and four natural
products do have a fish LC50 in PubChem, and the earlier "empty" reading came
from looking at a median of a zero-or-one column.

The reason CompTox Hazard cannot fill the aquatic gap is visible in its
content: 5,454 of the 5,814 records do not map to the comparison rules at all,
because their endpoints are regulatory derived values rather than experimental
endpoints. The most common are ADI, BMDL, DNEL, DWEL, ESL, and drinking-water
guidelines. **The aquatic endpoints of this project need ECOTOX, not
CompTox**, because CompTox Hazard, as served for these DTXSIDs, is a
human-health record collection.

## The chemistry does differ

| Trait | Herbicide median | Natural-product median | 95% CI of the difference | AUC |
| --- | ---: | ---: | --- | ---: |
| Molecular weight | 275.7 | 174.7 | [64, 141] | 0.75 |
| Heavy atom count | 19 | 12.5 | [2, 9.5] | 0.69 |
| XLogP | 2.7 | 1.7 | [0.55, 1.5] | 0.70 |
| Complexity | 315 | 206 | [46, 194] | 0.65 |
| H-bond acceptors | 5 | 3 | [1, 3] | 0.67 |
| Rotatable bonds | 3 | 1.5 | [1, 3] | 0.64 |
| TPSA | 65.4 | 47.1 | [-0.5, 37] | 0.63 |

The herbicides in this selection are larger, more lipophilic, and more complex.
The AUCs are modest, so the two groups overlap substantially and no single
trait separates them. These are differences in *descriptors*, not in toxicity.

## What the classifiers say

Logistic regression on ten z-scored descriptors, stratified five-fold
cross-validation, fixed seed, majority-class baseline for comparison.

| Model | Accuracy | Baseline | Reading |
| --- | ---: | ---: | --- |
| Group from structure | 0.78 | 0.66 | The groups are structurally distinguishable, as expected. A sanity check, not a finding. |
| Comparable oral LD50 available | 0.62 | 0.61 | Structure barely predicts whether comparable evidence exists. |
| Any complete measurement | 0.64 | 0.57 | Slightly better than chance. |
| Any PubChem annotation | 0.76 | 0.76 | **No better than the baseline.** Structure does not predict who gets studied. |

The last row is the important one. A compound's size and polarity do not
predict whether anyone has published a toxicity annotation for it. What
predicts study coverage is being a registered pesticide, not being a particular
kind of molecule. A model that could predict study coverage from structure
would be a warning sign about the literature, and this one cannot.

## What is not yet done

- **The ToxCast difference is unexplained.** The inactive-share result is
  real and significant, and it has three competing explanations that this
  data cannot separate. A matched-assay analysis is the next step.
- **No comparison of toxicity distributions.** There is still almost nothing to
  compare: 69 compounds have a comparable oral LD50 and only a handful have an
  aquatic one.
- **The seven endpoint definitions are not yet implementable from this
  evidence.** The project notes name LD50, LC50, EC50, NOAEL, LOAEL, BMD, and
  BMDL. The pipeline supports the first three. NOAEL and LOAEL are common in
  the EPA hazard data but need their own endpoint family and unit policy, and
  BMD and BMDL arrive as a modelled pair. See `notes/archive/reports/ENDPOINT_DEFINITIONS.md`.
- **ECOTOX is not connected.** It is the primary aquatic source and the
  reason the aquatic endpoints cannot be filled from CompTox.
- **The selection is purposive**, and the natural products are a specific set:
  small phenolic acids, terpenes, coumarins, and a few alkaloids from one book
  about allelopathy.
- **Identity review.** PubChem name resolution is a review task, and 24
  compounds need a human decision on their EPA identity before their EPA
  evidence is used.
- **Multiple comparisons.** Thirty-six traits were compared with unadjusted
  permutation p-values. The intervals, not the p-values, are the honest
  summary.
