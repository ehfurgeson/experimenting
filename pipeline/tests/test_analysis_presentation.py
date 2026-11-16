"""Chart data preserve selected denominators, missingness, and empirical CDFs."""

from pathlib import Path

import polars as pl
import pytest

ANALYSIS = Path(__file__).resolve().parents[2] / "analysis"


def test_endpoint_distribution_orders_seven_types_and_preserves_unknowns(monkeypatch):
    monkeypatch.syspath_prepend(str(ANALYSIS))
    from presentation import ENDPOINTS, endpoint_distribution

    rows = [{"chemical_group": "herbicide"}, {"chemical_group": "herbicide"},
            {"chemical_group": "natural_product"}]
    for _, policy, _ in ENDPOINTS:
        for row, value in zip(rows, [1, None, 0], strict = True):
            row[f"has_{policy}"] = value
    result = endpoint_distribution(pl.DataFrame(rows))
    assert list(dict.fromkeys(row["endpoint"] for row in result)) == [
        "LD50", "LC50", "EC50", "NOAEL", "LOAEL", "BMD", "BMDL",
    ]
    ld50 = [row for row in result if row["endpoint"] == "LD50"]
    herb = {row["state"]: row for row in ld50 if row["group"] == "Herbicides"}
    assert herb["Evidence found"]["count"] == 1
    assert herb["Unassessed"]["count"] == 1
    assert herb["Evidence found"]["fraction"] == 0.5
    assert sum(row["fraction"] for row in herb.values()) == 1
    assert herb["Evidence found"]["selected"] == 2
    assert herb["Evidence found"]["assessed"] == 1
    with pytest.raises(ValueError, match = "source"):
        endpoint_distribution(pl.DataFrame(rows), "invalid")


def test_ecdf_uses_group_denominators_and_excludes_nonfinite_values(monkeypatch):
    monkeypatch.syspath_prepend(str(ANALYSIS))
    from presentation import empirical_distributions

    frame = pl.DataFrame({"chemical_group": ["herbicide"] * 4 + ["natural_product"],
                          "xlogp": [1.0, 1.0, 3.0, float("inf"), None]})
    result = empirical_distributions(frame, ["xlogp"])
    assert len(result) == 2
    assert [row["cdf"] for row in result] == [pytest.approx(2 / 3), 1.0]
    assert {row["n"] for row in result} == {3}


def test_changed_prepared_products_are_rejected(tmp_path, monkeypatch):
    import hashlib
    import json

    monkeypatch.syspath_prepend(str(ANALYSIS))
    from presentation import load_results

    path = tmp_path / "compound_traits.parquet"
    path.write_bytes(b"original")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "output_hashes": {str(path): hashlib.sha256(b"original").hexdigest()},
    }))
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match = "rebuild"):
        load_results(tmp_path)
