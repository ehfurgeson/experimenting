# Compact input snapshots for the joint catalog rebuild

The rebuild driver combines these tracked files with the supplied local data
imports and checksum-pinned OPERA, COCONUT and LOTUS downloads. The files
freeze the details that would otherwise depend on an ignored run directory or
live source lookups.

| File | Origin and scope |
| --- | --- |
| `de-martino-2012-tables.xml` | Tables 1 and 2 from De Martino et al., DOI `10.3390/ijms13055406`, including the study and control values used in the 324 restored observations. The tables were extracted from the article XML under CC BY 3.0. [Open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC3382788/) · [License](https://creativecommons.org/licenses/by/3.0/) |
| `flavonoid-pubchem.json` | The 27 PubChem structure lookups used to map compound names in table order. Each mapping retains its CID and provider InChIKey. Biological sample stereochemistry remains provisional. |
| `toxval-dermal-observations.csv` | The 451 admitted row-level outputs of the ToxValDB 9.7.0 rat dermal filter. The export retains native locators, references and experimental-status distinctions. The full upstream workbooks and raw record exports remain accessible through the acquisition and extraction commands. [EPA release](https://doi.org/10.23645/epacomptox.20394501) · [Full audit workflow](../../docs/data-sprint.md) |
| `reviewed-plant-context.csv` | Frozen context rows from the original natural-product rescreen, including literature and still-held ECOTOX leads. References and assay observations stay attached. [Review procedure](../../docs/natural-product-rescreen.md) |
| `oral-qualifier-review.csv` | The reviewed ICE butyl stearate lower bound. The original report was stored as exact in the frozen cohort. The joint screen verifies the record ID, full key, value and absence of a separate exact record before applying the review. [Source review](../../docs/candidate-audit-2026-11-17.md#illustrative-shortlist) |

The snapshot pipeline recreates the current catalog, model diagnostics and
notebook. Repeating the historical source inventories or human-review runs
requires the larger raw archives specified in their own methods.
