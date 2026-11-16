"""
Prototype data scraping for Agrochemical Toxicity

Currently this script does the following:
1. takes a list of chemical names or PubChem CIDs
2. resolves each compound
3. retrieves basic chemical identity/ structure information
4. retrieves PubChem toxicity annotations
5. saves the results 

An example run:
Providing chemicals directly (you can also provide them in a file)
```bash
python pubchem_toxicity.py \
    diclofop-methyl \
    chlorsulfuron \
    azadirachtin \
    9750 \
    --out results
```

This will output something like
```text
results/
├── compound_summary.csv
├── toxicity_long.csv
└── raw/
    ├── 39985_toxicity.json
    ├── 47491_toxicity.json
    └── ...
```
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


PUG_REST: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PUG_VIEW: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view"

PROPERTY_FIELDS: List[str] = [
    "Title",
    "MolecularFormula",
    "MolecularWeight",
    "SMILES",
    "ConnectivitySMILES",
    "InChI",
    "InChIKey",
    "IUPACName",
]

SUMMARY_FIELDS: List[str] = [
    "input",
    "input_type",
    "resolution_status",
    "error",
    "cid",
    "title",
    "molecular_formula",
    "molecular_weight",
    "smiles",
    "connectivity_smiles",
    "inchi",
    "inchikey",
    "iupac_name",
    "toxicity_status",
    "toxicity_annotation_count",
    "toxicity_external_table_count",
    "raw_toxicity_json",
]

TOXICITY_FIELDS: List[str] = [
    "input",
    "cid",
    "record_title",
    "section_path",
    "section_heading",
    "information_name",
    "information_description",
    "value_text",
    "value_json",
    "external_table_name",
    "external_table_num_rows",
    "reference_number",
    "reference_source",
    "reference_source_id",
    "reference_description",
    "reference_url",
]


class PubChemClient:
    """Fetch PubChem records, retrying failures and spacing out requests."""

    def __init__(
        self,
        delay_seconds: float = 0.30,
        timeout_seconds: float = 30.0,
        user_agent: str = "AgrochemicalToxicityPrototype/0.1",
    ) -> None:
        self.delay_seconds: float = max(0.0, delay_seconds)
        self.timeout_seconds: float = timeout_seconds
        self._last_request_time: float = 0.0

        self.session: requests.Session = requests.Session()
        retry: Retry = Retry(
            total = 4,
            connect = 4,
            read = 4,
            status = 4,
            backoff_factor = 0.6,
            status_forcelist = (429, 500, 502, 503, 504),
            allowed_methods = frozenset(["GET"]),
            respect_retry_after_header = True,
        )
        adapter: HTTPAdapter = HTTPAdapter(max_retries = retry)
        self.session.mount("https://", adapter)
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "application/json",
            }
        )

    def _throttle(self) -> None:
        elapsed: float = time.monotonic() - self._last_request_time
        remaining: float = self.delay_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def get_json(self, url: str) -> Dict[str, Any]:
        """Request a JSON record, raising an exception for HTTP errors."""
        self._throttle()
        response: requests.Response = self.session.get(url, timeout = self.timeout_seconds)
        self._last_request_time = time.monotonic()
        response.raise_for_status()
        return response.json()

    def resolve_name_to_cid(self, name: str) -> int:
        """Use the first CID returned for a chemical name or synonym."""
        encoded_name: str = quote(name, safe = "")
        url: str = f"{PUG_REST}/compound/name/{encoded_name}/cids/JSON"
        data: Dict[str, Any] = self.get_json(url)
        cids: List[int] = data.get("IdentifierList", {}).get("CID", [])
        if not cids:
            raise ValueError(f"No PubChem CID found for name: {name}")
        # A name may match several compounds; this prototype keeps the first.
        return int(cids[0])

    def get_properties(self, cid: int) -> Dict[str, Any]:
        """Retrieve the identity and structure fields used in the summary CSV."""
        fields: str = ",".join(PROPERTY_FIELDS)
        url: str = f"{PUG_REST}/compound/cid/{cid}/property/{fields}/JSON"
        data: Dict[str, Any] = self.get_json(url)
        rows: List[Dict[str, Any]] = data.get("PropertyTable", {}).get("Properties", [])
        if not rows:
            raise ValueError(f"No property record returned for CID {cid}")
        return rows[0]

    def get_toxicity(self, cid: int) -> Dict[str, Any]:
        """Retrieve the compound's Toxicity section from PUG-View."""
        url: str = f"{PUG_VIEW}/data/compound/{cid}/JSON?heading=Toxicity"
        return self.get_json(url)


