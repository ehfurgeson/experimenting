"""Shared fixtures and network blocking for offline tests."""

import json
from pathlib import Path

import pytest
import requests

from agrotox.storage import compound_path, query_path, write_json

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse = True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Pipeline tests must not use the network")

    monkeypatch.setattr(requests.sessions.Session, "request", blocked)


@pytest.fixture
def synthetic_record(request):
    """Load a fresh synthetic PUG-View payload for each parameterized case."""
    return json.loads((FIXTURES / f"{request.param}.json").read_text(encoding = "utf-8"))


@pytest.fixture
def curated_queries():
    return [
        {"query": "alpha", "chemical_group": "herbicide"},
        {"query": "beta", "chemical_group": "natural_product"},
        {"query": "gamma", "chemical_group": "natural_product"},
        {"query": "unknown", "chemical_group": "natural_product"},
    ]


@pytest.fixture
def snapshot_cache(tmp_path, curated_queries):
    """Seed validated synthetic bundles; Unknown intentionally has no alias."""
    for query, cid in zip(curated_queries[:3], [101, 102, 103], strict = True):
        name = query["query"]
        write_json(query_path(tmp_path, name), {
            "query": name, "cid": cid, "input_metadata": query,
        })
        write_json(compound_path(tmp_path, cid, "properties"), {
            "PropertyTable": {"Properties": [{"CID": cid, "Title": f"Synthetic {name.title()}"}]}
        })
        write_json(compound_path(tmp_path, cid, "metadata"), {
            "cid": cid, "source": "PubChem", "retrieved_at": "2026-01-01T00:00:00Z",
            "toxicity_status": "missing" if name == "gamma" else "found",
        })
        if name == "gamma":
            payload = {"missing_section": "Toxicity"}
        else:
            payload = json.loads((FIXTURES / f"{name}.json").read_text(encoding = "utf-8"))
            payload["Record"].update(RecordNumber = cid, RecordType = "CID")
        write_json(compound_path(tmp_path, cid, "toxicity"), payload)
    return tmp_path
