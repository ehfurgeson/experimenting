from copy import deepcopy
from pathlib import Path

import pytest

from agrotox.coverage import load_definitions, validate_definitions


@pytest.mark.parametrize("text", [
    "[", "", "[]", "{}", "bad: null", "bad: []", "1: {endpoint: LD50}",
    "bad: {endpoint: UNKNOWN}", "bad: {species: rat}",
    "bad: {endpoint: LD50, typo: rat}",
    "bad: {endpoint: LD50, endpoint: LC50}",
    "bad: {endpoint: LD50}\nbad: {endpoint: LC50}",
    "bad: {endpoint: LD50, standard_unit: mg/L}",
    "bad: {endpoint: LC50, standard_unit: ug/L}",
    "bad: {endpoint: LD50, preferred_duration_hours: -1}",
    "bad: {endpoint: LD50, preferred_duration_hours: 0}",
    "bad: {endpoint: LD50, preferred_duration_hours: true}",
    "bad: {endpoint: LD50, preferred_duration_hours: '96'}",
    "bad: {endpoint: LD50, preferred_duration_hours: .inf}",
    "bad: {endpoint: LD50, preferred_duration_hours: .nan}",
    "bad: {endpoint: LD50, species: null}",
    "bad: {endpoint: LD50, species: []}",
    "bad: {endpoint: LD50, species: ' '}",
    "bad: {endpoint: LD50, label: 1}",
])
def test_invalid_yaml(tmp_path, text):
    path = tmp_path / "rules.yaml"
    path.write_text(text)
    with pytest.raises(ValueError):
        load_definitions(path)


def test_synthetic_definitions_and_display_metadata():
    fixtures = Path(__file__).parent / "fixtures"
    endpoints = load_definitions(fixtures / "endpoints.yaml")
    comparisons = load_definitions(fixtures / "comparisons.yaml")
    assert endpoints["fish_lc50"]["organism_group"] == "fish"
    assert comparisons["trout_96h"]["preferred_duration_hours"] == 96
    assert comparisons["trout_96h"]["label"] == "Synthetic trout comparison"
    original = deepcopy(comparisons)
    validated = validate_definitions(comparisons)
    assert validated == original == comparisons
    validated["trout_96h"]["label"] = "Changed"
    assert comparisons == original


@pytest.mark.parametrize("value", [None, [], {}, {"": {"endpoint": "LD50"}}])
def test_invalid_python_definitions(value):
    with pytest.raises(ValueError):
        validate_definitions(value)


def test_overflowing_duration_rejected():
    with pytest.raises(ValueError):
        validate_definitions({"bad": {"endpoint": "LD50", "preferred_duration_hours": 10**400}})