def parse_identifier(value: str) -> Tuple[str, str]:
    """Return the identifier type and its trimmed value."""
    value = value.strip()
    if not value:
        raise ValueError("Empty chemical identifier")
    if re.fullmatch(r"\d+", value):
        return "cid", value
    return "name", value


def extract_value_text(value: Any) -> str:
    """
    Convert common PUG-View Value objects to readable text.

    The original JSON is also saved separately, so this function is deliberately
    conservative: it extracts useful visible strings/numbers without trying to
    reinterpret toxicology semantics.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        list_parts: List[str] = [extract_value_text(item) for item in value]
        return " | ".join(part for part in list_parts if part)
    if not isinstance(value, dict):
        return str(value)

    parts: List[str] = []

    for item in value.get("StringWithMarkup", []) or []:
        if isinstance(item, dict):
            text: Any = item.get("String")
            if text:
                parts.append(str(text))
        elif item:
            parts.append(str(item))

    if "Number" in value:
        number: Any = value["Number"]
        if isinstance(number, list):
            parts.extend(str(x) for x in number)
        else:
            parts.append(str(number))

    if "Unit" in value and value["Unit"]:
        parts.append(str(value["Unit"]))

    if "Binary" in value and value["Binary"]:
        parts.append("[binary value]")

    # Generic fallback for value shapes not covered above, excluding metadata
    # that already has its own CSV columns.
    if not parts:
        metadata_fields: Set[str] = {"ExternalTableName", "ExternalTableNumRows"}
        for key, field_value in value.items():
            if key in metadata_fields:
                continue
            rendered: str = extract_value_text(field_value)
            if rendered:
                parts.append(f"{key}: {rendered}")

    return " ".join(parts).strip()


def build_reference_map(record: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """Index source references by the numbers used in annotation entries."""
    references: Dict[int, Dict[str, Any]] = {}
    for reference in record.get("Reference", []) or []:
        reference_number: Any = reference.get("ReferenceNumber")
        if isinstance(reference_number, int):
            references[reference_number] = reference
    return references


def flatten_toxicity(
    input_value: str,
    cid: int,
    toxicity_json: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Flatten PUG-View Information entries while retaining their section path."""
    record: Dict[str, Any] = toxicity_json.get("Record", {}) or {}
    reference_map: Dict[int, Dict[str, Any]] = build_reference_map(record)
    rows: List[Dict[str, Any]] = []

    def walk_sections(sections: Iterable[Dict[str, Any]], path: List[str]) -> None:
        """Visit nested sections, carrying their headings into each output row."""
        for section in sections or []:
            heading: str = str(section.get("TOCHeading") or "").strip()
            next_path: List[str] = path + ([heading] if heading else [])
            section_path: str = " > ".join(next_path)

            for information in section.get("Information", []) or []:
                value: Any = information.get("Value", {}) or {}
                reference_number: Any = information.get("ReferenceNumber")
                reference: Dict[str, Any] = {}
                if isinstance(reference_number, int):
                    reference = reference_map.get(reference_number, {})

                # Table details are only available when Value is a JSON object.
                external_table_name: Any = ""
                external_table_num_rows: Any = ""
                if isinstance(value, dict):
                    external_table_name = value.get("ExternalTableName", "")
                    external_table_num_rows = value.get("ExternalTableNumRows", "")

                rows.append(
                    {
                        "input": input_value,
                        "cid": cid,
                        "record_title": record.get("RecordTitle", ""),
                        "section_path": section_path,
                        "section_heading": heading,
                        "information_name": information.get("Name", ""),
                        "information_description": information.get("Description", ""),
                        "value_text": extract_value_text(value),
                        "value_json": json.dumps(
                            value, ensure_ascii = False, sort_keys = True
                        ),
                        "external_table_name": external_table_name,
                        "external_table_num_rows": external_table_num_rows,
                        "reference_number": (
                            reference_number if reference_number is not None else ""
                        ),
                        "reference_source": reference.get("SourceName", ""),
                        "reference_source_id": reference.get("SourceID", ""),
                        "reference_description": reference.get("Description", ""),
                        "reference_url": reference.get("URL", ""),
                    }
                )

            walk_sections(section.get("Section", []) or [], next_path)

    walk_sections(record.get("Section", []) or [], [])
    return rows


