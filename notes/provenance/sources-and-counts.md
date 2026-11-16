# Sources and historical counts

Dated source curation: **2026-10-21**. Reviewed for organization on 2026-11-02;
compound claims/identities have not been independently re-audited. This is the
historical candidate list, not the current selection or a reviewed activity set.
[Provenance index](../CURATED_COMPOUNDS.md) · [Current evidence conventions](../current/evidence-and-identities.md)

`NOTES` citations and literal `notes/notes.md L...` citations in the preserved
source text refer to the [pre-split snapshot](../archive/sources/research-notes-2026-11-02.md),
not today's overview. `ALLEL` and CSV source line references remain unchanged.
All source paths are repository-root-relative. Keep this alias when sharing the tables.


The original source introduction and count commentary follow. References to the
two tables “above” mean the split [herbicide](herbicides.md) and
[natural-product](natural-products.md) records. Their historical counts are not
a fresh audit of scientific identity or activity.

Verified, deduplicated candidate list for PubChem retrieval. Every compound name below appears literally in the cited source file; nothing has been invented. Line numbers refer to the files as read on 2026-10-21. Where the source spells a name differently from the PubChem-searchable form, the source spelling is shown in quotes in the source column.

**Sources mined (read in full)**

| Key | Path |
|---|---|
| `HRACdb` | `herbicide_target_tables/Herbicide target table - HRACdb.csv` |
| `Final_TargetIDs` | `herbicide_target_tables/Herbicide target table - Final_TargetIDs.csv` |
| `Weed_TargetIDs` | `herbicide_target_tables/Herbicide target table - Weed_TargetIDs.csv` |
| `SpeciesToTarget` | `herbicide_target_tables/Herbicide target table - SpeciesToTarget.csv` — cross-species organisms only; contains no compound names |
| `ALLEL` | `Allelopathy_Potential_for_Green_Agriculture.md` |
| `NOTES` | `notes/notes.md` |

---

## Counts

- **Herbicides (group A): 61**
- **Natural products (group B): 127**
- **Total candidate compounds: 188**

Counts are the number of data rows actually written in the two tables above, verified by re-parsing the rendered table rows. Group B includes the four professor-requested compounds (citrulline, solanine, tricolorin A, azadirachtin) and four plant response markers (indole-3-acetic acid, abscisic acid, ethylene, proline) that are named in the sources but are not themselves allelochemicals.

Group A compounds by source file (a compound is counted once per file it appears in):

- `HRACdb`: 60
- `Weed_TargetIDs`: 6
- `Final_TargetIDs`: 4

Group B compounds by source file (a compound is counted once per file it appears in):

- `ALLEL`: 123
- `NOTES`: 4
