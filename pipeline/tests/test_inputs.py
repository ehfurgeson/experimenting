"""Query classification and stable identity without chemical synonym inference."""

import json
import os
import re
import subprocess
import sys

import pytest

from agrotox.inputs import classify_query, load_queries, merge_queries, query_key


@pytest.mark.parametrize(
    "query, expected",
    [
        (" 9750 ", ("cid", "9750")),
        ("009750", ("cid", "9750")),
        ("1", ("cid", "1")),
        ("\t Solanine \n", ("name", "Solanine")),
        ("1,8-cineole", ("name", "1,8-cineole")),
        ("１２３", ("name", "１２３")),
        ("١٢٣", ("name", "١٢٣")),
        ("²", ("name", "²")),
        ("-5", ("name", "-5")),
        ("+5", ("name", "+5")),
        ("1.5", ("name", "1.5")),
    ],
)
def test_classification(query, expected):
    assert classify_query(query) == expected


@pytest.mark.parametrize("query", ["", " ", "\t\n", "0", "000", " 000 "])
def test_invalid_queries(query):
    with pytest.raises(ValueError):
        classify_query(query)
    with pytest.raises(ValueError):
        query_key(query)


@pytest.mark.parametrize(
    "first, equivalent",
    [(" Alpha ", "alpha"), ("Straße", "STRASSE"), ("009750", "9750")],
)
def test_equivalent_queries_share_keys(first, equivalent):
    assert query_key(first) == query_key(equivalent)


@pytest.mark.parametrize(
    "first, distinct",
    [("alpha", "beta"), ("1,8-cineole", "eucalyptol"), ("12", "１２"), ("a b", "a  b")],
)
def test_distinct_queries_keep_distinct_keys(first, distinct):
    assert query_key(first) != query_key(distinct)


def test_classification_preserves_display_spelling_separately_from_key():
    query = "  ALpha  "
    assert classify_query(query) == ("name", "ALpha")
    assert query_key(query) == query_key("alpha")
    assert query == "  ALpha  "


@pytest.mark.parametrize("query", ["../../alpha/beta", "α/β", "9750"])
def test_keys_are_safe_filename_components(query):
    assert re.fullmatch(r"[A-Za-z0-9_-]+", query_key(query))


def test_keys_are_stable_across_processes(tmp_path):
    queries = [" Alpha ", "Straße", "009750", "1,8-cineole"]
    script = (
        "import json; from agrotox.inputs import query_key; "
        f"print(json.dumps([query_key(q) for q in {queries!r}]))"
    )
    expected = [query_key(query) for query in queries]
    for seed in ["1", "98765"]:
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd = tmp_path,
            env = {**os.environ, "PYTHONHASHSEED": seed},
            capture_output = True,
            text = True,
            check = True,
        )
        assert json.loads(result.stdout) == expected


@pytest.mark.parametrize(
    "suffix, content, expected",
    [
        (".csv", "\ufeffquery,chemical_group\n Alpha , herbicide \nalpha,herbicide\n",
         [{"query": "Alpha", "chemical_group": "herbicide"}]),
        (".csv", "source_note,query\n curated ,009750\n curated ,9750\n",
         [{"query": "009750", "source_note": "curated"}]),
        (".CSV", '# comment\n\nalpha,ignored\n"1,8-cineole",ignored\n',
         [{"query": "alpha"}, {"query": "1,8-cineole"}]),
        (".txt", "\ufeff# comment\n Alpha \n\nalpha\n009750\n9750\n1,8-cineole\n",
         [{"query": "Alpha"}, {"query": "009750"}, {"query": "1,8-cineole"}]),
        (".csv", 'query,source_note\nalpha,"line one\nline two, quoted"\n',
         [{"query": "alpha", "source_note": "line one\nline two, quoted"}]),
        (".csv", "# before header\n query , chemical_group \n\n# comment\nalpha,h\n",
         [{"query": "alpha", "chemical_group": "h"}]),
    ],
)
def test_load_queries(tmp_path, suffix, content, expected):
    path = tmp_path / f"queries{suffix}"
    path.write_text(content, encoding = "utf-8")
    assert load_queries(path) == expected


