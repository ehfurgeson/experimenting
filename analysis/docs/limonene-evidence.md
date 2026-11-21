# (R)-(+)-Limonene plant and acute oral evidence

Kaur et al. (2025) tested a purchased (R)-(+)-limonene standard in a
Petri-dish germination assay. The concentrations are nominal weight
percent in the assay. These means come from the enantiomer-specific
experiment in Table 2. The paper separately tests celery essential oil,
its formulations, and a two-enantiomer blend.
[Plant study](https://doi.org/10.1038/s41598-025-25935-z).

| Concentration (% w/w) | Wheat germination (%) | Resistant *P. minor* (%) | Sensitive *P. minor* (%) | *A. ludoviciana* (%) |
| ---: | ---: | ---: | ---: | ---: |
| Control | 100 | 100 | 100 | 100 |
| 0.152 | 100 | 100 | 100 | 16 |
| 0.38 | 100 | 98 | 85 | 0 |
| 0.76 | 100 | 43 | 36 | 0 |
| 2.0 | 18 | 21 | 10 | 0 |

The assay shows stronger inhibition of *A. ludoviciana* than of
*P. minor* at the lower tested concentrations. At 2.0% wheat germination
also falls. Field efficacy and crop selectivity remain unresolved for
the individual compound.

Biochemical characterization of sweet-orange limonene synthase
supports natural production of the (+)-enantiomer. The screening row
uses the full stereospecific key `XMGQYMWWDOXHJM-JTQLQIEISA-N`,
consistent with the FDA substance record for CAS 5989-27-5.
[Biosynthesis study](https://doi.org/10.1021/acs.biochem.7b00143)
and [FDA substance record](https://precision.fda.gov/uniisearch/srs/unii/GFD7C86Q1W).

ICE retains one eligible point for that structure, 4,400 mg/kg
(`acute_oral_8184`, `Data!row2081`). WHO reports 4,400 and 5,100 mg/kg
in male and female rats from the same acute oral study. Both values
are above the project's 3,400 mg/kg cutoff. The 4,400 mg/kg value
should be treated as shared evidence across the sources. The EPA
scoping assessment also records irritation and dermal sensitization
concerns. Rat oral lethality alone leaves human risk unresolved.
[WHO oral toxicity table](https://www.inchem.org/documents/cicads/cicads/cicad05.htm)
and [EPA assessment](https://downloads.regulations.gov/EPA-HQ-OPP-2010-0673-0004/content.pdf).

Both forests predict medium in `public-panel-v6/panel.csv`. A uses a
scaffold-held-out prediction (medium probability 0.435, high 0.351).
B uses an exploratory full-fit prediction outside the teacher cohort
(medium 0.896, high 0.039). The measured rat oral point places the
compound in the high bin. These predictions show why measured evidence
matters for shortlisting.

`integrated-v7/` adds the five highest-ranked matches from each of the
two high-LD50 analogue pools. The high-median leader's exact points span
1,640–5,900 mg/kg, so the all-exact-high ranking removes it. The leader
in that ranking is the stereochemistry-unspecified α-terpineol entry
(Morgan Tanimoto 0.455), supported by one eligible exact ICE point.
These are structural leads requiring source and plant-response review.

To reproduce the scoring row, pass
`--extra-literature analysis/resources/limonene_primary_review_2026-11-18.csv`
to `public_panel.py` with the public cohort and benchmark inputs described
in the [analysis README](../README.md).
