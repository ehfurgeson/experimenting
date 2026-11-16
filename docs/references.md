# Source reference catalog

## Allelopathy literature

[Allelopathy: Potential for Green Agriculture](../Allelopathy_Potential_for_Green_Agriculture.md),
Waseem Mushtaq, Mohammad Badruzzaman Siddiqui and Khalid Rehman Hakeem,
Springer Nature, 2020; DOI `10.1007/978-3-030-40807-7`, ebook ISBN
`978-3-030-40807-7`. These identifiers come from the file's front matter.
The Markdown states that it was converted from a supplied 75-page PDF and
retains PDF page markers. Conversion/retrieval date is not recorded there.

This is a literature source for candidate curation, not a validated compound
activity table. Local `notes/CURATED_COMPOUNDS.md` cites its lines under `ALLEL`
as read on 2026-10-21; `notes/archive/reports/candidate_review.md` supplies further local review.
`experiments/01_curate_compounds.py` embeds selected natural-product names and
points to that provenance rather than automatically extracting the book.
Preserve the root path and source line numbering. Do not reflow or relocate the
text as a cosmetic change.

## Herbicide targets

The [source-table guide](../herbicide_target_tables/README.md) catalogs all four
exports and their positional schemas. HRAC grouping, target proteins, species,
resistance and ortholog references provide curation/binding context. Their presence
does not establish measured binding of a particular natural product.

The [experimental structural-evidence pilot](../analysis/docs/binding-evidence.md)
adds a separate audited route through primary papers and RCSB deposited
complexes. It preserves exact bound forms, protein construct/organism metadata
and source uncertainty; it does not alter the original target-table exports or
fill their unknown affinities/orthologs.

## Source-linked rat toxicity review

[Gorzinski et al., 1987](https://doi.org/10.1016/0272-0590(87)90025-X),
*Acute, Pharmacokinetic, and Subchronic Toxicological Studies of
2,4-Dichlorophenoxyacetic Acid*, *Fundamental and Applied Toxicology* 9:423–435,
is ECOTOX reference 93388. A scanned primary-paper copy was retrieved from an
accessible third-party mirror and visually checked for the
[experimental source-review checkpoint](../analysis/docs/rat-source-review-2026-11-12.md).
The checkpoint preserves material-tested versus acid-equivalent doses, acute
versus subchronic experiments, two displayed conversion discrepancies and
provisional review status. Native source exports are unchanged.
