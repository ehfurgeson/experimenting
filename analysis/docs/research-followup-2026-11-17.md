# Branch review and research follow-up — 17 November 2026

The branch has completed the broad data sprint and a permissive experimental
continuation. The next scientific bottleneck is **comparable plant dose-response
evidence and verified natural occurrence**. This follow-up also executes new
representation pilots, a LOTUS overlay, selection screens and an analogue search.

Reviewed branch: `research/data-first-sprint-2026-11-17`, HEAD `3bfd460`; 15 commits
and 38 tracked changed files relative to local `main` before this follow-up.
This is a local comparison, without fetching a remote ref. Pre-existing edits to
`analysis/uv.lock`, `pipeline/pyproject.toml` and `pipeline/uv.lock` were preserved.

## Plan versus completed work

| Workstream | Current evidence | Assessment / remaining work |
| --- | --- | --- |
| Natural-product identification | COCONUT matches 1,478/4,234 frozen A structures; either COCONUT or NPASS matches 1,617 | Useful catalog overlay; absent matches mean unknown origin. Verify natural occurrence. |
| EPA toxicity expansion | `toxicity-v2`: source-asserted exact pool 4,678; broad accepted exact pool 8,375; classification pool 9,520 | The +444 strict-source candidates still need tested-form/study-lineage reconciliation. Broad +4,141 incorporates missing-context assumptions; 3,934 of those new exact rows still carry one. It is not +4,141 newly verified independent studies. The pre-median 8,381 / 9,526 counts are `toxicity-v1`. |
| Plant data | `plant-v5`: 733 observations, 211 structures, 76 references, 207 high / 526 low | Replaces 2,260/365/342, the `plant-v3` class counts 208/525, and the `plant-v4` counts 204/529. Doses, endpoints, species and exposure methods remain heterogeneous. |
| Joint evidence | 2,619 catalog-plus-exact-toxicity structures; 49 also have plant responses | Replaces the retracted 120 three-axis count. Of the 49, 10 are selected herbicides and 4 are selected natural products. A catalog hit is not an origin claim. |
| Original selection | 116 natural-product and 60 herbicide rows | All 116 natural rows and 58 herbicides scored. Two multicomponent herbicide forms remain unscorable. Reconcile the requested “120” with the original list. |
| Protein interactions | 469 plant-protein records, including 40 Kd/Ki records | Preserve assay type. IC50 is not a binding constant; target annotation alone does not prove mechanism. |
| Candidate screen | `integrated-screen-v5`: 2,890 structures, 11-member mathematical prediction front | Not a safer-herbicide or natural-product shortlist. Full-fit scores include training compounds. |

The original plan's identity, provenance, censoring and validation contracts are
sound. Its leading plant counts and report pointers were stale and are corrected
in the local plan. `accepted_screen.py` defaults to `plant-v5`, `plant-models-v5`,
`toxicity-v2`, `toxicity-models-v2` and `uncertainty-v2`. `accepted_report.py`
writes `results-v5` and refuses the retracted 120-structure release. `results-v2`
remains the invalidated plant-v1 report. `results-v4` quoted the pre-refit forests.
The follow-up pilot was regenerated as `pilot-v2` on `plant-v5` labels and
`toxicity-models-v2` folds. `pilot-v1` and `report-v2` remain the earlier
`plant-v3` / `toxicity-v1` products.

Do not manufacture three universal classes called natural nonherbicidal, natural
herbicidal and synthetic herbicidal. Use documented occurrence as one axis, tested
high/low response **within a declared assay context** as another, and herbicide-use
membership separately. Keep mixed-context and untested structures visible. The
descriptive comparison includes 36 selected herbicide structures with exact toxicity;
it does not infer synthetic origin from catalog absence.

## New model experiments

Pilot: `experiments/data_acquisition/2026-11-17-review-followup/pilot-v2/`.
Verified figures, annotated analogues and coefficient summaries: `report-v3/`.

