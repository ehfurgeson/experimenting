"""Composition is complete or explicitly unavailable, never partially parsed."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from formula import FORMULA_FEATURES, formula_features


@pytest.mark.parametrize("formula,elements,atoms", [
    ("C6H12O6", 3, 24), ("CH3COOH", 3, 8), ("NaCl", 2, 2),
    ("C8H6Cl2O3", 4, 19), ("He", 1, 1),
])
def test_valid_flat_formula_has_exact_composition(formula, elements, atoms):
    result = formula_features(formula)
    assert result["formula_status"] == "valid"
    assert result["element_count"] == elements
    assert result["atom_count"] == atoms


def test_repeated_tokens_accumulate_and_absent_elements_are_zero():
    result = formula_features("CH3COOH")
    assert result["formula_C_count"] == 2
    assert result["formula_H_fraction"] == 0.5
    assert result["formula_Cl_count"] == 0
    assert formula_features("NaCl")["other_atom_count"] == 1


@pytest.mark.parametrize("formula,status", [
    (None, "missing"), ("", "missing"), ("  ", "missing"), (4, "unsupported"),
    ("C0H2", "unsupported"), ("Xx2", "unsupported"), ("C6H12O6?", "unsupported"),
    ("CuSO4.5H2O", "unsupported"), ("Ca(OH)2", "unsupported"),
    ("[13C]H4", "unsupported"), ("NH4+", "unsupported"), ("C01", "unsupported"),
])
def test_unsupported_or_missing_formula_never_yields_partial_counts(formula, status):
    result = formula_features(formula)
    assert result["formula_status"] == status
    assert all(result[feature] is None for feature in FORMULA_FEATURES)


def test_same_formula_has_same_features_regardless_of_isomer():
    assert formula_features("C2H6O") == formula_features("C2H6O")
    assert formula_features("C2H6O")["formula_O_fraction"] == pytest.approx(1 / 9)


def test_complete_composition_is_distinct_from_reduced_predictors():
    germanium, tin = formula_features("C4H12Ge"), formula_features("C4H12Sn")
    assert all(germanium[k] == tin[k] for k in FORMULA_FEATURES)
    assert germanium["formula_composition"] != tin["formula_composition"]
    assert formula_features("CH3COOH")["formula_composition"] == formula_features("C2H4O2")[
        "formula_composition"]
