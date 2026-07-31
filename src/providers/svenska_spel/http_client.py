"""HTTP client for structured Svenska Spel coupon data."""

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.providers.http_transport import (
    HttpTransport,
    HttpTransportError,
    UrllibHttpTransport,
)
from src.providers.svenska_spel.models import (
    SvenskaSpelCouponData,
)
from src.providers.svenska_spel.payload_parser import (
    SvenskaSpelPayloadError,
    SvenskaSpelPayloadParser,
)


class SvenskaSpelHttpClientError(ValueError):
    """Raised when Svenska Spel HTTP data cannot be retrieved or parsed."""


class SvenskaSpelHttpClient:
    """Retrieves structured Svenska Spel coupon data over HTTP."""

    def __init__(
        self,
        transport: HttpTransport | None = None,
        parser: SvenskaSpelPayloadParser | None = None,
        *,
        timeout: float = 15.0,
    ) -> None:
        """Create the client with an HTTP transport and payload parser."""

        if timeout <= 0:
            raise ValueError("HTTP timeout must be greater than zero.")

        self._transport = transport or UrllibHttpTransport()
        self._parser = parser or SvenskaSpelPayloadParser()
        self._timeout = timeout

    def fetch_coupon(
        self,
        source_reference: str | Path,
    ) -> SvenskaSpelCouponData:
        """Retrieve and parse one Svenska Spel coupon payload."""

        url = str(source_reference)
        self._validate_url(url)

        try:
            response = self._transport.get(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Pro-Vision-Engine/0.1.0",
                },
                timeout=self._timeout,
            )
        except HttpTransportError as error:
            raise SvenskaSpelHttpClientError(
                f"Could not retrieve Svenska Spel data from {url!r}."
            ) from error

        if not 200 <= response.status_code < 300:
            raise SvenskaSpelHttpClientError(
                "Svenska Spel HTTP request returned status "
                f"{response.status_code}."
            )

        self._validate_content_type(
            response.content_type
        )

        raw_payload = self._decode_json(
            response.body
        )

        try:
            return self._parser.parse(raw_payload)
        except SvenskaSpelPayloadError as error:
            raise SvenskaSpelHttpClientError(
                str(error)
            ) from error

    @staticmethod
    def _validate_url(url: str) -> None:
        """Ensure that the source is an HTTP or HTTPS URL."""

        parsed_url = urlparse(url)

        if (
            parsed_url.scheme not in {"http", "https"}
            or not parsed_url.netloc
        ):
            raise SvenskaSpelHttpClientError(
                "Svenska Spel HTTP source must be a valid "
                "HTTP or HTTPS URL."
            )

    @staticmethod
    def _validate_content_type(
        content_type: str | None,
    ) -> None:
        """Ensure that the response represents JSON data."""

        if content_type is None:
            return

        normalized_type = content_type.casefold()

        if (
            normalized_type != "application/json"
            and not normalized_type.endswith("+json")
        ):
            raise SvenskaSpelHttpClientError(
                "Svenska Spel HTTP response must contain JSON, "
                f"but received {content_type!r}."
            )

    @staticmethod
    def _decode_json(body: bytes) -> Any:
        """Decode an HTTP response body as UTF-8 JSON."""

        try:
            text = body.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise SvenskaSpelHttpClientError(
                "Svenska Spel HTTP response was not valid UTF-8."
            ) from error

        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise SvenskaSpelHttpClientError(
                "Svenska Spel HTTP response contained invalid JSON."
            ) from error