def normalize_property_row(
    input_value: str,
    input_type: str,
    cid: int,
    props: Dict[str, Any],
) -> Dict[str, Any]:
    """Map PubChem property names to the summary CSV's column names."""
    return {
        "input": input_value,
        "input_type": input_type,
        "resolution_status": "ok",
        "error": "",
        "cid": cid,
        "title": props.get("Title", ""),
        "molecular_formula": props.get("MolecularFormula", ""),
        "molecular_weight": props.get("MolecularWeight", ""),
        "smiles": props.get("SMILES", props.get("CanonicalSMILES", "")),
        "connectivity_smiles": props.get("ConnectivitySMILES", ""),
        "inchi": props.get("InChI", ""),
        "inchikey": props.get("InChIKey", ""),
        "iupac_name": props.get("IUPACName", ""),
        "toxicity_status": "",
        "toxicity_annotation_count": 0,
        "toxicity_external_table_count": 0,
        "raw_toxicity_json": "",
    }


def error_summary_row(
    input_value: str,
    input_type: str,
    message: str,
    cid: Optional[int] = None,
) -> Dict[str, Any]:
    """Keep failed inputs in the summary, leaving unavailable fields blank."""
    # Summary rows contain both text and numeric values.
    row: Dict[str, Any] = {field: "" for field in SUMMARY_FIELDS}
    row.update(
        {
            "input": input_value,
            "input_type": input_type,
            "resolution_status": "error",
            "error": message,
            "cid": cid if cid is not None else "",
            "toxicity_annotation_count": 0,
            "toxicity_external_table_count": 0,
        }
    )
    return row


