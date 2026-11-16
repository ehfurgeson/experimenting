"""Loss-aware source annotation extraction and stable content identities."""

import json
from copy import deepcopy

import pytest

from agrotox.parsers.pubchem import extract_values, flatten_sections


def flatten(payload, raw_file = "alpha.json", retrieved_at = "2026-01-01T00:00:00Z"):
    return flatten_sections(payload, cid = 101, raw_file = raw_file, retrieved_at = retrieved_at)


@pytest.mark.parametrize("value, expected", [
    ({"Number": 5, "Unit": "mg/L"}, [("5 mg/L", "Number")]),
    ({"Number": [5], "Unit": "mg/L"}, [("5 mg/L", "Number")]),
    ({"Number": -5, "Unit": "mg/L"}, [("-5 mg/L", "Number")]),
    ({"Number": [3, 5], "Unit": "mg/L"}, [("3, 5 mg/L", "NumberArray")]),
    ({"Number": 0.5}, [("0.5", "Number")]),
    ({"StringWithMarkup": [{"String": ">10 mg/kg"}]}, [(">10 mg/kg", "StringWithMarkup")]),
    ({"StringWithMarkup": [{"String": "α"}, {"String": "β"}]},
     [("α", "StringWithMarkup"), ("β", "StringWithMarkup")]),
    ("narrative", [("narrative", "String")]),
    (None, [("null", "unknown")]),
    ({}, [("{}", "unknown")]),
])
def test_value_representations(value, expected):
    assert extract_values(value) == expected


@pytest.mark.parametrize("value, preserved", [
    ({"CustomShape": {"x": 1}}, {"x": 1}),
    ({"Number": []}, {"Number": [], "Unit": None}),
    ({"Number": [3, "unknown"], "Unit": "mg/L"}, {"Number": [3, "unknown"], "Unit": "mg/L"}),
    ({"StringWithMarkup": []}, []),
    ({"StringWithMarkup": [{"Unexpected": "keep me"}]}, {"Unexpected": "keep me"}),
    (["unexpected", {"nested": 1}], ["unexpected", {"nested": 1}]),
])
def test_unsupported_shapes_are_serialized(value, preserved):
    extracted = extract_values(value)
    assert len(extracted) == 1
    decoded = json.loads(extracted[0][0])
    assert decoded == preserved


@pytest.mark.parametrize("synthetic_record", ["alpha"], indirect = True)
def test_alpha_has_six_annotations_with_context_and_provenance(synthetic_record):
    original = deepcopy(synthetic_record)
    rows = flatten(synthetic_record)
    assert len(rows) == 6
    first = rows[0]
    assert first["compound_id"] == "PUBCHEM:101"
    assert first["section_path"] == ["Toxicity", "Acute Toxicity"]
    assert first["record_title"] == "Synthetic Alpha"
    assert first["information_name"] == "LD50"
    assert first["description"] == "rat oral"
    assert first["reference_numbers"] == [1, 2]
    assert {source["source_url"] for source in first["sources"]} == {
        "https://example.org/a", "https://example.org/b",
    }
    assert {source["source_name"] for source in first["sources"]} == {
        "Synthetic source A", "Synthetic source B",
    }
    assert first["raw_file"] == "alpha.json"
    assert first["retrieved_at"] == "2026-01-01T00:00:00Z"
    information = synthetic_record["Record"]["Section"][0]["Section"][0]["Information"]
    assert json.loads(first["information_json"]) == information[0]
    assert rows[4]["value_kind"] == "NumberArray"
    assert rows[5]["value_kind"] == "CustomShape"
    assert synthetic_record == original


@pytest.mark.parametrize("synthetic_record", ["alpha"], indirect = True)
def test_ids_survive_information_section_and_reference_reordering(synthetic_record):
    record = synthetic_record["Record"]
    branch = record["Section"][0]["Section"][0]
    record["Section"].append({"TOCHeading": "Other", "Information": [{"Value": "note"}]})
    before = {row["value_raw"]: row["annotation_id"] for row in flatten(synthetic_record)}
    branch["Information"].reverse()
    record["Section"].reverse()
    record["Reference"].reverse()
    next(info for info in branch["Information"] if isinstance(info.get("ReferenceNumber"), list))[
        "ReferenceNumber"
    ].reverse()
    after = {row["value_raw"]: row["annotation_id"] for row in flatten(synthetic_record)}
    assert before == after
    relocated = flatten(synthetic_record, raw_file = "copied.json", retrieved_at = "2026-02-01T00:00:00Z")
    assert {row["value_raw"]: row["annotation_id"] for row in relocated} == before


