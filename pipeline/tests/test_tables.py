"""Typed native Parquet and dependency provenance contracts."""

import hashlib
import json
import os
from datetime import datetime, timedelta

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from agrotox.storage import save_table
from agrotox.tables import frame_from_rows, read_table


@pytest.fixture
def evidence_schema():
    return {
        "pubchem_cid": pl.Int64,
        "value_standardized": pl.Float64,
        "formulation_flag": pl.Boolean,
        "input_queries": pl.List(pl.String),
        "sources": pl.List(pl.Struct({
            "reference_number": pl.Int64, "source_name": pl.String, "source_url": pl.String,
        })),
    }


@pytest.mark.parametrize("kind", ["empty", "all-null", "populated"])
def test_parquet_preserves_explicit_schema_and_nested_provenance(tmp_path, evidence_schema, kind):
    rows = [] if kind == "empty" else [{field: None for field in evidence_schema}]
    if kind == "populated":
        rows = [{
            "pubchem_cid": 101, "value_standardized": 1.5, "formulation_flag": False,
            "input_queries": ["alpha", "101"],
            "sources": [
                {"reference_number": 1, "source_name": "Synthetic α", "source_url": None},
                {"reference_number": 2, "source_name": None, "source_url": "https://example.org"},
            ],
        }, {"pubchem_cid": None, "sources": [], "input_queries": []}]
    frame = frame_from_rows(rows, evidence_schema)
    path = tmp_path / "nested" / "evidence.parquet"
    save_table(path, frame, [], code_version = "test-version")
    assert frame.schema == evidence_schema
    assert_frame_equal(read_table(path, evidence_schema), frame)
    assert_frame_equal(pl.read_parquet(path), frame)
    metadata = json.loads(path.with_suffix(".metadata.json").read_text())
    assert metadata["row_count"] == len(rows)


def test_sidecar_hashes_all_supplied_dependencies_and_tracks_changes(tmp_path):
    sources = [tmp_path / name for name in [
        "alias.json", "metadata.json", "raw.json", "processed.parquet", "rules.yaml", "code.py",
    ]]
    for index, source in enumerate(sources):
        source.write_text(f"dependency {index}", encoding = "utf-8")
    before = {str(source): source.read_bytes() for source in sources}
    frame = frame_from_rows([{"value": 2.0}], {"value": pl.Float64})
    path = tmp_path / "output.parquet"
    save_table(path, frame, sources, code_version = "test-version")
    sidecar = path.with_suffix(".metadata.json")
    metadata = json.loads(sidecar.read_text())
    assert metadata["code_version"] == "test-version"
    assert metadata["row_count"] == 1
    assert metadata["input_hashes"] == {
        name: hashlib.sha256(content).hexdigest() for name, content in before.items()
    }
    generated = datetime.fromisoformat(metadata["generated_at"])
    assert generated.utcoffset() == timedelta(0)
    assert {str(source): source.read_bytes() for source in sources} == before
    sources[0].write_text("changed alias", encoding = "utf-8")
    save_table(path, frame, sources, code_version = "test-version")
    updated = json.loads(sidecar.read_text())
    assert updated["input_hashes"][str(sources[0])] != metadata["input_hashes"][str(sources[0])]
    for source in sources[1:]:
        assert updated["input_hashes"][str(source)] == metadata["input_hashes"][str(source)]


def test_missing_required_table_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_table(tmp_path / "missing.parquet")


@pytest.mark.parametrize("expected_schema", [
    {"cid": pl.Int64}, {"cid": pl.String}, {"other": pl.Float64},
    {"cid": pl.Float64, "extra": pl.String},
])
def test_read_schema_mismatch_raises_without_casting(tmp_path, expected_schema):
    path = tmp_path / "data.parquet"
    pl.DataFrame({"cid": [101.0, None]}).write_parquet(path)
    with pytest.raises(ValueError, match = "schema"):
        read_table(path, expected_schema)


def test_schema_order_is_checked(tmp_path):
    path = tmp_path / "data.parquet"
    pl.DataFrame({"first": [1], "second": [2]}).write_parquet(path)
    with pytest.raises(ValueError, match = "schema"):
        read_table(path, {"second": pl.Int64, "first": pl.Int64})


def test_invalid_numeric_text_is_not_coerced_to_null():
    with pytest.raises((TypeError, pl.exceptions.PolarsError)):
        frame_from_rows([{"value": "invalid"}], {"value": pl.Float64})


def test_corrupt_parquet_raises(tmp_path):
    path = tmp_path / "broken.parquet"
    path.write_bytes(b"not parquet")
    with pytest.raises(pl.exceptions.PolarsError):
        read_table(path)


def test_missing_dependency_preserves_existing_products(tmp_path):
    frame = frame_from_rows([], {"value": pl.Float64})
    path = tmp_path / "data.parquet"
    save_table(path, frame, [], code_version = "test")
    before = {file: file.read_bytes() for file in tmp_path.iterdir()}
    with pytest.raises(FileNotFoundError):
        save_table(path, frame, [tmp_path / "absent.json"], code_version = "test")
    assert {file: file.read_bytes() for file in tmp_path.iterdir()} == before


@pytest.mark.parametrize("source_kind", ["table", "sidecar"])
def test_output_cannot_overwrite_a_dependency(tmp_path, source_kind):
    path = tmp_path / "data.parquet"
    source = path if source_kind == "table" else path.with_suffix(".metadata.json")
    source.write_bytes(b"consumed evidence")
    with pytest.raises(ValueError, match = "dependency"):
        save_table(path, pl.DataFrame(), [source], code_version = "test")
    assert source.read_bytes() == b"consumed evidence"


def test_failed_parquet_replacement_preserves_previous_products(tmp_path, monkeypatch):
    path = tmp_path / "data.parquet"
    frame = frame_from_rows([{"value": 1.0}], {"value": pl.Float64})
    save_table(path, frame, [], code_version = "test")
    before = {file: file.read_bytes() for file in tmp_path.iterdir()}

    def fail(*args, **kwargs):
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError, match = "simulated replacement failure"):
        save_table(path, frame.clear(), [], code_version = "test")
    assert {file: file.read_bytes() for file in tmp_path.iterdir()} == before
