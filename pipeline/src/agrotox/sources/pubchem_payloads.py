"""Pure envelope validation shared by PubChem transport and cache readers."""

from typing import Any


def validate_properties(payload: dict[str, Any], cid: int) -> dict[str, Any]:
    """Require exactly one matching property record and return it without mutation."""
    table = payload.get("PropertyTable")
    records = table.get("Properties") if isinstance(table, dict) else None
    if (
        not isinstance(records, list) or len(records) != 1
        or not isinstance(records[0], dict) or type(records[0].get("CID")) is not int
        or records[0]["CID"] != cid
    ):
        raise ValueError(f"Expected exactly one property record matching CID {cid}")
    return records[0]


def validate_toxicity(payload: dict[str, Any], cid: int) -> None:
    """Require a PUG-View CID record with a Section list or null."""
    record = payload.get("Record")
    if (
        "missing_section" in payload or not isinstance(record, dict)
        or type(record.get("RecordNumber")) is not int or record["RecordNumber"] != cid
        or record.get("RecordType") != "CID" or "Section" not in record
        or (record["Section"] is not None and not isinstance(record["Section"], list))
    ):
        raise ValueError(f"Invalid PUG-View Toxicity record for CID {cid}")
