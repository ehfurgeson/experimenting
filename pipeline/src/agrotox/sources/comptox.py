"""EPA CompTox transport, without storage or interpretation."""

import math
import os
import time
from collections.abc import Callable, Mapping
from typing import Any, NamedTuple, Protocol
from urllib.parse import quote

import requests

CTX_API = "https://comptox.epa.gov/ctx-api"
API_KEY_ENVIRONMENT = "COMPTOX_API_KEY"


class SearchResult(NamedTuple):
    """The candidates of one exact search and the provider's near misses."""

    candidates: list[dict[str, Any]]
    suggestions: list[str]


class HTTPResponse(Protocol):
    """Response operations used by the adapter."""

    status_code: int
    headers: Mapping[str, str]

    def raise_for_status(self) -> None: ...

    def json(self) -> Any: ...


def _suggestions(response: HTTPResponse) -> list[str]:
    """Read the near-miss identifiers the provider offers for a failed search."""
    try:
        payload = response.json()
    except ValueError:
        return []
    if not isinstance(payload, dict):
        return []
    suggestions = payload.get("suggestions")
    if not isinstance(suggestions, list):
        return []
    return [item for item in suggestions if isinstance(item, str)]


class HTTPClient(Protocol):
    """Minimal transport boundary for sessions and offline fakes."""

    def get(
        self, url: str, *, params: dict[str, str] | None, headers: dict[str, str],
        timeout: tuple[int, int], allow_redirects: bool,
    ) -> HTTPResponse: ...


