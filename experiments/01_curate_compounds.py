"""Build the curated compound list from the repository sources.

Reads the herbicide target tables for the conventional herbicides and uses the
allelochemical names that the Allelopathy book and the project notes name
explicitly for the natural products. Writes a selection CSV that the retrieval
scripts can read.

Run from the repository root:

    uv run --project pipeline python experiments/01_curate_compounds.py
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HRAC_TABLE = ROOT / "herbicide_target_tables" / "Herbicide target table - HRACdb.csv"
OUTPUT = Path(__file__).resolve().parent / "data" / "compounds.csv"
CLASSES = Path(__file__).resolve().parent / "data" / "compound_classes.csv"

# Named allelochemicals from "Allelopathy: Potential for Green Agriculture"
# (Table 5.1 and the chapter text) and from the project's research notes.
# Each entry is (name, class, source note). Nothing here is a plant extract,
# a mixture, or a chemical class.
# Named allelochemicals and requested natural products. The full provenance table,
# with the source line for every name, is in notes/CURATED_COMPOUNDS.md.
#
# Some names were changed to a form PubChem resolves, or to an explicit CID
# where the name is ambiguous. A name that has no PubChem record at all is
# left out of the selection and is listed in the experiment notes.
NATURAL_PRODUCTS = [
    ("Citrulline", "amino acid"),
    ("Solanine", "glycoalkaloid (steroidal alkaloid glycoside)"),
    ("Tricolorin A", "glycoside (flavonoid glycoside)"),
    ("Azadirachtin", "terpenoid (limonoid)"),
    ("Sorgoleone", "hydroquinone"),
    ("Benzoquinone", "quinone"),
    ("Anthraquinone", "quinone"),
    ("Scopoletin", "coumarin"),
    ("4-Hydroxybenzoic acid", "phenolic acid"),
    ("Coumarin", "coumarin"),
    ("Vanillic acid", "phenolic acid"),
    ("alpha-Thujone", "terpenoid (monoterpene)"),
    ("Emodin", "anthraquinone"),
    ("Physcion", "anthraquinone"),
    ("Benzoic acid", "benzoic acid (phenolic acid)"),
    ("Chlorogenic acid", "phenolic acid (quinic acid ester)"),
    ("Cinnamic acid", "cinnamic acid (phenolic acid)"),
    ("p-Coumaric acid", "phenolic acid"),
    ("m-Coumaric acid", "phenolic acid"),
    ("o-Coumaric acid", "phenolic acid"),
    ("Ferulic acid", "phenolic acid"),
    ("Caffeic acid", "phenolic acid"),
    ("Gallic acid", "phenolic acid"),
    ("Syringic acid", "phenolic acid"),
    ("Protocatechuic acid", "phenolic acid"),
    ("Sinapic acid", "phenolic acid"),
    ("Acetic acid", "aliphatic acid"),
    ("Propionic acid", "aliphatic acid"),
    ("Butyric acid", "aliphatic acid"),
    ("Phenylacetic acid", "aromatic aliphatic acid"),
    ("4-Phenylbutyric acid", "aromatic aliphatic acid"),
    ("o-Hydroxyphenylacetic acid", "phenolic aliphatic acid"),
    ("Salicylic acid", "phenolic acid"),
    ("p-Hydroxybenzaldehyde", "phenolic aldehyde"),
    ("Syringaldehyde", "phenolic aldehyde"),
    ("Vanillin", "phenolic aldehyde"),
    ("Salicylaldehyde", "phenolic aldehyde"),
    ("Resorcinol", "dihydroxybenzene"),
    ("Phloroglucinol", "trihydroxybenzene"),
    ("Methyl vanillate", "phenolic ester"),
    ("1,8-Cineole", "terpenoid (monoterpene)"),
    ("Camphor", "terpenoid (monoterpene)"),
    ("Borneol", "terpenoid (monoterpene)"),
    ("Germacrene D", "terpenoid (sesquiterpene)"),
    ("Artemisia alcohol", "terpenoid (sesquiterpene)"),
    ("trans-Thujone", "terpenoid (monoterpene)"),
    ("para-Cymene", "terpenoid (monoterpene)"),
    ("Sabinene", "terpenoid (monoterpene)"),
    ("alpha-Pinene", "terpenoid (monoterpene)"),
    ("Pinocarvone", "terpenoid (monoterpene)"),
    ("11744854", "terpenoid (monoterpene)"),
    ("trans-Sabinene hydrate", "terpenoid (monoterpene)"),
    ("Myrtenol", "terpenoid (monoterpene)"),
    ("Carvacrol", "phenolic monoterpene"),
    ("Jasmine ketolactone", "terpenoid (lactone)"),
    ("(Z)-Methyl jasmonate", "jasmonate (terpenoid)"),
    ("alpha-Thujene", "terpenoid (monoterpene)"),
    ("Eugenol", "phenylpropanoid"),
    ("Terpinen-4-ol", "terpenoid (monoterpene)"),
    ("Artemisia ketone", "terpenoid (ketone)"),
    ("(E)-Ethyl cinnamate", "cinnamate ester"),
    ("Davanone", "terpenoid (sesquiterpene)"),
    ("Filifolide A", "terpenoid (sesquiterpene)"),
    ("(Z)-Ethyl cinnamate", "cinnamate ester"),
    ("Piperitone", "terpenoid (monoterpene)"),
    ("Chrysanthenone", "terpenoid (sesquiterpene)"),
    ("Nordavanone", "terpenoid (sesquiterpene)"),
    ("Yomogi alcohol", "terpenoid (sesquiterpene)"),
    ("Methyl epi-jasmonate", "jasmonate (terpenoid)"),
    ("Tricin", "flavonoid"),
    ("Acacetin", "flavonoid"),
    ("Syringoside", "phenylpropanoid glycoside"),
    ("Diosmetin", "flavonoid"),
    ("Militarine", "alkaloid (orchid alkaloid)"),
    ("Dactylorhin A", "alkaloid (orchid alkaloid)"),
    ("Naringin", "flavonoid glycoside"),
    ("Quercetin", "flavonoid"),
    ("Catechin", "flavonoid (flavan-3-ol)"),
    ("Aplotaxene", "sesquiterpene"),
    ("Caryophyllene oxide", "terpenoid (sesquiterpene)"),
    ("Linoleic acid", "fatty acid"),
    ("Germacrene B", "terpenoid (sesquiterpene)"),
    ("8-Hydroxyquinoline", "quinoline"),
    ("beta-Sitosterol", "phytosterol"),
    ("Amblyone", "terpenoid (triterpene)"),
    ("Calycopterin", "flavonoid"),
    ("Umbelliferone", "coumarin (hydroxycoumarin)"),
    ("Oleuropein", "secoiridoid glycoside"),
    ("Benzoxazolin-2(3H)-one", "benzoxazolinone"),
    ("Azelaic acid", "dicarboxylic acid"),
    ("1H-Indole-3-carboxaldehyde", "indole (heteroaromatic aldehyde)"),
    ("1H-Indole-3-carboxylic acid", "indole (heteroaromatic acid)"),
    ("1H-Indole-5-carboxylic acid", "indole (heteroaromatic acid)"),
    ("bis(2-ethylhexyl) phthalate", "aromatic diester"),
    ("6-methoxy-2-benzoxazolinone", "benzoxazolinone"),
    ("Dhurrin", "cyanogenic glycoside"),
    ("5-chloro-6-methoxy-1,3-benzoxazol-2(3H)-one", "benzoxazolinone"),
    ("2,4-dihydroxy-1,4-benzoxazin-3-one", "benzoxazinoid"),
    ("Parthenin", "sesquiterpene lactone"),
    ("Atropine", "tropane alkaloid"),
    ("3661", "tropane alkaloid"),
    ("5184", "tropane alkaloid"),
    ("Leptospermone", "triketone (natural HPPD inhibitor)"),
    ("Grandiflorone", "triketone (natural HPPD inhibitor)"),
    ("Flavesone", "triketone (natural HPPD inhibitor)"),
    ("3-hydroxy-L-tyrosine", "non-protein amino acid"),
    ("Citral", "terpenoid (monoterpene aldehyde)"),
    ("Juglone", "naphthoquinone"),
    ("Ethyl 2-methylacetoacetate", "beta-keto ester"),
    ("Dehydrozaluzanin C", "sesquiterpene lactone"),
    ("Camphene", "terpenoid (monoterpene)"),
    ("Indole-3-acetic acid", "plant hormone (response marker, not an allelochemical)"),
    ("Abscisic acid", "plant hormone (response marker, not an allelochemical)"),
    ("Ethylene", "plant hormone / gas (response marker, not an allelochemical)"),
    ("Proline", "amino acid (stress-response marker, not an allelochemical)"),
    ("DIMBOA", "benzoxazinoid (acronym not expanded in the source)"),
]


def herbicide_rows():
    """Return one row per representative herbicide in the HRAC target table."""
    rows = []
    with HRAC_TABLE.open(encoding = "utf-8-sig", newline = "") as stream:
        for record in csv.reader(stream):
            if len(record) < 4:
                continue
            group, _, _, representatives = record[:4]
            if not group.strip().isdigit() or not representatives.strip():
                continue
            if representatives.strip().lower().startswith("from "):
                continue
            # Split on a comma followed by a space and a letter, so a name
            # that contains a comma, such as 2,4-D, stays in one piece.
            for name in re.split(r",\s+(?=[A-Za-z])", representatives):
                name = name.strip()
                if name and not any(row["query"] == name for row in rows):
                    rows.append({
                        "query": name,
                        "chemical_group": "herbicide",
                        "subgroup": "hrac",
                        "hrac_group": group.strip(),
                        "source_note": "HRAC target table representative herbicide",
                        "compound_class": "synthetic herbicide",
                    })
    return rows


def natural_rows():
    """Return one row per named natural product."""
    rows = []
    for name, compound_class in NATURAL_PRODUCTS:
        rows.append({
            "query": name,
            "chemical_group": "natural_product",
            "subgroup": "allelochemical",
            "hrac_group": "",
            "source_note": "named allelochemical, see notes/CURATED_COMPOUNDS.md",
            "compound_class": compound_class,
        })
    return rows


def main() -> None:
    rows = herbicide_rows() + natural_rows()
    OUTPUT.parent.mkdir(parents = True, exist_ok = True)
    # The pipeline's curated input has a fixed set of fields, so the compound
    # class is kept beside it rather than inside it.
    with OUTPUT.open("w", encoding = "utf-8", newline = "") as stream:
        writer = csv.DictWriter(stream, fieldnames = [
            "query", "chemical_group", "subgroup", "hrac_group", "source_note",
        ])
        writer.writeheader()
        writer.writerows(
            {field: row[field] for field in writer.fieldnames} for row in rows
        )
    with CLASSES.open("w", encoding = "utf-8", newline = "") as stream:
        writer = csv.DictWriter(stream, fieldnames = ["query", "compound_class"])
        writer.writeheader()
        writer.writerows(
            {"query": row["query"], "compound_class": row["compound_class"]} for row in rows
        )
    herbicides = sum(1 for row in rows if row["chemical_group"] == "herbicide")
    print(f"wrote {len(rows)} compounds to {OUTPUT}")
    print(f"  herbicides: {herbicides}")
    print(f"  natural products: {len(rows) - herbicides}")


if __name__ == "__main__":
    main()