def read_inputs(positional: List[str], file_path: Optional[Path]) -> List[str]:
    """Combine command-line and file inputs, keeping the first of each name."""
    values: List[str] = []

    for item in positional:
        item = item.strip()
        if item:
            values.append(item)

    if file_path is not None:
        with file_path.open("r", encoding = "utf-8-sig") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                values.append(line)

    # Stable de-duplication while preserving the user's order.
    seen: Set[str] = set()
    unique_values: List[str] = []
    for value in values:
        key: str = value.casefold()
        if key not in seen:
            seen.add(key)
            unique_values.append(value)
    return unique_values


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    """Write rows in a fixed column order, including a header for empty results."""
    path.parent.mkdir(parents = True, exist_ok = True)
    with path.open("w", newline = "", encoding = "utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames = fieldnames, extrasaction = "ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_raw_filename(cid: int) -> str:
    return f"{cid}_toxicity.json"


def run(args: argparse.Namespace) -> int:
    """Fetch each compound and save summary, annotation, and raw JSON files."""
    inputs: List[str] = read_inputs(args.identifiers, args.file)
    if not inputs:
        print(
            "No chemical identifiers supplied. Pass names/CIDs positionally or use --file.",
            file = sys.stderr,
        )
        return 2

    output_dir: Path = args.out
    raw_dir: Path = output_dir / "raw"
    raw_dir.mkdir(parents = True, exist_ok = True)

    client: PubChemClient = PubChemClient(
        delay_seconds = args.delay,
        timeout_seconds = args.timeout,
        user_agent = args.user_agent,
    )

    summaries: List[Dict[str, Any]] = []
    toxicity_rows: List[Dict[str, Any]] = []

    input_type: str
    parsed_identifier: str
    cid: int
    summary: Dict[str, Any]

    for index, input_value in enumerate(inputs, start = 1):
        print(f"[{index}/{len(inputs)}] {input_value}", file = sys.stderr)

        try:
            input_type, parsed_identifier = parse_identifier(input_value)
        except ValueError as exc:
            summaries.append(error_summary_row(input_value, "unknown", str(exc)))
            continue

        try:
            if input_type == "cid":
                cid = int(parsed_identifier)
            else:
                cid = client.resolve_name_to_cid(parsed_identifier)
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            summaries.append(
                error_summary_row(
                    input_value,
                    input_type,
                    f"CID resolution failed: {exc}",
                )
            )
            continue

        try:
            properties: Dict[str, Any] = client.get_properties(cid)
            summary = normalize_property_row(input_value, input_type, cid, properties)
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            summary = error_summary_row(
                input_value,
                input_type,
                f"Property retrieval failed: {exc}",
                cid = cid,
            )
            summaries.append(summary)
            continue

        raw_path: Path = raw_dir / safe_raw_filename(cid)

        try:
            toxicity_json: Dict[str, Any] = client.get_toxicity(cid)
            with raw_path.open("w", encoding = "utf-8") as handle:
                json.dump(toxicity_json, handle, ensure_ascii = False, indent = 2)

            compound_toxicity_rows: List[Dict[str, Any]] = flatten_toxicity(
                input_value, cid, toxicity_json
            )
            toxicity_rows.extend(compound_toxicity_rows)

            external_table_count: int = sum(
                1 for row in compound_toxicity_rows if row.get("external_table_name")
            )
            summary["toxicity_status"] = "ok"
            summary["toxicity_annotation_count"] = len(compound_toxicity_rows)
            summary["toxicity_external_table_count"] = external_table_count
            summary["raw_toxicity_json"] = str(raw_path.relative_to(output_dir))

        except requests.HTTPError as exc:
            status_code: Optional[int] = (
                exc.response.status_code if exc.response is not None else None
            )
            if status_code == 404:
                summary["toxicity_status"] = "not_found"
                summary["error"] = (
                    "No PubChem PUG-View Toxicity section was returned for this CID."
                )
            else:
                summary["toxicity_status"] = "error"
                summary["error"] = f"Toxicity retrieval failed: {exc}"
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            summary["toxicity_status"] = "error"
            summary["error"] = f"Toxicity retrieval failed: {exc}"

        summaries.append(summary)

    write_csv(output_dir / "compound_summary.csv", summaries, SUMMARY_FIELDS)
    write_csv(output_dir / "toxicity_long.csv", toxicity_rows, TOXICITY_FIELDS)

    print(
        f"Wrote {len(summaries)} compound summary row(s) and "
        f"{len(toxicity_rows)} toxicity annotation row(s) to {output_dir}",
        file = sys.stderr,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Define the script's command-line inputs and request settings."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description = (
            "Retrieve basic PubChem identity/structure fields and PUG-View "
            "toxicity annotations for chemical names or PubChem CIDs."
        )
    )
    parser.add_argument(
        "identifiers",
        nargs = "*",
        help = "Chemical names and/or numeric PubChem CIDs.",
    )
    parser.add_argument(
        "--file",
        type = Path,
        help = (
            "Optional text file containing one chemical name or PubChem CID "
            "per line. Blank lines and lines beginning with # are ignored."
        ),
    )
    parser.add_argument(
        "--out",
        type = Path,
        default = Path("results"),
        help = "Output directory (default: ./results).",
    )
    parser.add_argument(
        "--delay",
        type = float,
        default = 0.30,
        help = "Minimum delay between PubChem requests in seconds (default: 0.30).",
    )
    parser.add_argument(
        "--timeout",
        type = float,
        default = 30.0,
        help = "Per-request timeout in seconds (default: 30).",
    )
    parser.add_argument(
        "--user-agent",
        default = "AgrochemicalToxicityPrototype/0.1",
        help = "HTTP User-Agent sent to PubChem.",
    )
    return parser


def main() -> int:
    """Parse command-line options and return the run's exit code."""
    parser: argparse.ArgumentParser = build_parser()
    args: argparse.Namespace = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
