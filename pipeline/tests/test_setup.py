"""Check the installed package and offline test foundation."""

from importlib.metadata import version
from pathlib import Path

import pytest
import requests


def test_installed_package():
    import agrotox

    assert agrotox.__version__ == version("agrotox")
    assert Path(agrotox.__file__).resolve().parent == (
        Path(__file__).resolve().parents[1] / "src" / "agrotox"
    )


@pytest.mark.parametrize("synthetic_record", ["alpha", "beta"], indirect = True)
def test_fixture_json_loads(synthetic_record):
    assert synthetic_record["Record"]["RecordTitle"].startswith("Synthetic ")
    assert synthetic_record["Record"]["Section"]


@pytest.mark.parametrize("use_session", [False, True])
def test_requests_are_blocked(use_session):
    with pytest.raises(AssertionError, match = "Pipeline tests must not use the network"):
        if use_session:
            with requests.Session() as session:
                session.get("https://example.org/offline-test", timeout = 1)
        else:
            requests.get("https://example.org/offline-test", timeout = 1)
