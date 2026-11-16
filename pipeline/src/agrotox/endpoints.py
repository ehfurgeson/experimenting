"""Shared standard units for supported normalized comparison endpoints."""

from types import MappingProxyType

ENDPOINT_UNITS = MappingProxyType({
    "LD50": "mg/kg",
    "LC50": "mg/L",
    "EC50": "mg/L",
})

# Point of departure units retain the reported dose time basis.
POINT_OF_DEPARTURE_UNITS = MappingProxyType({
    endpoint: ("mg/kg", "mg/kg-day")
    for endpoint in ("NOAEL", "LOAEL", "BMD", "BMDL")
})