Five fixed profiles compare the seven original descriptors, thirteen descriptors
(adding logP, individual F/Cl/Br/I counts and formal charge), and chiral radius-2
2048-bit Morgan fingerprints. No hyperparameter search or automatic model promotion
was performed. Toxicity uses the `toxicity-models-v2` all-accepted chemical
partitions and evaluates **unchanged 4,234 frozen A outcomes**. Plant uses `plant-v5`
quantitative labels, inverse chemical-frequency training weights and equal total evaluation
weight per structure. Publication and chemical holdouts are separate protocols.

| Profile | Toxicity macro-F1, frozen A | Plant macro-F1, publication holdout | Plant macro-F1, chemical holdout |
| --- | ---: | ---: | ---: |
| 7 descriptors, logistic | 0.3757 | **0.6676** | 0.6084 |
| 7 descriptors, forest | 0.4387 | 0.5912 | 0.4861 |
| 13 descriptors, logistic | 0.3916 | 0.6103 | 0.5417 |
| 13 descriptors, forest | **0.4555** | 0.5620 | 0.4948 |
| Morgan, logistic | 0.4287 | 0.6134 | **0.6288** |

The seven-descriptor forest matches `toxicity-models-v2` and `plant-models-v5`
on these same holdouts. The richer toxicity forest moves low-LD50 recall from
0.5187 to 0.5575. Its macro-F1 difference is +0.0168, conditional paired 95%
interval −0.0052 to +0.0337. The original logistic's plant gains over the original
forest are +0.0764 by publication (−0.0261 to +0.2171) and +0.1223 by chemistry
(−0.0056 to +0.2270). Those three intervals include zero. Two toxicity logistic
comparisons exclude zero because they are lower than the seven-descriptor forest:
−0.0630 (−0.0791 to −0.0352) for seven descriptors and −0.0472 (−0.0619 to −0.0135)
for thirteen. The Morgan chemical-holdout gain is +0.1427 (+0.0358 to +0.2574)
and excludes zero; its publication interval includes zero. Intervals resample
clusters of fixed held-out predictions, with 2,000 draws, no refitting and no
multiplicity correction. They do not promote a new profile or justify a general
plant-inhibition claim.

