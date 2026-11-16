"""Availability summaries retain sparse endpoints without implying potency."""

import runpy
from pathlib import Path

import polars as pl
import pytest

ANALYSIS = Path(__file__).resolve().parents[2] / "analysis"


@pytest.mark.parametrize("script_name", ["distributions.py", "compare.py"])
def test_sparse_endpoint_flags_are_reported_as_availability(tmp_path, monkeypatch, script_name):
    monkeypatch.syspath_prepend(str(ANALYSIS))
    frame = pl.DataFrame({
        "chemical_group": ["herbicide", "natural_product"],
        "molecular_weight": [100.0, 80.0],
        "has_epa_NOAEL": [1, None],
        "has_epa_BMD": [None, None],
        "has_epa_BMDL": [1, 0],
    }, schema_overrides = {"has_epa_BMD": pl.Int64})
    path = tmp_path / "traits.parquet"
    frame.write_parquet(path)
    output = tmp_path / "result.csv"
    module = runpy.run_path(str(ANALYSIS / script_name))
    module["main"].__globals__.update(COMPOUNDS = path, OUTPUT = output)
    module["main"]()
    result = pl.read_csv(output)
    assert "has_epa_BMD" in result["trait"].to_list()
    assert result.filter(pl.col("trait").str.starts_with("has_"))["kind"].unique().to_list() == [
        "endpoint_availability",
    ]
    empty = result.filter(pl.col("trait") == "has_epa_BMD")
    if script_name == "distributions.py":
        assert empty["n_present"].to_list() == [0, 0]
        assert empty["median"].null_count() == 2
    else:
        assert empty["permutation_p"].to_list() == [None]
        assert empty["n_herbicide"].to_list() == [0]
        sparse = result.filter(pl.col("trait") == "has_epa_NOAEL").row(0, named = True)
        assert sparse["n_natural"] == 0
        assert sparse["median_difference"] is None


def test_molecular_atom_counts_remain_chemical_traits(monkeypatch):
    monkeypatch.syspath_prepend(str(ANALYSIS))
    from endpoint_analysis import trait_kind

    for name in ["hbond_donor_count", "hbond_acceptor_count", "heavy_atom_count",
                 "rotatable_bond_count", "defined_atom_stereo_count",
                 "isotope_atom_count", "covalent_unit_count"]:
        assert trait_kind(name) == "molecular_property"
    assert trait_kind("annotation_count") == "study_coverage"
