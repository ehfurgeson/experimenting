# Ambiguities

Dated source curation: **2026-10-21**. Reviewed for organization on 2026-11-02;
compound claims/identities have not been independently re-audited. This is the
historical candidate list, not the current selection or a reviewed activity set.
[Provenance index](../CURATED_COMPOUNDS.md) · [Current evidence conventions](../current/evidence-and-identities.md)

`NOTES` citations and literal `notes/notes.md L...` citations in the preserved
source text refer to the [pre-split snapshot](../archive/sources/research-notes-2026-11-02.md),
not today's overview. `ALLEL` and CSV source line references remain unchanged.
All source paths are repository-root-relative. Keep this alias when sharing the tables.

## Ambiguities

Names below appear in the source files but were **excluded** from the candidate tables, or need a decision before PubChem retrieval. Handling recommendation is given for each.

### Excluded: class, family, or group names (not a single compound)

| Name as written | Where | Why excluded | Recommended handling |
|---|---|---|---|
| phenolics / phenolic compounds | `ALLEL` L523, L635, L1114, L1229, L1237, L1254, L1256, L1261, L1279 | generic chemical class | Do not retrieve. Use the individual phenolic acids listed in table (B). |
| terpenoids / terpenes / monoterpenes / sesquiterpenes / diterpenes / triterpenes | `ALLEL` L523, L814, L923, L947, L958, L1229 | generic chemical class | Do not retrieve as a class. Use the individual terpenoids in table (B). |
| flavonoids | `ALLEL` L523, L814, L923, L943, L962, L1229 | generic chemical class | Do not retrieve as a class. |
| benzoxazinoids / benzoxazinones | `ALLEL` L1114, L1334, L1373 | class; several distinct members are named separately | Use `DIMBOA`, `MBOA`, `Cl-MBOA`, `DIBOA`, `BOA` from table (B). |
| glucosinolates | `ALLEL` L1114, L1229 | class of sulfur-containing glycosides | Do not retrieve as a class. |
| isoflavonoids | `ALLEL` L1114 | class | Do not retrieve as a class. |
| hydroxamic acids | `ALLEL` L1114 | class | Do not retrieve as a class. |
| tannins | `ALLEL` L523, L1229 | class of high-molecular-weight polyphenols | Do not retrieve as a class. |
| quinones / quinines | `ALLEL` L923 | class, though `benzoquinone` and `anthraquinone` are named specifically and are kept | Retain the two specific members only. |
| lactones (simple unsaturated lactones) | `ALLEL` L923, L1229 | class | Keep only the named lactones in table (B). |
| alkaloids | `ALLEL` L1229 | class | Keep only the named alkaloids in table (B). |
| fatty acids | `ALLEL` L1114 | class | Keep only the named fatty acids in table (B). |
| amino acids (generic) | `ALLEL` L635 | class | Keep only the named amino acids in table (B). |
| carboxylic acid / organic acids / aromatic acids | `ALLEL` L523, L1229 | class | Keep only the named acids in table (B). |
| cinnamic acid and its derivatives | `ALLEL` L923 | class (parent plus derivatives) | Keep `Cinnamic acid`; the derivatives are not individually named. |
| coumarins | `ALLEL` L923, L1229 | class | Keep `Coumarin`, `Umbelliferone`, `Scopoletin` from table (B). |
| polyacetylenes | `ALLEL` L523 | class | Do not retrieve. |
| quinolinic corrosive | `ALLEL` L1334 | garbled text, not a valid chemical name (likely a scan/translation error for a quinolinic compound) | Do not retrieve. Verify against the printed original before adding anything. |
| leptospermones (plural) | `ALLEL` L1334 | plural of the specific compound `leptospermone` | Already covered by the `Leptospermone` row. |
| thiophenes (root exudates) | `ALLEL` L529 | class of sulfur heterocycles, no member named | Do not retrieve as a class. |
| fumonisin (family of mycotoxins) | `ALLEL` L914 | family of structurally distinct mycotoxins (fumonisin B1, B2, ...) | Do not retrieve the family name. If needed, retrieve a specific fumonisin. |
| pentapeptide | `ALLEL` L914, L1036 | a five-amino-acid peptide, not a single defined small molecule as written | Do not retrieve. Retrieve only if a specific sequence is established. |
| aliphatic aldehydes, straight-chain alcohols, ketones, long-chain fatty acids | `ALLEL` L523 | classes | Do not retrieve. |

