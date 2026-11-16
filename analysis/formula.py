"""Conservative composition features for flat, neutral molecular formulas."""

import re
from collections import Counter

from rdkit import Chem

ELEMENTS = ("C", "H", "N", "O", "P", "S", "F", "Cl", "Br", "I", "B", "Si")
FORMULA_FEATURES = ["element_count", "atom_count", "other_atom_count"] + [
    f"formula_{element}_{kind}" for element in ELEMENTS for kind in ("count", "fraction")
]


def formula_features(formula):
    """Return null features unless the entire neutral formula is supported."""
    empty = dict.fromkeys([*FORMULA_FEATURES, "formula_composition"])
    if formula is None or isinstance(formula, str) and not formula.strip():
        return {"formula_status": "missing", **empty}
    if not isinstance(formula, str) or not re.fullmatch(
        r"(?:[A-Z][a-z]?(?:[1-9][0-9]*)?)+", formula
    ):
        return {"formula_status": "unsupported", **empty}
    symbols = {Chem.GetPeriodicTable().GetElementSymbol(i) for i in range(1, 119)}
    counts = Counter()
    for element, number in re.findall(r"([A-Z][a-z]?)([0-9]*)", formula):
        if element not in symbols:
            return {"formula_status": "unsupported", **empty}
        counts[element] += int(number or 1)
    total = sum(counts.values())
    result = {
        "formula_status": "valid", "element_count": len(counts), "atom_count": total,
        "formula_composition": ";".join(f"{e}:{n}" for e, n in sorted(counts.items())),
        "other_atom_count": sum(n for element, n in counts.items() if element not in ELEMENTS),
    }
    for element in ELEMENTS:
        result[f"formula_{element}_count"] = counts[element]
        result[f"formula_{element}_fraction"] = counts[element] / total
    return result
