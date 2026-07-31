"""Reusable HTTP transport components for external providers."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """Represents a completed HTTP response."""

    status_code: int
    body: bytes
    content_type: str | None = None


class HttpTransportError(ConnectionError):
    """Raised when an HTTP request cannot be completed."""


@runtime_checkable
class HttpTransport(Protocol):
    """Defines the HTTP behavior required by provider clients."""

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 15.0,
    ) -> HttpResponse:
        """Perform an HTTP GET request."""

        ...


class UrllibHttpTransport:
    """Performs HTTP requests using Python's standard library."""

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 15.0,
    ) -> HttpResponse:
        """Perform an HTTP GET request and return its response."""

        request = Request(
            url=url,
            headers=headers or {},
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=timeout,
            ) as response:
                return HttpResponse(
                    status_code=response.status,
                    body=response.read(),
                    content_type=response.headers.get_content_type(),
                )
        except HTTPError as error:
            return HttpResponse(
                status_code=error.code,
                body=error.read(),
                content_type=error.headers.get_content_type(),
            )
        except (URLError, OSError) as error:
            raise HttpTransportError(
                f"HTTP request failed for {url!r}."
            ) from error