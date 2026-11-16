"""Reviewed natural occurrence and herbicidal activity are independent labels."""
LABEL_FIELDS = {"compound_id", "natural_origin", "origin_reference", "herbicidal_activity",
                "activity_reference", "activity_context", "activity_policy"}


def attach_labels(compounds, labels):
    """Attach only explicitly reviewed targets, rejecting ambiguous inputs."""
    ids = [row.get("compound_id") for row in compounds]
    if any(not isinstance(value, str) or not value.strip() for value in ids):
        raise ValueError("Every compound_id must be a nonempty string")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate compound_id")
    by_id = {}
    policies = set()
    for label in labels:
        extra = set(label) - LABEL_FIELDS
        if extra:
            raise ValueError(f"Unknown label fields: {sorted(extra)}")
        identity = label.get("compound_id")
        if identity not in ids:
            raise ValueError(f"Unknown compound_id: {identity}")
        if identity in by_id:
            raise ValueError(f"Duplicate label: {identity}")
        normalized = {}
        for field in LABEL_FIELDS - {"compound_id"}:
            value = label.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{field} must be text")
            normalized[field] = (value or "").strip()
        for field, allowed in [("natural_origin", {"natural", "synthetic", "unknown", ""}),
                               ("herbicidal_activity", {"active", "inactive", "unknown", ""})]:
            if normalized[field] not in allowed:
                raise ValueError(f"Invalid {field}: {normalized[field]}")
        if (normalized["natural_origin"] in {"natural", "synthetic"}
                and not normalized["origin_reference"]):
            raise ValueError("Known origin requires origin_reference")
        if normalized["herbicidal_activity"] in {"active", "inactive"}:
            for field in ("activity_reference", "activity_context", "activity_policy"):
                if not normalized[field]:
                    raise ValueError(f"Known activity requires {field}")
            policies.add(normalized["activity_policy"])
        normalized["activity_target"] = {"active": 1, "inactive": 0}.get(
            normalized["herbicidal_activity"])
        normalized["origin_target"] = {"natural": 1, "synthetic": 0}.get(
            normalized["natural_origin"])
        by_id[identity] = normalized
    if len(policies) > 1:
        raise ValueError("Use one activity_policy per training dataset")
    attached = []
    seen = {}
    for compound in compounds:
        label = by_id.get(compound["compound_id"], {})
        row = {**compound, **dict.fromkeys(LABEL_FIELDS - {"compound_id"}),
               "activity_target": None, "origin_target": None, **label}
        structure = row.get("canonical_structure")
        for target in ("activity_target", "origin_target"):
            if structure and row[target] is not None:
                key = (structure, target)
                if key in seen and seen[key] != row[target]:
                    raise ValueError(f"Conflicting {target} for structure {structure}")
                seen[key] = row[target]
        attached.append(row)
    return attached


def selection_target(row):
    return {"herbicide": 1, "natural_product": 0}.get(row.get("chemical_group"))
