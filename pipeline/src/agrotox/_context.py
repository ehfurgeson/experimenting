"""Explicit annotation context vocabulary and ambiguity checks."""

import re
from typing import Any

from .endpoints import ENDPOINT_UNITS
from .units import duration_hours

SPECIES = {
    "rat": ("mammal", r"rats?|Rattus norvegicus|Rattus rattus"),
    "mouse": ("mammal", r"mouse|mice|Mus musculus"),
    "rabbit": ("mammal", r"rabbits?|Oryctolagus cuniculus"),
    "fish": ("fish", r"fish|fishes"),
    "trout": ("fish", r"trout"),
    "bluegill": ("fish", r"bluegill"),
    "carp": ("fish", r"carp"),
    "rainbow_trout": ("fish", r"rainbow trout|Oncorhynchus mykiss|Salmo gairdneri"),
    "fathead_minnow": ("fish", r"fathead minnow|Pimephales promelas"),
    "daphnia": ("aquatic_invertebrate", r"daphnia"),
    "daphnia_magna": ("aquatic_invertebrate", r"Daphnia magna"),
    "algae": ("algae", r"alga|algae"),
    "bee": ("bee", r"bees?"),
    "mallard": ("bird", r"mallards?"),
}
ROUTES = {
    "oral": "oral", "dermal": "dermal|percutaneous", "inhalation": "inhalation",
    "contact": "contact", "intraperitoneal": "intraperitoneal|ip",
    "intravenous": "intravenous|iv", "subcutaneous": "subcutaneous|sc",
}
ENDPOINTS = re.compile(
    r"\b(?:(?:LD|LC|EC|IC|ED|TD|TC)\s*[0-9]+|NOEC|LOEC|NOEL|LOEL)\b", re.IGNORECASE,
)
TIME_UNIT = r"(?:hours?|hrs?|h|days?|d|seconds?|secs?|s|minutes?|mins?|weeks?|wks?|months?|years?)"
DURATION = re.compile(
    rf"(?<![\w.,+\-−–—])(?P<value>[+\-−]?\s*(?:[0-9][0-9.,eE+\-−–—]*|"
    rf"\.[0-9][0-9eE+\-−]*|nan|inf(?:inity)?|∞))\s*(?P<unit>{TIME_UNIT})\b",
    re.IGNORECASE,
)
DECIMAL_DURATION = r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:e[+-]?[0-9]+)?"
DURATION_RANGE = re.compile(
    rf"{DECIMAL_DURATION}\s*[-–—]\s*{DECIMAL_DURATION}\s*{TIME_UNIT}\b", re.IGNORECASE,
)


def _is_nonexposure_duration(text: str, start: int, end: int) -> bool:
    prefix = text[:start]
    if re.search(r"\b(?:age|aged)(?:\s+of)?\s*:?\s*[\(\[]?\s*$", prefix, re.IGNORECASE):
        return True
    if re.match(r"\s*(?:old|of\s+age)\b", text[end:], re.IGNORECASE):
        return True
    clause = re.split(r"[.;]", prefix)[-1]
    return re.search(
        r"\b(?:follow[-\s]?up|survival|observation|monitoring|monitored|recorded)\b",
        clause, re.IGNORECASE,
    ) is not None


def _duration_context(text: str) -> tuple[float | None, str | None, float | None, list[str]]:
    if any(
        not _is_nonexposure_duration(text, match.start(), match.end())
        for match in DURATION_RANGE.finditer(text)
    ):
        return None, None, None, ["unsupported exposure-duration range"]
    durations = []
    notes = []
    for match in DURATION.finditer(text):
        if _is_nonexposure_duration(text, match.start(), match.end()):
            continue
        try:
            value = float(re.sub(r"\s+", "", match["value"]).replace("−", "-"))
            hours = duration_hours(value, match["unit"])
            if hours is None or hours <= 0:
                raise ValueError("unsupported or nonpositive duration")
            durations.append((value, match["unit"], hours))
        except ValueError:
            notes.append("invalid or unsupported exposure duration")
    if notes:
        return None, None, None, notes
    if len({item[2] for item in durations}) > 1:
        return None, None, None, ["multiple exposure durations"]
    return (*durations[0], []) if durations else (None, None, None, [])


def extract_context(text: str, duration_text: str) -> dict[str, Any]:
    """Read explicit context only; retain ambiguity instead of choosing a candidate."""
    notes = []
    endpoints = {re.sub(r"\s+", "", match.group().upper()) for match in ENDPOINTS.finditer(text)}
    supported = endpoints & ENDPOINT_UNITS.keys()
    endpoint = next(iter(supported)) if len(endpoints) == len(supported) == 1 else None
    if endpoint is None:
        notes.append("multiple endpoints" if supported else "no supported endpoint")
    species = {
        name for name, (_, pattern) in SPECIES.items()
        if re.search(r"\b(?:" + pattern.replace(" ", r"\s+") + r")\b", text, re.IGNORECASE)
    }
    if "rainbow_trout" in species:
        species.discard("trout")
    if species & {"trout", "bluegill", "carp", "rainbow_trout", "fathead_minnow"}:
        species.discard("fish")
    if "daphnia_magna" in species:
        species.discard("daphnia")
    groups = {SPECIES[name][0] for name in species}
    routes = {
        name for name, pattern in ROUTES.items()
        if re.search(rf"\b(?:{pattern})\b", text, re.IGNORECASE)
    }
    if len(species) > 1:
        notes.append("multiple species")
    if len(routes) > 1:
        notes.append("multiple exposure routes")
    media = {name for name, pattern in {
        "water": "water|aqueous", "air": "air", "seawater": "seawater", "freshwater": "freshwater",
    }.items() if re.search(rf"\b(?:{pattern})\b", text, re.IGNORECASE)}
    if len(media) > 1:
        notes.append("multiple exposure media")
    value, unit, hours, duration_notes = _duration_context(duration_text)
    return {
        "endpoint": endpoint, "has_supported_endpoint": bool(supported),
        "species": next(iter(species)) if len(species) == 1 else None,
        "organism_group": next(iter(groups)) if len(groups) == 1 else None,
        "exposure_route": next(iter(routes)) if len(routes) == 1 else None,
        "medium": next(iter(media)) if len(media) == 1 else None,
        "duration_value": value, "duration_unit": unit, "duration_hours": hours,
        "notes": [*notes, *duration_notes],
    }