class ComptoxClient:
    """Read EPA CompTox chemical records using an injectable transport.

    Construction performs no requests. The API key travels in a request header
    only, so it never appears in a URL, a stored snapshot, or an error message.
    """

    def __init__(
        self, http: HTTPClient | None = None, *, api_key: str | None = None,
        interval: float = 0.25, retries: int = 4,
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
        self.api_key = api_key if api_key is not None else os.environ.get(API_KEY_ENVIRONMENT)
        if self.api_key is not None and not isinstance(self.api_key, str):
            raise ValueError("The EPA API key must be a string")
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

    def _request(self, url: str) -> HTTPResponse:
        if not self.api_key:
            raise ValueError(
                f"An EPA API key is required; set {API_KEY_ENVIRONMENT} or pass api_key"
            )
        headers = {"x-api-key": self.api_key, "accept": "application/json"}
        delay = 0.0
        for attempt in range(self.retries + 1):
            self._pace(delay)
            try:
                response = self.http.get(
                    url, params = None, headers = headers,
                    timeout = (10, 40), allow_redirects = False,
                )
            except requests.exceptions.SSLError:
                raise
            except (requests.Timeout, requests.ConnectionError):
                if attempt == self.retries:
                    raise
                delay = 2.0 ** attempt
                continue
            if response.status_code in {429, 500, 502, 503, 504} and attempt < self.retries:
                delay = max(2.0 ** attempt, 0.0)
                continue
            return response
        raise RuntimeError("Request attempts exhausted without a response")

    def _get(self, path: str) -> Any:
        response = self._request(f"{CTX_API}{path}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        if response.status_code != 200:
            raise requests.HTTPError(
                f"Unexpected CompTox HTTP {response.status_code}", response = response,
            )
        return response.json()

    def search_equal(self, term: str) -> SearchResult:
        """Return the chemicals whose identifier equals the supplied term.

        The term may be a chemical name, DTXSID, DTXCID, CAS Registry Number,
        or InChIKey. This endpoint documents its 400 response as "data not
        found", so a term with no match is an empty result rather than an
        error. The provider's near-miss suggestions are kept, because they
        often name the alternative structure of the same compound.
        """
        if not isinstance(term, str) or not term.strip():
            raise ValueError("An EPA search term must be a nonempty string")
        response = self._request(
            f"{CTX_API}/chemical/search/equal/{quote(term.strip(), safe = '')}"
        )
        if response.status_code == 400:
            return SearchResult(candidates = [], suggestions = _suggestions(response))
        if response.status_code == 404:
            return SearchResult(candidates = [], suggestions = [])
        response.raise_for_status()
        if response.status_code != 200:
            raise requests.HTTPError(
                f"Unexpected CompTox HTTP {response.status_code}", response = response,
            )
        payload = response.json()
        if not isinstance(payload, list):
            # Malformed source data follows the adapter's ValueError contract.
            raise ValueError("Expected a list of EPA chemical search results")  # noqa: TRY004
        return SearchResult(
            candidates = [item for item in payload if isinstance(item, dict)],
            suggestions = [],
        )


    def bioactivity(self, dtxsid: str) -> list[dict[str, Any]]:
        """Return the in-vitro bioactivity records for one substance.

        The response holds one row per tested chemical and assay endpoint. A
        substance that was never tested in an assay has no row for it, which is
        different from a row that records an inactive result.
        """
        if not isinstance(dtxsid, str) or not dtxsid.strip():
            raise ValueError("A DTXSID must be a nonempty string")
        payload = self._get(
            f"/bioactivity/data/search/by-dtxsid/{quote(dtxsid.strip(), safe = '')}"
        )
        if payload is None:
            return []
        if not isinstance(payload, list):
            # Malformed source data follows the adapter's ValueError contract.
            raise ValueError("Expected a list of EPA bioactivity records")  # noqa: TRY004
        return [item for item in payload if isinstance(item, dict)]

    def assay(self, aeid: int) -> dict[str, Any] | None:
        """Return the annotation of one ToxCast assay endpoint.

        The provider serves this endpoint as a list holding the single
        annotation, so the list is unwrapped here.
        """
        if type(aeid) is not int or aeid <= 0:
            raise ValueError("A ToxCast assay endpoint ID must be a positive integer")
        payload = self._get(f"/bioactivity/assay/search/by-aeid/{aeid}")
        if payload is None:
            return None
        if isinstance(payload, list):
            if not payload:
                return None
            payload = payload[0]
        if not isinstance(payload, dict):
            # Malformed source data follows the adapter's ValueError contract.
            raise ValueError("Expected a single EPA assay annotation object")  # noqa: TRY004
        return payload

    def hazard(self, dtxsid: str) -> list[dict[str, Any]]:
        """Return the hazard observations recorded for one substance.

        Each record is one study observation with its own context: endpoint,
        species, route, duration, value, and its bibliographic reference. The
        record also states whether it is experimental or predicted.
        """
        if not isinstance(dtxsid, str) or not dtxsid.strip():
            raise ValueError("A DTXSID must be a nonempty string")
        payload = self._get(f"/hazard/toxval/search/by-dtxsid/{quote(dtxsid.strip(), safe = '')}")
        if payload is None:
            return []
        if not isinstance(payload, list):
            # Malformed source data follows the adapter's ValueError contract.
            raise ValueError("Expected a list of EPA hazard records")  # noqa: TRY004
        return [item for item in payload if isinstance(item, dict)]

    def property_experimental(self, dtxsid: str) -> list[dict[str, Any]]:
        """Return the experimental property records recorded for one substance."""
        return self._property_list("experimental", dtxsid)

    def property_predicted(self, dtxsid: str) -> list[dict[str, Any]]:
        """Return the computed property predictions recorded for one substance."""
        return self._property_list("predicted", dtxsid)

    def _property_list(self, kind: str, dtxsid: str) -> list[dict[str, Any]]:
        if not isinstance(dtxsid, str) or not dtxsid.strip():
            raise ValueError("A DTXSID must be a nonempty string")
        path = f"/chemical/property/{kind}/search/by-dtxsid/{quote(dtxsid.strip(), safe = '')}"
        payload = self._get(path)
        if payload is None:
            return []
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            # Malformed source data follows the adapter's ValueError contract.
            raise ValueError("Expected a list of EPA property records")  # noqa: TRY004
        return [item for item in payload if isinstance(item, dict)]

    def details(self, dtxsid: str) -> dict[str, Any] | None:
        """Return the chemical record for one DTXSID, or None when absent."""
        if not isinstance(dtxsid, str) or not dtxsid.strip():
            raise ValueError("A DTXSID must be a nonempty string")
        payload = self._get(f"/chemical/detail/search/by-dtxsid/{quote(dtxsid.strip(), safe = '')}")
        if payload is None:
            return None
        if not isinstance(payload, dict):
            # Malformed source data follows the adapter's ValueError contract.
            raise ValueError("Expected a single EPA chemical detail object")  # noqa: TRY004
        return payload
