"""Selection membership cannot silently become an activity or origin label."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from labels import attach_labels, selection_target


def compound(identity = "a", structure = "CCO"):
    return {"compound_id": identity, "chemical_group": "herbicide",
            "canonical_structure": structure}


def review(identity = "a", activity = "active", origin = "natural"):
    return {"compound_id": identity, "natural_origin": origin,
            "origin_reference": "doi:natural-occurrence", "herbicidal_activity": activity,
            "activity_reference": "doi:plant-assay", "activity_context": "species; dose; duration",
            "activity_policy": "whole_plant_inhibition_review_v1"}


def test_natural_herbicide_is_both_natural_and_active():
    row = attach_labels([compound()], [review()])[0]
    assert row["activity_target"] == 1
    assert row["origin_target"] == 1
    assert row["activity_reference"] == "doi:plant-assay"


def test_absent_labels_stay_unknown_even_for_selected_herbicides():
    row = attach_labels([compound()], [])[0]
    assert row["activity_target"] is None
    assert row["origin_target"] is None
    assert selection_target(row) == 1
    assert selection_target({"chemical_group": "other"}) is None


def test_reviewed_inactive_natural_compound_is_explicit_negative():
    row = attach_labels([compound()], [review(activity = "inactive")])[0]
    assert row["activity_target"] == 0
    assert row["origin_target"] == 1


@pytest.mark.parametrize("field,value,match", [
    ("herbicidal_activity", "no_evidence", "herbicidal_activity"),
    ("natural_origin", "plant", "natural_origin"),
    ("origin_reference", "", "origin_reference"),
    ("activity_reference", " ", "activity_reference"),
    ("activity_context", "", "activity_context"),
    ("activity_policy", "", "activity_policy"),
    ("surprise", "x", "Unknown label fields"),
    ("compound_id", "orphan", "Unknown compound_id"),
])
def test_invalid_review_rows_raise_explicit_errors(field, value, match):
    label = {**review(), field: value}
    with pytest.raises(ValueError, match = match):
        attach_labels([compound()], [label])


def test_duplicate_compound_or_review_ids_are_rejected():
    with pytest.raises(ValueError, match = "Duplicate compound_id"):
        attach_labels([compound(), compound()], [])
    with pytest.raises(ValueError, match = "Duplicate label"):
        attach_labels([compound()], [review(), review()])


def test_conflicting_labels_for_same_structure_are_rejected():
    with pytest.raises(ValueError, match = "Conflicting.*structure"):
        attach_labels([compound(), compound("b")], [review(), review("b", activity = "inactive")])


def test_incompatible_activity_policies_cannot_be_pooled():
    with pytest.raises(ValueError, match = "one activity_policy"):
        attach_labels([compound(), compound("b", "COC")],
                      [review(), {**review("b"), "activity_policy": "other_assay"}])


def test_unknown_reviews_need_no_references_and_keep_no_target():
    row = attach_labels([compound()], [{"compound_id": "a"}])[0]
    assert row["activity_target"] is None
    assert row["origin_target"] is None
