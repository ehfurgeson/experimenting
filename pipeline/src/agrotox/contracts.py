"""Shared input record types."""

from typing import Any, Literal, NotRequired, Protocol, TypedDict


class Query(TypedDict):
    """Curated input retaining its trimmed display spelling apart from identity.

    When equivalent inputs are combined, retain the first query spelling.
    Canonical keys are derived separately with ``inputs.query_key``.
    """

    query: str
    chemical_group: NotRequired[str]
    subgroup: NotRequired[str]
    hrac_group: NotRequired[str]
    source_note: NotRequired[str]


class Snapshot(TypedDict):
    """Resolved identity with one property record and explicit retrieval metadata."""

    cid: int
    properties: dict[str, Any]
    metadata: dict[str, Any]
    toxicity: NotRequired[dict[str, Any] | None]


class Compound(TypedDict):
    """One resolved CID or unresolved query identity, retaining all input aliases."""

    compound_id: str
    pubchem_cid: int | None
    input_queries: list[str]
    preferred_name: str | None
    chemical_group: str | None
    subgroup: str | None
    hrac_group: str | None
    source_notes: list[str]
    inchi: str | None
    inchikey: str | None
    smiles: str | None
    connectivity_smiles: str | None
    molecular_formula: str | None
    molecular_weight: float | None
    iupac_name: str | None
    resolution_status: Literal["resolved", "unresolved"]
    toxicity_status: Literal["found", "missing", "pending", "not_retrieved"]


class Source(Protocol):
    """Injectable identity and toxicity source, without storage or interpretation."""

    def resolve(self, query: str) -> int: ...

    def properties(self, cid: int) -> dict[str, Any]:
        """Return the original property response envelope for this CID."""
        ...

    def toxicity(self, cid: int) -> dict[str, Any] | None:
        """Return a toxicity envelope, or None for an observed missing section."""
        ...


class Outcome(TypedDict):
    """One retrieval result, retaining enough context to review a batch failure."""

    query: str
    cid: int | None
    status: Literal["fetched", "skipped", "error"]
    stage: str
    error_type: str | None
    message: str | None


class SourceReference(TypedDict):
    """A referenced source, including raw metadata or nulls for a dangling number."""

    reference_number: int
    source_name: str | None
    source_url: str | None
    reference_json: str | None


class Annotation(TypedDict):
    """One value representation with stable identity and original source context."""

    annotation_id: str
    compound_id: str
    record_title: str | None
    section_path: list[str]
    information_name: str | None
    description: str | None
    value_raw: str
    value_kind: str
    reference_numbers: list[int]
    sources: list[SourceReference]
    information_url: str | None
    information_json: str
    raw_file: str
    retrieved_at: str


ValueQualifier = Literal["=", "<", ">", "<=", ">=", "range"]


class ParsedValue(TypedDict):
    """Unconverted exact result, inequality threshold, or ascending interval."""

    value_numeric: float | None
    value_lower: float | None
    value_upper: float | None
    qualifier: ValueQualifier
    unit_raw: str


class Measurement(Annotation):
    """One normalized or reviewable row for one source annotation."""

    endpoint: str | None
    study_type: str | None
    duration_class: str | None
    effect: str | None
    evidence_basis: str | None
    benchmark_response: str | None
    benchmark_response_type: str | None
    model_name: str | None
    model_id: str | None
    confidence_level: str | None
    study_id: str | None
    species: str | None
    organism_group: str | None
    exposure_route: str | None
    medium: str | None
    duration_value: float | None
    duration_unit: str | None
    duration_hours: float | None
    value_numeric: float | None
    value_lower: float | None
    value_upper: float | None
    qualifier: ValueQualifier | None
    unit_raw: str | None
    unit_standardized: str | None
    value_standardized: float | None
    value_lower_standardized: float | None
    value_upper_standardized: float | None
    formulation_flag: bool
    parse_status: Literal["complete", "partial", "failed"]
    parse_note: str
