"""Compound reconciliation from curated queries and hand-built snapshots."""

from copy import deepcopy

import polars as pl
import pytest

from agrotox.identity import compound_key, reconcile_compounds
from agrotox.inputs import query_key
from agrotox.tables import compound_table


def snapshot(cid = 101, properties = None, status = "found"):
    return {
        "cid": cid,
        "properties": {"CID": cid, **(properties or {})},
        "metadata": {"toxicity_status": status},
    }


def test_merge_aliases_and_preserve_unresolved():
    queries = [
        {"query": "Alpha", "chemical_group": "herbicide", "source_note": "first"},
        {"query": "00101", "subgroup": "synthetic", "source_note": "second"},
        {"query": "unknown", "chemical_group": "natural_product"},
    ]
    snapshots = {name: snapshot() for name in ["Alpha", "00101"]}
    original = deepcopy((queries, snapshots))
    rows = reconcile_compounds(queries, snapshots)
    assert len(rows) == 2
    alpha, unknown = rows
    assert alpha["compound_id"] == "PUBCHEM:101"
    assert alpha["pubchem_cid"] == 101
    assert alpha["input_queries"] == ["Alpha", "00101"]
    assert alpha["chemical_group"] == "herbicide"
    assert alpha["subgroup"] == "synthetic"
    assert alpha["source_notes"] == ["first", "second"]
    assert alpha["resolution_status"] == "resolved"
    assert alpha["toxicity_status"] == "found"
    assert unknown["compound_id"] == f"QUERY:{query_key('unknown')}"
    assert unknown["pubchem_cid"] is None
    assert unknown["resolution_status"] == "unresolved"
    assert unknown["toxicity_status"] == "not_retrieved"
    assert (queries, snapshots) == original


@pytest.mark.parametrize("field", ["chemical_group", "subgroup", "hrac_group"])
def test_conflicting_alias_classifications(field):
    with pytest.raises(ValueError, match = field):
        reconcile_compounds(
            [{"query": "alpha", field: "one"}, {"query": "101", field: "two"}],
            {"alpha": snapshot(), "101": snapshot()},
        )


def test_equivalent_unresolved_queries_keep_aliases_notes_and_enrichment():
    rows = reconcile_compounds([
        {"query": " Alpha ", "source_note": " one ", "chemical_group": ""},
        {"query": "alpha", "source_note": "two", "chemical_group": "h"},
        {"query": "Alpha", "source_note": "one"},
    ], {})
    assert len(rows) == 1
    assert rows[0]["input_queries"] == ["Alpha", "alpha"]
    assert rows[0]["source_notes"] == ["one", "two"]
    assert rows[0]["chemical_group"] == "h"


def test_different_cids_remain_distinct():
    queries = [{"query": name} for name in ["acid", "salt", "ester"]]
    snapshots = {name: snapshot(cid) for name, cid in [("acid", 101), ("salt", 102), ("ester", 103)]}
    assert [row["pubchem_cid"] for row in reconcile_compounds(queries, snapshots)] == [101, 102, 103]


def test_structures_and_numeric_weight():
    props = {
        "Title": "Alpha", "SMILES": "C[C@H](O)F", "ConnectivitySMILES": "CC(O)F",
        "InChI": "synthetic-inchi", "InChIKey": "synthetic-key",
        "MolecularFormula": "C2H5FO", "MolecularWeight": "64.06", "IUPACName": "synthetic",
    }
    row = reconcile_compounds([{"query": "alpha"}], {"alpha": snapshot(properties = props)})[0]
    assert row["preferred_name"] == "Alpha"
    assert row["smiles"] == "C[C@H](O)F"
    assert row["connectivity_smiles"] == "CC(O)F"
    assert row["molecular_weight"] == 64.06
    assert row["inchi"] == "synthetic-inchi"
    assert row["inchikey"] == "synthetic-key"
    assert row["molecular_formula"] == "C2H5FO"
    assert row["iupac_name"] == "synthetic"


@pytest.mark.parametrize("properties, smiles, connectivity", [
    ({}, None, None),
    ({"IsomericSMILES": "stereo", "CanonicalSMILES": "flat"}, "stereo", "flat"),
    ({"ConnectivitySMILES": "flat"}, None, "flat"),
    ({"CanonicalSMILES": "flat"}, None, "flat"),
    ({"SMILES": "new", "IsomericSMILES": "old"}, "new", None),
])
def test_missing_and_legacy_structure_fields(properties, smiles, connectivity):
    row = reconcile_compounds([{"query": "alpha"}], {
        "alpha": snapshot(properties = properties)
    })[0]
    assert row["smiles"] == smiles
    assert row["connectivity_smiles"] == connectivity
    assert row["molecular_weight"] is None


