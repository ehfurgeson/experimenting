"""Conservative unit factors and duration conversion without inferred context."""

import math
import re

from .endpoints import ENDPOINT_UNITS, POINT_OF_DEPARTURE_UNITS


def normalize_unit(
    unit: str | None, endpoint: str | None, medium: str | None = None
) -> tuple[str | None, float | None]:
    """Return a standard unit and multiplier, or (None, None) if unsupported.

    LD50 dose converts to mg/kg; LC50/EC50 concentration converts to mg/L.
    Aqueous ppm assumes a dilute solution with density approximately 1 kg/L,
    so 1 ppm is approximated as 1 mg/L. This requires explicit medium context.
    """
    if unit is None or endpoint is None:
        return None, None
    kind = re.sub(r"\s+", "", endpoint.upper())
    if kind in POINT_OF_DEPARTURE_UNITS:
        cleaned = re.sub(
            r"\s+(?:bw|body\s*weight)(?=\s*(?:/|$))", "", unit.casefold(),
        )
        cleaned = re.sub(r"\s+", "", cleaned.replace("µ", "u").replace("μ", "u"))
        match = re.fullmatch(
            r"(mg|ug|g)(?:/kg|kg-1)(?P<daily>/day|/d|-day|day-1)?", cleaned,
        )
        if match:
            standard = "mg/kg-day" if match["daily"] else "mg/kg"
            return standard, {"g": 1000.0, "mg": 1.0, "ug": 0.001}[match[1]]
        return None, None
    standard = ENDPOINT_UNITS.get(kind)
    cleaned = unit.casefold()
    if standard == "mg/kg":
        cleaned = re.sub(r"\s+(?:bw|body\s*weight)\s*$", "", cleaned)
        denominator = "kg"
    elif standard == "mg/L":
        denominator = "l"
    else:
        return None, None
    cleaned = re.sub(r"\s+", "", cleaned.replace("µ", "u").replace("μ", "u"))
    for mass, factor in {"g": 1000.0, "mg": 1.0, "ug": 0.001}.items():
        if cleaned in {f"{mass}/{denominator}", f"{mass}{denominator}-1"}:
            return standard, factor
    if (
        cleaned == "ppm" and standard == "mg/L"
        and medium is not None and medium.strip().casefold() in {"water", "aqueous"}
    ):
        return "mg/L", 1.0
    return None, None


def duration_hours(value: float | None, unit: str | None) -> float | None:
    """Convert explicit hours, days or weeks; unsupported units remain unknown.

    Values must be numeric, nonnegative, and finite. Overflow is rejected.
    Zero is a numeric duration, not a substitute for missing context; endpoint
    matching policies may impose stricter positive-duration requirements.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Duration must be a numeric value or None")
    try:
        numeric = float(value)
    except OverflowError as error:
        raise ValueError("Duration must be finite") from error
    if not math.isfinite(numeric) or numeric < 0:
        raise ValueError("Duration must be nonnegative and finite")
    if unit is None:
        return None
    name = unit.strip().casefold()
    if name in {"h", "hr", "hrs", "hour", "hours"}:
        factor = 1.0
    elif name in {"d", "day", "days"}:
        factor = 24.0
    elif name in {"wk", "wks", "week", "weeks"}:
        factor = 168.0
    else:
        return None
    result = numeric * factor
    if not math.isfinite(result):
        raise ValueError("Converted duration must be finite")
    return result
