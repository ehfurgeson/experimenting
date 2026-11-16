# Herbicide target source exports

Preserved spreadsheet-style source files used for compound/target curation.
Original spreadsheet ownership, export/retrieval dates and version history are
not recorded in these files. Local `notes/CURATED_COMPOUNDS.md` cites them as
read on **2026-10-21**; that is a review date, not a retrieval date.

| Export | Purpose and curation relationship |
| --- | --- |
| [HRACdb](<Herbicide target table - HRACdb.csv>) | HRAC groups, mechanisms and representative herbicides; 52 CSV records after the first row, including headings/blank rows. Contains curated and weedscience.org confirmation blocks. The first row includes an HRAC Global classification-explorer URL; another row says “From Claude”, so independently check scientific assertions. Local `01_curate_compounds.py` parses representative names positionally. |
| [Final_TargetIDs](<Herbicide target table - Final_TargetIDs.csv>) | 13 records after the header: target/protein/EC number, two weed species, paper DOIs, protein IDs, binding residues, resistance, orthologs and Ki/mutation fields. Provides additional named-compound context in the local provenance review. |
| [Weed_TargetIDs](<Herbicide target table - Weed_TargetIDs.csv>) | Same 18-column header structure and 13 records as Final_TargetIDs, but different content (for example, resistance mechanisms). Relationship/order of versions is unknown; retain both. |
| [SpeciesToTarget](<Herbicide target table - SpeciesToTarget.csv>) | 19 records after the header mapping cross-reactivity/target species and taxonomy. Context for species selection; contains no compound names according to the local curation review. |

Counts are CSV records, not validated biological observations. HRACdb and
SpeciesToTarget have blank/repeated headers and internal spreadsheet layout.
Target-ID exports repeat DOI, residue and resistance headers for the two species.
Treat columns by position and species block; a dictionary CSV reader can silently
collapse repeated names. Empty cells and placeholders such as `xxxx` are not
validated missing-value codes or confirmed negative findings.

Keep exports byte-for-byte intact. A future normalized table needs a separate
output and explicit source-column mapping, provenance and validation. Filenames
alone do not establish authority or redundancy. See the [literature/source
catalog](../docs/references.md) and [data guide](../docs/data.md).