### Excluded: plant extracts, mixtures, and formulations (not a single compound)

| Name as written | Where | Why excluded | Recommended handling |
|---|---|---|---|
| vinegar | `ALLEL` L914 | commercial mixture (acetic acid solution) | Exclude. `Acetic acid` is listed separately as a wheat-straw salt. |
| clove oil | `ALLEL` L914 | essential-oil mixture | Exclude. |
| lemon extract | `ALLEL` L914 | extract mixture | Exclude. |
| maize gluten meal | `ALLEL` L914 | bulk meal, a mixture | Exclude. |
| Porganic (PORGANIC) | `ALLEL` L1334, L1365 | commercial bioherbicide formulation from *Aglaia odorata* leaf extracts | Exclude. Not a single compound. |
| neem oil / neem extract | not literally present in the mined files; the `azadirachtin` row in `NOTES` L200 is the compound name only | extract / formulation | Exclude. Retrieve `Azadirachtin` as the defined compound. |
| aqueous extracts, plant residues, root exudates, essential oils, cover-crop extracts | `ALLEL` throughout | mixtures, not defined compounds | Exclude. |

### Ambiguous for PubChem search: single compound, but the name is not unique

| Name as written | Where | Ambiguity | Recommended handling |
|---|---|---|---|
| 2,4-D | `HRACdb` L7, L36 | common name for 2,4-dichlorophenoxyacetic acid; PubChem also holds esters and salts | Search the exact string `2,4-D` and confirm the resolved structure is 2,4-dichlorophenoxyacetic acid (CID 2348). |
| MSMA | `HRACdb` L52 | trade/common name for monosodium methyl arsonate; arsenical herbicide | Search `MSMA` and confirm the resolved record is the arsonate salt, not a mixture. |
| DNOC | `HRACdb` L21 | abbreviation for 4,6-dinitro-o-cresol | Search `DNOC`; verify the resolved record is 4,6-dinitro-o-cresol. |
| Endothall | `HRACdb` L26, L50 | common name for the endothall acid; often sold as a disodium salt | Search `Endothall` and confirm which salt form is returned. |
| Diquat | `HRACdb` L19 | usually formulated as the dibromide salt | Search `Diquat` and confirm the resolved record. |
| Glufosinate / Glufosinate-ammonium | `HRACdb` L12, L40 | free acid vs. ammonium salt; two different structures under near-identical names | Retrieve as two separate records and label the salt form explicitly. |
| 1,2-Benzenedicarboxylic acid bis(2-ethylhexyl) ester (dioctyl phthalate) | `ALLEL` L638 | a synthetic plasticizer listed as a rice-root allelochemical; long industrial history | Include only if the study's rice-root claim is confirmed. Flag as a suspected anthropogenic contaminant rather than a biosynthetic allelochemical. |
| Tricolorin A | `NOTES` L199 | rare compound; PubChem may resolve to a related tricolorin without the 'A' | Confirm the resolved structure matches tricolorin A exactly. |
| Solanine | `NOTES` L198 | 'solanine' can mean alpha-solanine, solanine A, solanine B, or the parent glycoalkaloid mixture | Confirm alpha-solanine (the dominant potato glycoalkaloid) and record the exact CID. |
| Azadirachtin | `NOTES` L200 | 'azadirachtin' is used for a complex mixture of >20 nimbin-type limonoids; azadirachtin A is the major component | Retrieve azadirachtin A specifically and record the CID; treat the mixture as a separate object if needed. |
| Citrulline | `NOTES` L197 | L- and D-citellulline are both commercially common; PubChem 'citrulline' usually returns the L form (CID 9750) | Confirm the stereoisomer matches the intended compound before comparison. |
| Camphene (source spelling 'samphene') | `ALLEL` L938 | source text has a spelling error; 'camphene' is the real compound | Search `Camphene`; note the source spelling error. |
| 3,3',5-Trihydroxy-4',7-dimethoxyflavone | `ALLEL` L800 | source has the garbled spelling '3-3'-5-trihidroxy-4'-7-dimethoxyflanove' (OCR errors: 'trihidroxy', 'flanove') | Search the corrected systematic name; verify against the printed original. |
| 3,3',5-Trihydroxy-4',7-dimethoxyflavone-3-O-sulfate | `ALLEL` L800 | same OCR garbling as the entry above ('trihidroxy') | Search the corrected systematic name; verify against the printed original. |
| alpha-Thujone (source spelling 'a-thujone') | `ALLEL` L930 | the source uses a plain 'a' where the Greek alpha should be; also thujone has alpha/beta and cis/trans forms, and `trans-Thujone` and `cis-Thujone` are listed separately at L938 | Search `alpha-Thujone`; keep the three thujone rows distinct and do not merge them. |
| Camphor / Borneol | `ALLEL` L938 | each name covers multiple stereoisomers in PubChem (e.g. (+)/(-)-camphor, isoborneol) | Confirm the resolved stereochemistry and record the CID. |
| Germacrene D / Germacrene B | `ALLEL` L938, L947 | both are single defined sesquiterpenes, but E/Z isomer sets exist in PubChem | Verify the resolved record. |
| alpha-Pinene / alpha-Thujene | `ALLEL` L938 | enantiomer pairs | Verify the resolved record. |
| m-Tyrosine (meta-tyrosine) | `ALLEL` L406, L1259 | 'm-tyrosine' is an older name for meta-tyrosine (3-hydroxyphenylalanine); L- and D- forms exist | Search `meta-Tyrosine`; confirm the stereoisomer. |
| 8-Hydroxyquinoline | `ALLEL` L956 | a single compound; listed in the source as an allelochemical of *Centaurea diffusa* | Fine as written. |
| Triketone herbicides mesotrione / tembotrione / sulcotrione | `ALLEL` L1111 | synthetic HPPD inhibitors named only as the synthetic analogues of the natural triketones | They belong in group (A) if wanted; `mesotrione` and `tembotrione` are already in table (A) from `HRACdb`. `sulcotrione` is in neither table. |
| DIMBOA | `ALLEL` L648 | the source gives only the acronym; it is not expanded there | Search `DIMBOA` and confirm the resolved structure before use. The full systematic name is not stated in the source, so it is not reproduced here. |
| MBOA / Cl-MBOA / DIBOA / BOA | `ALLEL` L648, L669, L964 | benzoxazinoid acronyms; `MBOA` and `Cl-MBOA` are given with systematic names in the source, `DIBOA` and `BOA` are also given | Search each acronym and verify the resolved structure. |

