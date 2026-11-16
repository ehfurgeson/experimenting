"""Conservative result parsing preserves uncertainty and rejects numeric substrings."""

import pytest

from agrotox.normalize import parse_value


@pytest.mark.parametrize("text, value, unit", [
    ("560 mg/kg", 560.0, "mg/kg"),
    ("LD50: rat oral 1 g/kg", 1.0, "g/kg"),
    ("LD50=5 mg/kg", 5.0, "mg/kg"),
    ("= 5 mg/L", 5.0, "mg/L"),
    ("1,000 mg/kg", 1000.0, "mg/kg"),
    ("1,234,567.5 mg/L", 1234567.5, "mg/L"),
    ("1e3 mg/kg", 1000.0, "mg/kg"),
    ("1.5E-3 mg/L", 0.0015, "mg/L"),
    ("5e+2 µg/L", 500.0, "µg/L"),
    (".5 mg/L", 0.5, "mg/L"),
    ("5 μg / L", 5.0, "μg / L"),
    ("5 µg/kg", 5.0, "µg/kg"),
    ("5 mg kg-1 bw", 5.0, "mg kg-1 bw"),
    ("5 mg/kg body weight", 5.0, "mg/kg body weight"),
    ("LC50 5 ppm for 96 h", 5.0, "ppm"),
    ("5 mg/L (4 days)", 5.0, "mg/L"),
    ("5 mg/L (2 weeks)", 5.0, "mg/L"),
    ("5 mg/L for 2 wk", 5.0, "mg/L"),
    ("(5 mg/L).", 5.0, "mg/L"),
])
def test_exact_values(text, value, unit):
    assert parse_value(text) == {
        "value_numeric": value, "value_lower": None, "value_upper": None,
        "qualifier": "=", "unit_raw": unit,
    }
    assert isinstance(parse_value(text)["value_numeric"], float)


@pytest.mark.parametrize("symbol, qualifier", [
    (">", ">"), ("<", "<"), (">=", ">="), ("<=", "<="), ("≥", ">="), ("≤", "<="),
])
def test_inequalities_keep_thresholds_and_qualifiers(symbol, qualifier):
    assert parse_value(f"{symbol} 1e3 mg/kg") == {
        "value_numeric": 1000.0, "value_lower": None, "value_upper": None,
        "qualifier": qualifier, "unit_raw": "mg/kg",
    }


@pytest.mark.parametrize("text, lower, upper", [
    ("3-5 mg/L", 3.0, 5.0), ("3–5 mg/L", 3.0, 5.0), ("3 — 5 mg/L", 3.0, 5.0),
    ("3 to 5 mg/L", 3.0, 5.0), ("1,000-2,000 mg/kg", 1000.0, 2000.0),
    ("1e-3-2e-3 mg/L", 0.001, 0.002), (".1 – .5 mg/L", 0.1, 0.5),
    ("1E+1 – 2E+1 mg/kg", 10.0, 20.0),
])
def test_ranges_have_bounds_and_no_scalar(text, lower, upper):
    result = parse_value(text)
    assert result["qualifier"] == "range"
    assert result["value_numeric"] is None
    assert result["value_lower"] == lower
    assert result["value_upper"] == upper
    assert isinstance(result["value_lower"], float)
    assert isinstance(result["value_upper"], float)


@pytest.mark.parametrize("text", [
    "", "no result", None,
    "-5 mg/L", "−5 mg/L", "- 5 mg/L", "− 5 mg/L", "(-5 mg/L)",
    "x-5 mg/L", "abc5 mg/L", "+5 mg/L", "+ 5 mg/L",
    "0 mg/kg", "0.0 mg/L", "0e3 mg/L", "0-5 mg/L", "-3–5 mg/L", "3--5 mg/L",
    "5-3 mg/L", "3-3 mg/L", ">3-5 mg/L", "≤ 3–5 mg/L",
    "NaN mg/L", "Infinity mg/L", "inf mg/L", "∞ mg/L", "1e309 mg/L",
    "1e-999 mg/L", "1-1e309 mg/L",
    "1 mg/L; 2 mg/L", "1 g/kg or 2 mg/kg", "1 or 2 mg/L", "1, 2 mg/L",
    "1 mg/L (95% CI 0.5–2)", "1 mg/L; NaN mg/L",
    "1,00 mg/L", "1,2345 mg/L", "1234,567 mg/L", "1.2.3 mg/L", "5. mg/L",
    "1e mg/L", "1e 3 mg/L", "1e--3 mg/L", "1e- 3 mg/L", "1e3.0 mg/L",
    "١5 mg/L", "1 000 mg/L",
    "approximately 3 mg/L", "about 3 mg/L", "approx. 3 mg/L", "~3 mg/L", "≈3 mg/L",
    "roughly 3 mg/L", "estimated 3 mg/L", "between about 3 and 5 mg/L",
    "less than 5 mg/L", "at least 5 mg/L", "up to 5 mg/L", "<<5 mg/L", "< < 5 mg/L",
    "5 mg/L/day", "5 mg/L^2", "5 mg/L2", "5 mol/L", "5 mg/m3", "5%", "5",
    "-(5 mg/L)", "− ( (5 mg/L))", "minus 5 mg/L", "negative 5 mg/L", "x/5 mg/L",
    "≃5 mg/L", "∼5 mg/L", "±5 mg/L", "5 mg/L +/- 1", "below 5 mg/L", "above 5 mg/L",
    "over 5 mg/L", "5 mg/L per day", "5 mg/L body weight",
])
def test_ambiguous_or_invalid_results_return_none(text):
    assert parse_value(text) is None


def test_successful_parsing_does_not_convert_units():
    result = parse_value("> 2 g/kg")
    assert result["value_numeric"] == 2.0
    assert result["qualifier"] == ">"
    assert result["unit_raw"] == "g/kg"


@pytest.mark.parametrize("text", [5, True])
def test_nontext_values_are_not_interpreted(text):
    with pytest.raises(TypeError):
        parse_value(text)
