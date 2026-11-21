# Parthenium dose-response evidence

The study tested seven purchased chemical standards and a mixture against two
weed species in Petri dishes. It reported week-one germination, root length
and shoot length. The authors used LC–MS on a separate leaf extract to assign
occurrence leads. The study's compound standards and its extract annotations
are separate observations. The caffeic acid mass calculation in section 5.6
is inconsistent with the concentration heading, so concentrations stay
nominal. See [Bashar et al.](https://doi.org/10.3390/toxins14080561).

```powershell
$run = 'experiments/import-expansion'
curl.exe -fLsS -o "$run/raw/parthenium-publisher.xml" https://mdpi-res.com/d_attachment/toxins/toxins-14-00561/article_deploy/toxins-14-00561.xml
uv run --project analysis --locked python -X utf8 analysis/parthenium_panel.py --source "$run/raw/parthenium-publisher.xml" --output "$run/parthenium-review"
```

Tables 4–6 and 8–10 contain 210 dose points for individual compounds and 30
mixture dose points. The extraction preserves measured means, reported
standard errors, original cells, and the published and recomputed percentages
of inhibition. Controls repeat across chemical rows and shared observations
remain associated with a single study. When the printed and recomputed
percentages differ by more than one percentage point or assign different
response bands, the point remains under review. The 40% high and 20% low
cutoffs are descriptive within each species, dose and endpoint.

Named structures from Table 3 support mapping vanillic acid, trans-ferulic
acid, and p-anisic acid. Four other standards and the blend remain in the
response table with identity holds. These data support dose- and
species-specific inhibition. They leave field efficacy, crop selectivity,
natural origin confirmation, and human safety open.

The study's `panel.csv` can be passed to `public_panel.py` using
`--extra-literature`. Each named standard gets one score row within this
study. Multiple records for a standard retain their distinct source
locators. Conflicting structure assertions prevent scoring. The integrated
screen also uses valid structures from additional literature panels as
queries against the high-LD50 catalog pool.

## Follow-up results

`parthenium-review-v2/` retains 210 individual-compound observations.
Of these, 77 are high, 59 low, 70 intermediate and four need review.
Two discrepancies cross the 20% cutoff by less than 0.01 percentage point.
The other two occur in adjacent p-anisic acid cells in Table 8, where the
printed percentage reductions appear swapped relative to the means.
Vanillic acid spans low to high root inhibition in goosegrass as the
nominal dose changes. The high and low counts therefore describe
observations within the experiment rather than distinct kinds of compound.

`public-panel-v5/` records medium-bin predictions from both forests for
vanillic acid, trans-ferulic acid and p-anisic acid. All three scores are
exploratory full fits outside both model target cohorts. These three full
keys lack exact measured ICE medians in this release.
`integrated-v5/` exports 15 new analogue pairs across the three queries.

| Query | Leading analogue | Morgan Tanimoto | Evidence review |
| --- | --- | ---: | --- |
| Vanillic acid | Terephthalic acid | 0.423 | Source-dose conflict and occurrence hold |
| Trans-ferulic acid | Scopoletin | 0.333 | Plant biosynthesis and laboratory root effects supported. Source LD50 lineage unresolved. |
| p-Anisic acid | Terephthalic acid | 0.600 | Source-dose conflict and occurrence hold |

Terephthalic acid's two ICE rat oral points are 1,960 and 18,800 mg/kg
(`acute_oral_28` and `acute_oral_14`). The 10,380 mg/kg median hides a
medium/high disagreement. The sole NPASS taxon/publication link in this
bundle is a pediatric urinary-organic-acid study. Its subject and tissue
context do not verify plant biosynthesis. The source record and review
justify withholding this leading match from a natural-herbicide shortlist.
[Urinary study](https://pubmed.ncbi.nlm.nih.gov/8087979/) and
[EPA toxicology assessment](https://hhpprtv.ornl.gov/issue_papers/PhthalicAcidpTerephthalicAcid.pdf).

Scopoletin has primary evidence for biosynthesis from feruloyl-CoA and for
species-dependent root effects. Its sole exact ICE LD50 is 3,800 mg/kg
(`acute_oral_11463`). The 1974 citation carried by secondary toxicity
sources resolves to a paper on seed alkaloids and hypoglycemia. The
accessible record does not verify the 3,800 point. A separate primary
study reports no treatment-related mortality at a 2,000 mg/kg oral
limit dose, which leaves the high-bin cutoff unverified. Scopoletin is
a plant-effect lead whose higher LD50 needs confirmation.
[Biosynthesis](https://doi.org/10.1111/j.1365-313X.2008.03568.x),
[root-effect study](https://doi.org/10.3390/plants12061278),
[1974 citation](https://pubmed.ncbi.nlm.nih.gov/4280278/) and
[oral limit study](https://pubmed.ncbi.nlm.nih.gov/27133199/).

## High-bin sensitivity

`integrated-v6/` preserves the 399-structure high-median pool and reranks the
same queries against the 360 structures whose eligible exact ICE reports all
fall in the high bin. The two rankings and the source-support ledger retain
the number of point records, distinct dose values, distinct citation strings,
and censored records. A single report can pass the sensitivity screen.
Citation agreement leaves study independence and tested-form verification
open. Censored reports remain visible outside the exact-value check.

The all-exact-high pass removes terephthalic acid from the ranked pool. The
new p-anisic acid leader is 1,4-dimethoxybenzene (Tanimoto 0.550), supported by
one exact ICE report (`acute_oral_2897`, 3,600 mg/kg). Primary field sampling
identifies it in willow floral scent and reports attraction of a specialist
bee. The plant-growth response remains unknown in the reviewed evidence.
Scopoletin remains the leading trans-ferulic match under this narrower test
because its sole ICE report is high. Its citation hold still applies.
[Willow floral scent study](https://pubmed.ncbi.nlm.nih.gov/16258713/).

Isophthalic acid leads the vanillic acid reranking (Tanimoto 0.414).
Four ICE point values span 10,400–13,000 mg/kg and cite the same secondary
database. OECD's dossier resolves the four values to older test reports
and a handbook entry. It also describes a separate rat oral limit study
above 5,000 mg/kg. These records support the high rat oral bin. The exact
COCONUT match (`CNP0265672.0`) provides catalog membership. A 1972 primary
paper's abstract lists isophthalic acid among the compounds tested in
three plant assays. Its accessible abstract leaves the compound-specific
results and natural origin unverified.
[OECD dossier](https://hpvchemicals.oecd.org/UI/handler.axd?id=a2ab2415-8bdd-4338-88a1-156ba0a24145)
and [plant study abstract](https://hero.epa.gov/reference/5551990/).