### Source spelling and OCR variants

| Name as written | Where | Issue | Recommended handling |
|---|---|---|---|
| `samphene` | `ALLEL` L938 | misspelling of `camphene` | Search `Camphene`; the source spelling is preserved in the group (B) table. |
| `a-thujone` | `ALLEL` L930 | the source uses a plain `a` where the Greek alpha belongs | Search `alpha-Thujone`. Keep it distinct from the `trans-Thujone` and `cis-Thujone` rows at L938. |
| `ρ-coumaric acid` | `ALLEL` L638 | the Greek rho is an OCR rendering of `p` | Treated as `p-Coumaric acid`; the source form is preserved in the group (B) table. |
| `3-3'-5-trihidroxy-4'-7-dimethoxyflanove` | `ALLEL` L800 | OCR errors: `trihidroxy` for `trihydroxy`, `flanove` for `flavone` | Search the corrected systematic name `3,3',5-Trihydroxy-4',7-dimethoxyflavone`; verify against the printed original before trusting the CID. |
| `3-3'-5-tri hidroxy-4'-7-dimethoxyflavone-3-O-sulphate` | `ALLEL` L800 | OCR errors: `tri hidroxy` for `trihydroxy`, and British spelling `sulphate` | Search `3,3',5-Trihydroxy-4',7-dimethoxyflavone-3-O-sulfate`; verify against the printed original. |
| `17-α hydroxycabraleactone` | `ALLEL` L958 | missing hyphen between the locant and the name | Search `17-alpha-Hydroxycabraleactone`. |
| `2-amino-9-(4-oxoazetidin- 2-yl)` | `ALLEL` L959 | stray space inside the IUPAC name | Search the cleaned IUPAC name; the source form is preserved in the group (B) table. |
| `1H-indole-3carboxaldehyde` | `ALLEL` L638 | missing hyphen | Search `1H-Indole-3-carboxaldehyde`. |
| `ethyl 2-methyl acetoacetate` | `ALLEL` L611 | a space in the IUPAC name | Search `Ethyl 2-methylacetoacetate`. |
| `11-α-acetylbrachycarpone-22(23)-ene` | `ALLEL` L958 | line break inserted as `22(23)- ene` | Search the unbroken name. |
| `4,6-dimethylbicyclo[3.1.0] hex-2-ene-2,6-dimethanol` | `ALLEL` L937 | stray space after the bracket | Search the unbroken name. |

---