def test_multiple_and_dangling_references_keep_all_distinct_sources():
    payload = {"Record": {
        "Reference": [
            {"ReferenceNumber": 1, "SourceName": "A", "URL": "https://example.org/a"},
            {"ReferenceNumber": 1, "Name": "B", "URL": "https://example.org/b", "LicenseNote": "keep"},
        ],
        "Section": [{"TOCHeading": "Toxicity", "Section": None, "Information": [{
            "Value": "text", "ReferenceNumber": [99, 1, 1], "URL": "https://example.org/info",
        }]}],
    }}
    row = flatten(payload)[0]
    assert row["reference_numbers"] == [1, 99]
    assert len(row["sources"]) == 3
    assert row["information_url"] == "https://example.org/info"
    assert any(source["source_name"] is None and source["reference_number"] == 99 for source in row["sources"])
    assert any(
        json.loads(source["reference_json"] or "{}").get("LicenseNote") == "keep"
        for source in row["sources"]
    )


@pytest.mark.parametrize("payload", [
    {"Record": {}}, {"Record": {"Section": None}},
    {"Record": {"Reference": None, "Section": [{"Section": None, "Information": None}]}},
])
def test_missing_and_null_sections_are_empty(payload):
    assert flatten(payload) == []


def test_repeated_content_keeps_rows_and_shared_identity():
    info = {"Name": "Narrative", "Value": "same"}
    payload = {"Record": {"Section": [{"Information": [info, deepcopy(info)]}]}}
    rows = flatten(payload)
    assert len(rows) == 2
    assert rows[0]["annotation_id"] == rows[1]["annotation_id"]


@pytest.mark.parametrize("change", ["value", "context", "source", "compound"])
def test_semantic_changes_change_annotation_identity(change):
    payload = {"Record": {
        "Reference": [{"ReferenceNumber": 1, "SourceName": "A"}],
        "Section": [{"TOCHeading": "Toxicity", "Information": [{
            "Name": "LD50", "Description": "rat oral", "Value": "1 g/kg", "ReferenceNumber": 1,
        }]}],
    }}
    before = flatten(payload)[0]["annotation_id"]
    info = payload["Record"]["Section"][0]["Information"][0]
    if change == "value":
        info["Value"] = "2 g/kg"
    elif change == "context":
        info["Description"] = "mouse oral"
    elif change == "source":
        payload["Record"]["Reference"][0]["SourceName"] = "B"
    cid = 102 if change == "compound" else 101
    assert flatten_sections(payload, cid = cid, raw_file = "alpha.json", retrieved_at = "now")[0]["annotation_id"] != before


def test_markup_and_unrecognized_information_metadata_are_preserved():
    info = {
        "Value": {"StringWithMarkup": [{"String": "text", "Markup": [{"Start": 0, "Length": 4}]}]},
        "UnrecognizedMetadata": {"note": "retain me"},
    }
    row = flatten({"Record": {"Section": [{"Information": [info]}]}})[0]
    assert json.loads(row["information_json"]) == info


@pytest.mark.parametrize("payload", [
    {"Record": {"Section": "invalid"}},
    {"Record": {"Section": [{"Information": "invalid"}]}},
])
def test_malformed_traversal_containers_raise(payload):
    with pytest.raises(ValueError):
        flatten(payload)


def test_each_value_representation_is_retained():
    value = {"StringWithMarkup": [{"String": "text"}], "CustomShape": {"note": "also keep"}}
    rows = flatten({"Record": {"Section": [{"Information": [{"Value": value}]}]}})
    assert len(rows) == 2
    assert {row["value_kind"] for row in rows} == {"StringWithMarkup", "CustomShape"}
    assert len({row["annotation_id"] for row in rows}) == 2
    assert all(json.loads(row["information_json"])["Value"] == value for row in rows)
