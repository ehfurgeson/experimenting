"""Validated endpoint policies and conservative measurement matching."""

from collections.abc import Mapping
from copy import deepcopy
from math import isfinite
from pathlib import Path
from sys import float_info

import polars as pl
import yaml

from agrotox.endpoints import ENDPOINT_UNITS, POINT_OF_DEPARTURE_UNITS
from agrotox.tables import MEASUREMENT_SCHEMA, STUDY_CONTEXT_SCHEMA

Definitions = dict[str, dict[str, str | float | int]]
_CONTEXT = {
    "organism_group": "organism_group",
    "species": "species",
    "preferred_route": "exposure_route",
    "preferred_duration_hours": "duration_hours",
    "standard_unit": "unit_standardized",
    **{field: field for field in STUDY_CONTEXT_SCHEMA},
}
_DISPLAY = {"endpoint_family", "label", "context_note"}
_NUMERIC = (
    "value_standardized", "value_lower_standardized", "value_upper_standardized",
    "duration_hours",
)
_COLUMNS = (
    "endpoint", "organism_group", "species", "exposure_route", "duration_hours",
    "unit_standardized", "parse_status", "formulation_flag", "qualifier",
    *_NUMERIC[:3],
)


class _UniqueLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects silently overwritten mapping keys."""


def _unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep = True)
        try:
            if key in result:
                raise ValueError(f"Duplicate YAML key: {key!r}")
            result[key] = loader.construct_object(value_node, deep = True)
        except TypeError as error:
            raise ValueError("YAML mapping keys must be scalar values") from error
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def validate_definitions(definitions: object) -> Definitions:
    """Return an independent validated copy; reject unknown or malformed fields."""
    if not isinstance(definitions, Mapping) or not definitions:
        raise ValueError("Definitions must be a nonempty mapping")
    for name, definition in definitions.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Definition names must be nonempty strings")
        if not isinstance(definition, Mapping):
            # Configuration errors use one exception type, including YAML types.
            raise ValueError(f"Definition {name!r} must be a mapping")  # noqa: TRY004
        unknown = set(definition) - {"endpoint", "summary_mode", *_CONTEXT, *_DISPLAY}
        if unknown:
            raise ValueError(f"Unknown fields in {name!r}: {unknown!r}")
        endpoint = definition.get("endpoint")
        if not isinstance(endpoint, str) or endpoint not in {*ENDPOINT_UNITS, *POINT_OF_DEPARTURE_UNITS}:
            raise ValueError(f"Definition {name!r} requires a supported endpoint")
        for field, value in definition.items():
            if field == "preferred_duration_hours":
                if (type(value) not in (int, float) or value <= 0
                        or value > float_info.max or not isfinite(value)):
                    raise ValueError(f"{name}.{field} must be positive finite hours")
            elif not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name}.{field} must be a nonempty string")
        units = POINT_OF_DEPARTURE_UNITS.get(endpoint, (ENDPOINT_UNITS.get(endpoint),))
        if "standard_unit" in definition and definition["standard_unit"] not in units:
            raise ValueError(f"{name}.standard_unit must be one of {units}")
        mode = definition.get("summary_mode", "availability" if endpoint in POINT_OF_DEPARTURE_UNITS
                              else "potency")
        if mode not in {"availability", "potency"}:
            raise ValueError(f"{name}.summary_mode must be availability or potency")
        if endpoint in POINT_OF_DEPARTURE_UNITS:
            if "standard_unit" not in definition:
                raise ValueError(f"{name}.standard_unit is required for a point of departure")
            basis = "model_derived" if endpoint in {"BMD", "BMDL"} else "observed"
            if "evidence_basis" in definition and definition["evidence_basis"] != basis:
                raise ValueError(f"{name}.evidence_basis must be {basis}")
            if mode == "potency":
                required = {"species", "preferred_route", "preferred_duration_hours",
                            "study_type", "effect"}
                if endpoint in {"BMD", "BMDL"}:
                    required.update({"benchmark_response", "benchmark_response_type", "model_name"})
                if endpoint == "BMDL":
                    required.add("confidence_level")
                missing = required - set(definition)
                if missing:
                    raise ValueError(f"{name} potency summary requires {', '.join(sorted(missing))}")
    return deepcopy({name: dict(rule) for name, rule in definitions.items()})


def load_definitions(path: Path) -> Definitions:
    """Read safe UTF-8 YAML, rejecting duplicate keys and invalid policies.

    File I/O errors propagate; YAML syntax and policy errors raise ValueError.
    """
    try:
        definitions = yaml.load(Path(path).read_text(encoding = "utf-8-sig"),
                                Loader = _UniqueLoader)
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid definitions YAML in {path}: {error}") from error
    return validate_definitions(definitions)


def matching_expr(definition: Mapping) -> pl.Expr:
    """Match complete converted results and every configured context equality.

    Requires normalized measurement columns. Missing context values fail required
    equalities. Display metadata has no effect; no value is imputed or changed.
    """
    rule = validate_definitions({"policy": definition})["policy"]
    scalar = pl.col("value_standardized")
    lower = pl.col("value_lower_standardized")
    upper = pl.col("value_upper_standardized")
    qualifier = pl.col("qualifier")
    standard_unit = rule.get("standard_unit", ENDPOINT_UNITS.get(rule["endpoint"]))

    def positive_finite(value):
        return value.is_not_null() & value.is_finite() & (value > 0)

    scalar_result = (
        qualifier.is_in(["=", "<", ">", "<=", ">="])
        & positive_finite(scalar) & lower.is_null() & upper.is_null()
    )
    range_result = (
        (qualifier == "range") & scalar.is_null()
        & positive_finite(lower) & positive_finite(upper) & (lower < upper)
    )
    predicate = (
        (pl.col("parse_status") == "complete")
        & ~pl.col("formulation_flag")
        & (pl.col("endpoint") == rule["endpoint"])
        & (pl.col("unit_standardized") == standard_unit)
        & (scalar_result | range_result)
    )
    if rule["endpoint"] in POINT_OF_DEPARTURE_UNITS:
        basis = "model_derived" if rule["endpoint"] in {"BMD", "BMDL"} else "observed"
        predicate = predicate & (pl.col("evidence_basis") == basis)
    for field, column in _CONTEXT.items():
        if field in rule:
            predicate = predicate & (pl.col(column) == rule[field])
    return predicate.fill_null(False).alias("matches")


def matches(record: Mapping, definition: Mapping) -> bool:
    """Evaluate the shared predicate for one row without modifying either input.

    Absent fields become null. Malformed measurement types are ineligible.
    Use matching_expr for table filtering to avoid constructing a frame per row.
    """
    predicate = matching_expr(definition)
    row = {key: record.get(key) for key in (*_COLUMNS, *STUDY_CONTEXT_SCHEMA)}
    for key, value in row.items():
        if value is None:
            continue
        if key in _NUMERIC:
            if type(value) not in (int, float):
                return False
        elif key == "formulation_flag":
            if type(value) is not bool:
                return False
        elif not isinstance(value, str):
            return False
    try:
        frame = pl.DataFrame([row], schema = {key: MEASUREMENT_SCHEMA[key] for key in row})
    except (TypeError, ValueError, OverflowError):
        return False
    return frame.select(predicate).item()


def coverage_tables(
    compounds: pl.DataFrame, measurements: pl.DataFrame, definitions: Mapping,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return binary compound availability and counts per selected chemical group.

    Denominators include unresolved and zero-data compounds. Identical duplicate
    compound rows collapse; conflicting identities and orphan measurements raise.
    Rows retain compound selection order; summaries sort by group (null last) and
    definition insertion order. Inputs are never modified.
    """
    rules = validate_definitions(definitions)
    context_columns = {
        column for rule in rules.values() for field, column in _CONTEXT.items() if field in rule
    }
    if any(rule["endpoint"] in POINT_OF_DEPARTURE_UNITS for rule in rules.values()):
        context_columns.add("evidence_basis")
    identity_schema = {
        "compound_id": pl.String, "input_queries": pl.List(pl.String),
        "chemical_group": pl.String,
    }
    summary_schema = {
        "chemical_group": pl.String, "endpoint": pl.String,
        "compounds_with_data": pl.Int64, "total_compounds": pl.Int64,
    }
    if set(rules) & set(identity_schema):
        raise ValueError("Definition names collide with coverage identity columns")
    for label, frame, schema in [
        ("compounds", compounds, identity_schema),
        ("measurements", measurements, {
            field: MEASUREMENT_SCHEMA[field]
            for field in ("compound_id", *_COLUMNS, *sorted(context_columns))
        }),
    ]:
        if any(frame.schema.get(field) != dtype for field, dtype in schema.items()):
            raise ValueError(f"Invalid {label} schema")
        if frame["compound_id"].null_count():
            raise ValueError(f"{label} identities must be nonnull")
    universe = compounds.unique(maintain_order = True)
    if universe["compound_id"].is_duplicated().any():
        raise ValueError("Compound rows contain conflicting duplicate identities")
    if measurements.select("compound_id").unique().join(
        universe.select("compound_id"), on = "compound_id", how = "anti",
    ).height:
        raise ValueError("Measurements reference compounds outside the selected universe")
    matrix = universe.select(*identity_schema)
    summaries = []
    for position, (name, rule) in enumerate(rules.items()):
        available = measurements.filter(matching_expr(rule)).select("compound_id").unique()
        available = available.with_columns(pl.lit(1, dtype = pl.Int64).alias(name))
        matrix = matrix.join(available, on = "compound_id", how = "left",
                             validate = "1:1", maintain_order = "left").with_columns(
            pl.col(name).fill_null(0),
        )
        summaries.append(matrix.group_by("chemical_group").agg(
            pl.col(name).sum().alias("compounds_with_data"),
            pl.len().cast(pl.Int64).alias("total_compounds"),
        ).with_columns(
            pl.lit(name).alias("endpoint"), pl.lit(position).alias("_definition_order"),
        ))
    summary = pl.concat(summaries).sort(
        "chemical_group", "_definition_order", nulls_last = True,
    ).select(*summary_schema)
    return matrix, summary