@pytest.mark.parametrize("status", ["found", "missing", "pending", "not_retrieved"])
def test_explicit_toxicity_status(status):
    row = reconcile_compounds([{"query": "alpha"}], {"alpha": snapshot(status = status)})[0]
    assert row["toxicity_status"] == status


@pytest.mark.parametrize("cid", [0, -1, True, "101", 1.5])
def test_invalid_resolved_cids(cid):
    with pytest.raises(ValueError, match = "CID"):
        compound_key(cid, "alpha")


def test_snapshot_cid_mismatch():
    with pytest.raises(ValueError, match = "CID"):
        reconcile_compounds([{"query": "alpha"}], {
            "alpha": snapshot(properties = {"CID": 102})
        })


@pytest.mark.parametrize("weight", ["invalid", "NaN", "inf", -1, 0, True])
def test_invalid_molecular_weight(weight):
    with pytest.raises(ValueError, match = "molecular_weight"):
        reconcile_compounds([{"query": "alpha"}], {
            "alpha": snapshot(properties = {"MolecularWeight": weight})
        })


def test_incompatible_snapshots_are_not_arbitrarily_selected():
    with pytest.raises(ValueError, match = "smiles"):
        reconcile_compounds([{"query": "alpha"}, {"query": "101"}], {
            "alpha": snapshot(properties = {"SMILES": "C"}),
            "101": snapshot(properties = {"SMILES": "CC"}),
        })


def test_typed_compound_tables():
    empty = compound_table([])
    rows = reconcile_compounds([{"query": "unknown"}], {})
    frame = compound_table(rows)
    assert empty.schema == frame.schema
    assert empty.height == 0
    assert frame.schema["pubchem_cid"] == pl.Int64
    assert frame.schema["molecular_weight"] == pl.Float64
    assert frame.schema["input_queries"] == pl.List(pl.String)
    assert frame.schema["source_notes"] == pl.List(pl.String)
    assert frame.to_dicts() == rows


def test_empty_selection_ignores_unselected_snapshots():
    assert reconcile_compounds([], {"unselected": snapshot()}) == []


def test_compatible_labels_and_missing_properties_are_enriched():
    queries = [
        {"query": "alpha", "chemical_group": " h ", "subgroup": ""},
        {"query": "101", "chemical_group": "h", "subgroup": "s", "hrac_group": "1"},
    ]
    rows = reconcile_compounds(queries, {
        "alpha": snapshot(), "101": snapshot(properties = {"Title": "Alpha"}),
    })
    assert rows[0]["preferred_name"] == "Alpha"
    assert rows[0]["chemical_group"] == "h"
    assert rows[0]["subgroup"] == "s"
    assert rows[0]["hrac_group"] == "1"


def test_unresolved_cid_equivalents_share_identity():
    rows = reconcile_compounds([{"query": "00101"}, {"query": "101"}], {})
    assert len(rows) == 1
    assert rows[0]["input_queries"] == ["00101", "101"]
    assert rows[0]["pubchem_cid"] is None
    assert rows[0]["compound_id"] == compound_key(None, "101")


def test_status_conflict_is_visible():
    with pytest.raises(ValueError, match = "toxicity_status"):
        reconcile_compounds([{"query": "alpha"}, {"query": "101"}], {
            "alpha": snapshot(status = "pending"), "101": snapshot(status = "found"),
        })


def test_invalid_status():
    with pytest.raises(ValueError, match = "toxicity_status"):
        reconcile_compounds([{"query": "alpha"}], {"alpha": snapshot(status = "unknown")})


def test_metadata_cid_mismatch():
    record = snapshot()
    record["metadata"]["cid"] = 102
    with pytest.raises(ValueError, match = "CID"):
        reconcile_compounds([{"query": "alpha"}], {"alpha": record})


def test_structure_fields_require_text():
    with pytest.raises(TypeError, match = "smiles"):
        reconcile_compounds([{"query": "alpha"}], {
            "alpha": snapshot(properties = {"SMILES": 123})
        })
