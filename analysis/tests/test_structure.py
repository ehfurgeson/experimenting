"""Descriptors depend on chemistry alone and preserve failures for review."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from structure import DESCRIPTORS, FINGERPRINT_SIZE, screening_rules, structure_features


def test_ethanol_has_formula_descriptors_and_bounded_sa():
    result = structure_features("CCO")
    assert result["structure_status"] == "valid"
    assert result["derived_formula"] == "C2H6O"
    assert result["element_count"] == 3
    assert result["mw"] == pytest.approx(46.069, abs = .01)
    assert result["hbd"] == 1
    assert result["lipinski_violations"] == 0
    assert 1 <= result["sa_score"] <= 10
    assert len(result["fingerprint"]) == FINGERPRINT_SIZE
    assert set(result["fingerprint"]) <= {0, 1}
    assert result["scaffold"] == "ACYCLIC"


def test_equivalent_smiles_have_same_identity_fingerprint_and_scaffold():
    left, right = structure_features("Cc1ccccc1"), structure_features("c1ccccc1C")
    for key in ("canonical_structure", "structure_inchikey", "fingerprint", "scaffold"):
        assert left[key] == right[key]
    assert structure_features("Oc1ccccc1")["scaffold"] == left["scaffold"]
    assert structure_features("CCO")["canonical_structure"] != structure_features("COC")[
        "canonical_structure"]
    assert structure_features("CCO")["element_count"] == structure_features("COC")["element_count"]


@pytest.mark.parametrize("smiles,status", [
    (None, "missing"), ("", "missing"), ("  ", "missing"),
    ("invalid", "invalid_smiles"), (42, "invalid_smiles"),
    ("C.C", "multicomponent"), ("[Na+].[Cl-]", "multicomponent"),
    ("[Na+]", "unsupported_chemistry"), ("[CH3]", "unsupported_chemistry"),
])
def test_unusable_structures_have_explicit_status_and_null_descriptors(smiles, status):
    result = structure_features(smiles)
    assert result["structure_status"] == status
    assert all(result[key] is None for key in DESCRIPTORS)
    assert result["fingerprint"] is None
    assert result["scaffold"] is None


def test_rule_boundaries_are_inclusive_and_missing_inputs_stay_unknown():
    assert screening_rules(500, 3.5, 3, 12, 12) == {
        "lipinski_violations": 1, "tice_proxy_violations": 0}
    assert screening_rules(150, 3.5, 3, 2, 12)["tice_proxy_violations"] == 0
    assert screening_rules(500, 5, 5, 10, 12)["lipinski_violations"] == 0
    assert screening_rules(501, 5.1, 6, 11, 13)["lipinski_violations"] == 4
    assert screening_rules(149, 3.6, 4, 1, 13)["tice_proxy_violations"] == 5
    assert screening_rules(None, 2, 1, 2, 1) == {
        "lipinski_violations": None, "tice_proxy_violations": None}
