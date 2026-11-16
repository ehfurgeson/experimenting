"""Conservative unit factors and explicit exposure-duration conversion."""

import pytest

from agrotox.units import duration_hours, normalize_unit


@pytest.mark.parametrize("unit, expected_factor", [
    ("g/kg", 1000.0), ("mg/kg", 1.0), ("ug/kg", 0.001),
    ("µg / kg", 0.001), ("μg/kg", 0.001), (" MG / KG ", 1.0),
    ("mg kg-1", 1.0), ("g kg-1", 1000.0),
    ("mg/kg bw", 1.0), ("mg / kg body weight", 1.0),
])
def test_dose_units(unit, expected_factor):
    assert normalize_unit(unit, "LD50") == ("mg/kg", expected_factor)


@pytest.mark.parametrize("endpoint", ["LC50", "EC50", " lc 50 "])
@pytest.mark.parametrize("unit, expected_factor", [
    ("g/L", 1000.0), ("mg/L", 1.0), ("ug/L", 0.001),
    ("µg / L", 0.001), (" μg\t/ L ", 0.001), ("mg L-1", 1.0),
])
def test_concentration_units(unit, expected_factor, endpoint):
    assert normalize_unit(unit, endpoint) == ("mg/L", expected_factor)


@pytest.mark.parametrize("unit, endpoint", [
    ("mg/L", "LD50"), ("mg/kg", "LC50"), ("g/kg", "EC50"),
    ("mol/L", "LC50"), ("mg/m3", "LC50"), ("percent", "EC50"),
    ("mg/L", "IC50"), ("mg/L", None), (None, "LD50"), ("", "LD50"),
    ("mg/kg bodyweightless", "LD50"),
    ("mg/L bw", "LC50"),
])
def test_incompatible_or_unsupported_units_remain_unknown(unit, endpoint):
    assert normalize_unit(unit, endpoint) == (None, None)


@pytest.mark.parametrize("medium", ["water", "aqueous", " Water ", "AQUEOUS"])
@pytest.mark.parametrize("endpoint", ["LC50", "EC50"])
def test_ppm_requires_explicit_aqueous_medium(medium, endpoint):
    assert normalize_unit(" ppm ", endpoint, medium) == ("mg/L", 1.0)


@pytest.mark.parametrize("medium", [None, "", "air", "unknown", "fish", "seawater"])
def test_ppm_is_not_imputed_from_endpoint_or_organism(medium):
    assert normalize_unit("ppm", "LC50", medium) == (None, None)


def test_ppm_cannot_become_a_dose():
    assert normalize_unit("ppm", "LD50", "water") == (None, None)


@pytest.mark.parametrize("value, unit, expected", [
    (96, "h", 96.0), (4, "days", 96.0), (0.5, "day", 12.0),
    (2, "d", 48.0), (1.5, " HOURS ", 1.5),
    (1, "hr", 1.0), (1, "hrs", 1.0), (1, "hour", 1.0),
    (0, "h", 0.0), (0, "days", 0.0),
    (2, "wk", 336.0), (0.5, "week", 84.0), (1, " WEEKS ", 168.0),
    (0, "wks", 0.0),
])
def test_duration_conversions(value, unit, expected):
    result = duration_hours(value, unit)
    assert result == expected
    assert isinstance(result, float)


@pytest.mark.parametrize("value, unit", [
    (None, "h"), (None, None), (1, None), (1, ""), (1, "months"), (60, "seconds"),
    (2, "wph"), (2, "hph"), (2, "dph"),
])
def test_missing_or_unsupported_duration_remains_unknown(value, unit):
    assert duration_hours(value, unit) is None


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("unit", ["h", "days", "unknown"])
def test_invalid_duration_numbers_raise_even_for_unsupported_units(value, unit):
    with pytest.raises(ValueError):
        duration_hours(value, unit)


@pytest.mark.parametrize("unit", ["days", "weeks"])
def test_duration_conversion_overflow_raises(unit):
    with pytest.raises(ValueError):
        duration_hours(1e308, unit)


@pytest.mark.parametrize("value", [True, False, "96"])
def test_duration_requires_a_numeric_value(value):
    with pytest.raises(TypeError):
        duration_hours(value, "h")


@pytest.mark.parametrize("endpoint", ["NOAEL", "LOAEL", "BMD", "BMDL"])
@pytest.mark.parametrize("unit, standard, factor", [
    ("g/kg", "mg/kg", 1000.0),
    ("mg/kg bw", "mg/kg", 1.0),
    ("ug/kg", "mg/kg", 0.001),
    ("g/kg-day", "mg/kg-day", 1000.0),
    ("mg/kg/day", "mg/kg-day", 1.0),
    ("µg / kg / d", "mg/kg-day", 0.001),
    ("mg/kg bw/day", "mg/kg-day", 1.0),
    ("mg / kg body weight / day", "mg/kg-day", 1.0),
    ("mg kg-1 day-1", "mg/kg-day", 1.0),
])
def test_point_of_departure_units_preserve_daily_dose(endpoint, unit, standard, factor):
    assert normalize_unit(unit, endpoint) == (standard, factor)


@pytest.mark.parametrize("endpoint", ["NOAEL", "LOAEL", "BMD", "BMDL"])
@pytest.mark.parametrize("unit", ["ppm", "mg/m3", "mg/L", "mg/kg/week", "mg/day"])
def test_point_of_departure_units_do_not_infer_doses(endpoint, unit):
    assert normalize_unit(unit, endpoint, "water") == (None, None)


@pytest.mark.parametrize("endpoint", ["LD50", "LC50", "EC50"])
def test_daily_dose_does_not_change_acute_unit_policy(endpoint):
    assert normalize_unit("mg/kg-day", endpoint) == (None, None)
