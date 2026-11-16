"""The presentation rebuild reads caches without changing local experiments."""

import runpy
from pathlib import Path

import polars as pl
import pytest

ANALYSIS = Path(__file__).resolve().parents[2] / "analysis"


def test_trait_builder_uses_only_cached_descriptors(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ANALYSIS))
    module = runpy.run_path(str(ANALYSIS / "build_traits.py"))
    import urllib.request

    def no_network(*args, **kwargs):
        pytest.fail("Offline analysis attempted descriptor retrieval")

    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    module["computed_properties"].__globals__["EXTRA"] = tmp_path
    assert module["computed_properties"](101) == {}


def test_coverage_exports_to_its_output_directory(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ANALYSIS))
    from endpoint_analysis import export_epa

    from agrotox.workflow import OfflineAnalysis

    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    (source / "compounds.csv").write_text("query\nalpha\n")
    definitions = tmp_path / "rules.yaml"
    definitions.write_text("LD50: {endpoint: LD50}\n")
    analysis = OfflineAnalysis(tables = {"example": pl.DataFrame({"n": [1]})}, dependencies = {})
    export_epa(analysis, source, definitions, output_data = output)
    assert (output / "epa_analysis" / "example.parquet").exists()
    assert not (source / "epa_analysis").exists()


def test_rebuild_preserves_inputs_and_exports_independent_products(
    snapshot_cache, tmp_path_factory, monkeypatch,
):
    import json

    monkeypatch.syspath_prepend(str(ANALYSIS))
    from rebuild import rebuild

    (snapshot_cache / "compounds.csv").write_text(
        "query,chemical_group\nalpha,herbicide\nbeta,natural_product\ngamma,natural_product\n"
    )
    (snapshot_cache / "compound_classes.csv").write_text("query,compound_class\nalpha,synthetic\n")
    before = {path: path.read_bytes() for path in snapshot_cache.rglob("*") if path.is_file()}
    output = tmp_path_factory.mktemp("presentation")
    manifest = rebuild(snapshot_cache, output)
    assert all(path.read_bytes() == content for path, content in before.items())
    assert (output / "classifiers.csv").exists()
    assert pl.read_parquet(output / "compound_traits.parquet").height == 3
    assert json.loads((output / "manifest.json").read_text())["source"] == str(snapshot_cache.resolve())
    assert len(manifest["endpoint_policies"]) == 8
    assert not manifest["epa_available"]
    with pytest.raises(ValueError, match = "outside"):
        rebuild(snapshot_cache, snapshot_cache / "nested")
