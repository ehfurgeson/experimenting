"""Bounded ChEMBL assay snapshots for explicit activity review."""

import re
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

from .storage import write_json

BASE = "https://www.ebi.ac.uk/chembl/api/data"


def _identity(value):
    if not isinstance(value, str) or not re.fullmatch(r"CHEMBL[1-9][0-9]*", value):
        raise ValueError(f"Expected a positive ChEMBL ID: {value!r}")
    return value


def fetch_assay(root, assay_id, *, http = None, page_size = 1000, max_activities = 10000,
                sleep = None):
    """Publish one complete raw assay; existing snapshots are never refreshed.

    Preserve source values, qualifiers, structures and unknown fields. Requests
    are paced at four per second; failures propagate without publishing a bundle.
    Callers must serialize writes to a data root and choose a new root to refresh.
    """
    _identity(assay_id)
    if type(page_size) is not int or not 1 <= page_size <= 1000:
        raise ValueError("page_size must be a positive integer at most 1000")
    if type(max_activities) is not int or max_activities < 1:
        raise ValueError("max_activities must be a positive integer")
    path = Path(root) / "raw" / "chembl" / f"{assay_id}.json"
    if path.exists():
        raise FileExistsError(f"Use a new root to refresh an existing snapshot: {path}")
    transport = http if http is not None else requests.Session()
    pause = sleep if sleep is not None else time.sleep
    requests_made = []

    def get(endpoint, params = None):
        if requests_made:
            pause(.25)
        url = f"{BASE}/{endpoint}.json"
        response = transport.get(url, params = params, timeout = (10, 40),
                                 allow_redirects = False)
        response.raise_for_status()
        if response.status_code != 200:
            raise requests.HTTPError(f"Unexpected ChEMBL HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Expected a ChEMBL JSON object")  # noqa: TRY004
        requests_made.append({"url": url, "params": params})
        return payload

    status = get("status")
    if not isinstance(status.get("chembl_db_version"), str) or not status["chembl_db_version"]:
        raise ValueError("Missing ChEMBL database version")
    assay = get(f"assay/{assay_id}")
    if assay.get("assay_chembl_id") != assay_id:
        raise ValueError("ChEMBL assay identity mismatch")
    document_id = _identity(assay.get("document_chembl_id"))
    document = get(f"document/{document_id}")
    if document.get("document_chembl_id") != document_id:
        raise ValueError("ChEMBL document identity mismatch")
    pages, seen = [], set()
    offset, total = 0, None
    while True:
        payload = get("activity", {"assay_chembl_id": assay_id,
                                   "limit": str(page_size), "offset": str(offset),
                                   "order_by": "activity_id"})
        meta = payload.get("page_meta")
        if not isinstance(meta, dict):
            raise ValueError("Missing ChEMBL page metadata")  # noqa: TRY004
        count = meta.get("total_count")
        if type(count) is not int or count < 0:
            raise ValueError("Invalid ChEMBL activity count")
        if count > max_activities:
            raise ValueError("ChEMBL assay exceeds max_activities bound")
        if total is not None and total != count:
            raise ValueError("ChEMBL activity count changed during retrieval")
        total = count
        if type(meta.get("offset")) is not int or meta["offset"] != offset:
            raise ValueError("ChEMBL page offset mismatch")
        records = payload.get("activities")
        if (not isinstance(records, list) or len(records) > page_size
                or offset + len(records) > total or not records and offset < total):
            raise ValueError("Incomplete or oversized ChEMBL activity page")
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Expected a ChEMBL activity object")  # noqa: TRY004
            identity = record.get("activity_id")
            if type(identity) is not int or identity <= 0 or identity in seen:
                raise ValueError("Invalid or duplicate ChEMBL activity_id")
            if record.get("assay_chembl_id") != assay_id:
                raise ValueError("Activity belongs to another assay")
            if record.get("document_chembl_id") != document_id:
                raise ValueError("Activity belongs to another document")
            _identity(record.get("molecule_chembl_id"))
            seen.add(identity)
        pages.append(payload)
        offset += len(records)
        if offset == total:
            break
    write_json(path, {
        "source": "ChEMBL", "retrieved_at": datetime.now(UTC).isoformat(),
        "requests": requests_made, "status": status, "assay": assay,
        "document": document, "activity_pages": pages, "activity_count": len(seen),
    })
    return path
