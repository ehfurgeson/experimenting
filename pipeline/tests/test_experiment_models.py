"""Endpoint availability modeling uses training-only preprocessing."""

import runpy
from pathlib import Path

import pytest

ANALYSIS = Path(__file__).resolve().parents[2] / "analysis"


def statistics(monkeypatch):
    monkeypatch.syspath_prepend(str(ANALYSIS))
    return runpy.run_path(str(ANALYSIS / "stats.py"))


def test_scaling_can_transform_new_compounds_in_training_coordinates(monkeypatch):
    module = statistics(monkeypatch)
    scaled, parameters = module["standardize"]([{"x": 0.0}, {"x": 2.0}], ["x"])
    assert isinstance(parameters, dict)
    held_out, reused = module["standardize"]([{"x": 3.0}], ["x"], parameters = parameters)
    assert held_out[0]["x"] == pytest.approx(2 ** 0.5)
    assert reused == parameters
    assert scaled[0]["x"] < 0 < scaled[1]["x"]


def test_rare_or_single_class_targets_have_no_cross_validated_accuracy(monkeypatch):
    module = statistics(monkeypatch)
    rows = [{"x": float(i), "target": int(i == 9)} for i in range(10)]
    assert module["cross_validated_accuracy"](rows, ["x"], "target") is None
    assert module["cross_validated_accuracy"](rows[:-1], ["x"], "target") is None


def test_separable_target_has_reproducible_held_out_accuracy(monkeypatch):
    module = statistics(monkeypatch)
    rows = [{"x": float(label), "target": label} for label in [0, 1] for _ in range(5)]
    accuracy = module["cross_validated_accuracy"](rows, ["x"], "target")
    assert accuracy == 1.0
    assert module["cross_validated_accuracy"](rows, ["x"], "target") == accuracy


def test_classifiers_include_chronic_targets_without_imputing_labels(tmp_path, monkeypatch):
    import polars as pl

    monkeypatch.syspath_prepend(str(ANALYSIS))
    module = runpy.run_path(str(ANALYSIS / "classifiers.py"))
    columns = {name: [1.0, 2.0, 3.0] for name in module["FEATURES"]}
    columns.update({
        "chemical_group": ["herbicide", "natural_product", "natural_product"],
        "has_epa_NOAEL": [1, None, 0], "has_epa_BMD": [0, 0, None],
        "has_epa_BMDL": [1, 0, None], "has_mammal_oral_ld50": [1, 0, None],
    })
    path = tmp_path / "traits.parquet"
    pl.DataFrame(columns).write_parquet(path)
    output = tmp_path / "classifiers.csv"
    module["main"].__globals__.update(COMPOUNDS = path, OUTPUT = output)
    module["main"]()
    results = pl.read_csv(output)
    assert "epa_NOAEL_availability" in results["model"].to_list()
    noael = results.filter(pl.col("model") == "epa_NOAEL_availability").row(0, named = True)
    assert noael["n"] == 2
    assert noael["positives"] == 1
    assert noael["accuracy"] is None
    bmd = results.filter(pl.col("model") == "epa_BMD_availability").row(0, named = True)
    assert bmd["status"] == "insufficient_class_support"
    assert bmd["positives"] == 0