Exports retain per-class F1/recall/precision/support, predictions, memberships,
standardized logistic coefficients and five-repeat tree-specific OOB permutation
diagnostics. Logistic weights describe conditional associations per training
standard deviation, not causation. Plant coefficients refer to high response;
toxicity coefficients are class-specific. OOB targets are low-LD50-versus-rest
and high plant response, using separate unweighted observation forests. Repeat SD
is stability, **not significance**; OOB does not separate repeated chemicals/studies.
Correlated descriptors can mask one another's contribution.
[scikit-learn interpretation guidance](https://scikit-learn.org/stable/modules/permutation_importance.html)

The three logistic alternatives were fit to the full pools and applied to 174
scorable selection rows, with explicit training-membership flags. These scores
are uncalibrated and separate from held-out evaluation. The earlier B forest
F1 ≈0.616 predicts **CATMoS teacher outputs** from the OPERA archive. Comparing it
with the current experimental forest macro-F1 of 0.4387 does not establish better experimental accuracy.
Retain teacher overlap and applicability-domain information.
[CATMoS primary study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8086800/)

## Natural toxicants, occurrence links and analogues

The 2,596 exact-toxicity catalog matches contain **1,127 low-, 803 medium- and
666 high-LD50 structures**. Project bins are low ≤1,080, medium >1,080
through 3,400 and high >3,400 mg/kg; these are not regulatory categories. Of the
low-class entries, 694 are frozen A, 12 are ToxValDB rows without a context
assumption, and 421 have an experimental, route, or acute-context assumption.

Catalog hits include scilliroside and brucine but also problematic origin leads
such as phorate and crimidine. **1,127 is a catalog-matched low-LD50 count, not a
verified natural-toxicant count.** COCONUT's methods discuss curation and possible
misclassifications; NP-likeness also does not prove occurrence.
[COCONUT 2.0 primary publication](https://academic.oup.com/nar/article/53/D1/D634/7908792)

The verified [LOTUS v11 export, 13 April 2026](https://zenodo.org/records/19360665)
updates the plan's assumption that only a static 2021 download is available.
Its 674,454 structure–organism–reference triplets yield **63,671 exact-key links
for 1,212 of the 2,890 structures in `integrated-screen-v5`**.
`pilot-v1` had reported 63,720 links for 1,220 of the unre-run 2,908-candidate
`integrated-screen-v3` screen. That overlay is not current.
Only 25 matched rows carry the provider's manual-validation flag; 63,643 have DOIs.
Native taxon/reference/Wikidata fields persist. Trace shared publications before
counting corroboration; a provider flag is not this project's primary review.
Publisher MD5 and local SHA256 were checked; release license is CC BY 4.0.

A concrete provenance counterexample is retained in
`analysis/resources/origin_counterexample_review_2026-11-17.csv`: LOTUS links
glyphosate to soybean through DOI 10.1021/jf073087h. The
[primary publication](https://doi.org/10.1021/jf073087h) studies the composition of
glyphosate-tolerant soybean; that link does not demonstrate glyphosate biosynthesis
by soybean. Treat taxon/reference co-occurrence as a review lead, not an automatic
natural-origin decision. Several familiar herbicides also occur in the 49-way
intersection, which is consequently not a list of 49 verified natural herbicides.

Analogue search queries all 116 selected natural-product rows against the 2,596
catalog-matched exact-toxicity structures. It retains the top five with accepted
LD50 ≥3,400 mg/kg and different connectivity: **580 pairs**, with **18 at Morgan
Tanimoto ≥0.6**. The queue threshold differs slightly from the high-class boundary.
Low-similarity top-five matches remain visible; these are not 580 close analogues.
Examples: sinapic acid → isoferulic acid (0.629, accepted LD50 7,900 mg/kg), and
linoleic acid → decanoic acid (0.654, 3,730 mg/kg). Review natural occurrence,
tested forms, plant responses and dose context before any read-across claim.

Azelaic acid and different chain-length diacids can score Tanimoto 1.0 because
finite-radius binary fingerprints can coincide. The annotated table retains
SMILES and this limitation; full keys establish identity. This search covers the
accepted-toxicity intersection, **not all 724,233 validated COCONUT full keys**.
Of these 2,596 structures, 2,557 (98.5%) have no labeled plant observations.

## Prioritized research and next work

1. **Recover comparable efficacy and low responses.** A
   [2024 field study](https://www.mdpi.com/2073-4395/14/3/537) compares six natural
   compounds and herbicide controls. Six review-only UPV observations are saved in
   `analysis/resources/plant_field_review_2026-11-17.csv`. At 28 days, ground coverage
   ranges from 10.1% for PA-55 to 99.9% for p-cymene, against 100% untreated coverage.
   These are raw field coverage percentages, not percentages of inhibition.
   Formulations, initial coverage and mixed weed populations prevent direct
   pure-compound label adoption. Recover replicate data and a declared response policy.
2. **Fit assay-specific dose-response models.** A
   [pelargonic-acid study](https://doi.org/10.3390/agronomy12123229) tests five
   application rates and estimates species-specific ED50–ED95, including censored
   results. Recover tables/uncertainty and fit monotone/log-logistic curves per
   species/context, retaining regrowth and incomplete inhibition. Plant kg/ha and
   rat mg/kg do not form a dose-matched selectivity ratio.
3. **Audit natural occurrence where it changes decisions.** Start with the 49
   three-axis structures, low-LD50 extremes and 18 closer analogue pairs. Follow
   LOTUS/COCONUT/NPASS links to primary publications and exact tested forms.
   Resolve false catalog membership and study mirrors before group hypothesis tests.
4. **Expand EPA selectively.** EPA lists
   [ToxValDB v9.7.0 and ToxRefDB v3.0](https://www.epa.gov/comptox-tools/downloadable-computational-toxicology-data).
   ToxValDB is already acquired: audit the 445 strict-source candidates' form and
   lineage first. ToxRefDB can add separate repeat-dose/reproductive evidence;
   ToxCast can add mechanistic hazard flags. Neither becomes an acute LD50 label.
   ECOTOX supplies ecological plant effects, not human acute oral toxicity.
   No new strictly qualified independent LD50 study was established in this pass.
5. **Benchmark pretrained models after these baselines.**
   [ADMET-AI](https://github.com/swansonk14/admet_ai) supports batch Chemprop
   predictions. Its current v2 code and v1 web server/paper use different fits;
   pin checkpoint, endpoint scale and training overlap before comparison.
   [Uni-Mol](https://github.com/deepmodeling/Uni-Mol) supplies pretrained molecular
   representations: a frozen-embedding head is a reasonable next comparator.
   Use the same outer partitions and training-only tuning/calibration. Outputs
   remain endpoint-specific screening evidence. Neither was installed/run here.
6. **Make protein modeling target-specific.** A
   [19-compound Arabidopsis HPPD study](https://pubmed.ncbi.nlm.nih.gov/19435355/)
   contains natural β-triketones and inactive analogues; grandiflorone enzyme
   inhibition is 750 ±70 nM. This is I50, not Kd or whole-plant potency. Recover
   structures and compare plant/mammalian orthologs. [ESM C](https://github.com/Biohub/esm)
   or [ESM-2](https://github.com/facebookresearch/esm) can represent target sequences;
   embeddings alone do not predict binding/selectivity. Keep direct affinities
   separate from functional assays, and hold out ligand scaffolds and sequence
   clusters. Forty heterogeneous affinity records do not justify a large DTI fit.

The next semester deliverable should be an audited 10–20-compound validation queue
with exact occurrence, plant dose-response evidence, measured acute hazard,
separate chronic/non-target flags and feasible assays. Include a chemically diverse
uncertain subset for informative testing. Higher rat oral LD50 alone does not
establish that a compound is non-toxic to humans.

## Reproduce and verify

From the repository root with the prepared local inputs:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 uv run --project analysis --locked python analysis/research_followup.py \
  --accepted experiments/data_acquisition/2026-11-17-accepted-experiments \
  --sprint experiments/data_acquisition/2026-11-17-data-sprint \
  --lotus experiments/data_acquisition/2026-11-17-review-followup/raw/260413_frozen.csv.gz \
  --output experiments/data_acquisition/NEW_RUN/pilot

uv run --project analysis --locked python analysis/research_followup_report.py \
  --pilot experiments/data_acquisition/NEW_RUN/pilot \
  --accepted experiments/data_acquisition/2026-11-17-accepted-experiments \
  --output experiments/data_acquisition/NEW_RUN/report
```

The scripts require local inputs, verify hashes and refuse existing output folders.
LOTUS input is the linked v11 publisher file `260413_frozen.csv.gz`. Raw data and
large products remain ignored/local. Source URLs, release, license, runtime versions
and code snapshots are recorded. Computed classes use upstream `ld50_bin`:
low ≤1,080, medium above 1,080 through 3,400, and high above 3,400 mg/kg.
The analogue queue threshold of ≥3,400 mg/kg is not exactly the high-class boundary.

`selection_screen.csv` retains all 176 rows and existing forest scores;
`selection_model_comparison.csv` adds logistic alternatives and training membership.
Other products include `natural_toxicity.csv`, `lotus_occurrence_links.csv`,
`analogues.csv`, `group_contrasts.csv`, `metrics.csv`, `coefficients.csv`, `oob.csv`
and `paired_intervals.csv`. The report adds annotated analogue names/structures,
fold summaries of logistic weights and standalone PNG/SVG figures.

Independent verification recomputes 15 model F1 scores, reproduces the six
descriptor7 baselines in `toxicity-models-v2` and `plant-models-v5`, verifies 19
pilot product hashes, checks group fold exclusivity and
checks selection, class, occurrence and analogue counts. All 390 analysis tests
pass. These checks verify computation under source assumptions, not biology.
