"""PubChem transport and response validation, without storage or interpretation."""

import math
import time
from collections.abc import Callable, Mapping
from email.utils import parsedate_to_datetime
from typing import Any, Protocol
from urllib.parse import quote

import requests

from ..inputs import classify_query
from .pubchem_payloads import validate_properties, validate_toxicity

PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PUG_VIEW = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view"
PROPERTIES = (
    "Title,MolecularFormula,MolecularWeight,SMILES,ConnectivitySMILES,InChI,InChIKey,IUPACName"
)


class HTTPResponse(Protocol):
    """Response operations used by the adapter."""

    status_code: int
    headers: Mapping[str, str]

    def raise_for_status(self) -> None: ...

    def json(self) -> Any: ...


class HTTPClient(Protocol):
    """Minimal transport boundary for sessions and offline fakes."""

    def get(
        self, url: str, *, params: dict[str, str] | None,
        timeout: tuple[int, int], allow_redirects: bool,
    ) -> HTTPResponse: ...


class PubChemClient:
    """Resolve queries and return validated envelopes using an injectable transport.

    Construction performs no requests. Pacing covers every attempt, including
    retries, using injectable monotonic/epoch clocks and sleep.
    """

    def __init__(
        self, http: HTTPClient | None = None, *, interval: float = 0.25, retries: int = 4,
        clock: Callable[[], float] | None = None,
        wall_clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        if (
            isinstance(interval, bool) or not isinstance(interval, (int, float))
            or not math.isfinite(interval) or interval < 0
        ):
            raise ValueError("Request interval must be nonnegative and finite")
        if type(retries) is not int or retries < 0:
            raise ValueError("Retry count must be a nonnegative integer")
        self.http = http if http is not None else requests.Session()
        if isinstance(self.http, requests.Session):
            no_retries = requests.adapters.HTTPAdapter(max_retries = 0).max_retries
            for adapter in self.http.adapters.values():
                if isinstance(adapter, requests.adapters.HTTPAdapter):
                    adapter.max_retries = no_retries
        self.interval = interval
        self.retries = retries
        self.clock = clock if clock is not None else time.monotonic
        self.wall_clock = wall_clock if wall_clock is not None else time.time
        self.sleep = sleep if sleep is not None else time.sleep
        self.last_request: float | None = None

    def _pace(self, retry_delay: float) -> None:
        now = self.clock()
        deadline = now + retry_delay
        if self.last_request is not None:
            deadline = max(deadline, self.last_request + self.interval)
        if deadline > now:
            self.sleep(deadline - now)
        self.last_request = self.clock()

    def _retry_after(self, response: HTTPResponse) -> float:
        header = response.headers.get("Retry-After", "").strip()
        try:
            if header.isascii() and header.isdecimal():
                delay = float(header)
            else:
                date = parsedate_to_datetime(header)
                if date.utcoffset() is None:
                    return 0.0
                delay = date.timestamp() - self.wall_clock()
        except (TypeError, ValueError, OverflowError, OSError):
            return 0.0
        return max(0.0, delay) if math.isfinite(delay) else 0.0

    def _request(self, url: str, params: dict[str, str] | None) -> HTTPResponse:
        delay = 0.0
        for attempt in range(self.retries + 1):
            self._pace(delay)
            try:
                response = self.http.get(
                    url, params = params, timeout = (10, 40), allow_redirects = False,
                )
            except requests.exceptions.SSLError:
                raise
            except (requests.Timeout, requests.ConnectionError):
                if attempt == self.retries:
                    raise
                delay = 2.0 ** attempt
                continue
            if response.status_code in {429, 500, 502, 503, 504} and attempt < self.retries:
                delay = max(2.0 ** attempt, self._retry_after(response))
                continue
            return response
        raise RuntimeError("Request attempts exhausted without a response")

    def _get(
        self, url: str, params: dict[str, str] | None = None, *, missing_ok: bool = False
    ) -> dict[str, Any] | None:
        response = self._request(url, params)
        if missing_ok and response.status_code == 404:
            return None
        response.raise_for_status()
        if response.status_code != 200:
            raise requests.HTTPError(
                f"Unexpected PubChem HTTP {response.status_code}", response = response,
            )
        payload = response.json()
        if not isinstance(payload, dict):
            # Malformed response data is a ValueError at the source boundary.
            raise ValueError("Expected a PubChem JSON object")  # noqa: TRY004
        return payload

    def resolve(self, query: str) -> int:
        """Return a positive CID, requiring exactly one match for a name."""
        kind, value = classify_query(query)
        if kind == "cid":
            return int(value)
        payload = self._get(f"{PUG}/compound/name/{quote(value, safe = '')}/cids/JSON")
        identifiers = payload.get("IdentifierList")
        cids = identifiers.get("CID") if isinstance(identifiers, dict) else None
        if not isinstance(cids, list) or any(type(cid) is not int or cid <= 0 for cid in cids):
            raise ValueError(f"Invalid PubChem CID list for {query!r}")
        if not cids:
            raise LookupError(f"No PubChem CID found for {query!r}")
        if len(cids) != 1:
            raise ValueError(f"Ambiguous PubChem name {query!r}: {cids!r}; use an explicit CID")
        return cids[0]

    def properties(self, cid: int) -> dict[str, Any]:
        """Retrieve and validate the original identity/structure envelope."""
        self._validate_cid(cid)
        payload = self._get(f"{PUG}/compound/cid/{cid}/property/{PROPERTIES}/JSON")
        validate_properties(payload, cid)
        return payload

    def toxicity(self, cid: int) -> dict[str, Any] | None:
        """Retrieve the Toxicity section; only its 404 response means missing."""
        self._validate_cid(cid)
        payload = self._get(
            f"{PUG_VIEW}/data/compound/{cid}/JSON", {"heading": "Toxicity"}, missing_ok = True,
        )
        if payload is not None:
            validate_toxicity(payload, cid)
        return payload

    @staticmethod
    def _validate_cid(cid: int) -> None:
        if type(cid) is not int or cid <= 0:
            raise ValueError("PubChem CID must be a positive integer")