@pytest.mark.parametrize("suffix", [".csv", ".txt"])
@pytest.mark.parametrize("content", ["", "\ufeff", "\n  \n# comment\n"])
def test_empty_inputs(tmp_path, suffix, content):
    path = tmp_path / f"queries{suffix}"
    path.write_text(content, encoding = "utf-8")
    assert load_queries(path) == []


def test_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_queries(tmp_path / "missing.csv")


@pytest.mark.parametrize(
    "content",
    [
        "query,query\nalpha,beta\n",
        "query, query \nalpha,beta\n",
        "chemical_group,source_note\nh,curated\n",
        "query,unexpected\nalpha,value\n",
        "query,chemical_group\nalpha,h,extra\n",
        "query,chemical_group\nalpha\n",
        "query,chemical_group\n,h\n",
        'query,source_note\nalpha,"unterminated\n',
        "query\n000\n",
        "query,chemical_group\nAlpha,h\nalpha,n\n",
        "query,chemical_group\n009750,h\n9750,n\n",
    ],
)
def test_invalid_csv(tmp_path, content):
    path = tmp_path / "queries.csv"
    path.write_text(content, encoding = "utf-8")
    with pytest.raises(ValueError):
        load_queries(path)


def test_load_enriches_metadata(tmp_path):
    path = tmp_path / "queries.csv"
    path.write_text("query,chemical_group\n Alpha ,\nalpha,h\nALPHA,\n", encoding = "utf-8")
    assert load_queries(path) == [{"query": "Alpha", "chemical_group": "h"}]


@pytest.mark.parametrize("field", ["chemical_group", "subgroup", "hrac_group", "source_note"])
def test_merge_enriches_without_mutating_inputs(field):
    first = {"query": " Alpha ", field: " "}
    second = {"query": "alpha", field: " curated "}
    assert merge_queries([first, second, {"query": "ALPHA", field: ""}]) == [
        {"query": "Alpha", field: "curated"}
    ]
    assert first == {"query": " Alpha ", field: " "}
    assert second == {"query": "alpha", field: " curated "}


@pytest.mark.parametrize("field", ["chemical_group", "subgroup", "hrac_group", "source_note"])
def test_merge_conflicts_identify_query_and_field(field):
    with pytest.raises(ValueError, match = f"Alpha.*{field}"):
        merge_queries([{"query": "Alpha", field: "one"}, {"query": "alpha", field: "two"}])


def test_merge_combines_file_and_positional_queries(tmp_path):
    path = tmp_path / "queries.txt"
    path.write_text("009750\nbeta\n", encoding = "utf-8")
    assert merge_queries([
        {"query": "9750", "chemical_group": "h"},
        *load_queries(path),
        {"query": "Alpha"},
    ]) == [
        {"query": "9750", "chemical_group": "h"},
        {"query": "beta"},
        {"query": "Alpha"},
    ]


@pytest.mark.parametrize("row", [{}, {"query": " "}, {"query": "0"}])
def test_merge_requires_valid_query(row):
    with pytest.raises(ValueError):
        merge_queries([row])


@pytest.mark.parametrize(
    "row",
    [{"query": "alpha", "unexpected": "x"}, {"query": 101},
     {"query": "alpha", "source_note": None}],
)
def test_merge_rejects_unsupported_fields_and_nonstring_values(row):
    with pytest.raises(ValueError):
        merge_queries([row])


def test_empty_merge():
    assert merge_queries([]) == []


def test_header_only_input(tmp_path):
    path = tmp_path / "queries.csv"
    path.write_text("query,chemical_group\n", encoding = "utf-8")
    assert load_queries(path) == []


def test_unsupported_input_format(tmp_path):
    path = tmp_path / "queries.json"
    path.write_text("[]", encoding = "utf-8")
    with pytest.raises(ValueError, match = r"\.csv or \.txt"):
        load_queries(path)


def test_invalid_txt_query_reports_path(tmp_path):
    path = tmp_path / "queries.txt"
    path.write_text("alpha\n000\n", encoding = "utf-8")
    with pytest.raises(ValueError, match = "queries.txt.*positive"):
        load_queries(path)
