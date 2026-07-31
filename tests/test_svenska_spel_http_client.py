"""Tests for the Svenska Spel HTTP client."""

import json
from pathlib import Path

import pytest

from src.importer.svenska_spel_importer import (
    SvenskaSpelImporter,
)
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.providers.http_transport import (
    HttpResponse,
    HttpTransport,
    UrllibHttpTransport,
)
from src.providers.svenska_spel.client_protocol import (
    SvenskaSpelClient,
)
from src.providers.svenska_spel.http_client import (
    SvenskaSpelHttpClient,
    SvenskaSpelHttpClientError,
)
from src.services.coupon_import_service import (
    CouponImportService,
)


class FakeHttpTransport:
    """HTTP transport that returns a prepared response."""

    def __init__(
        self,
        response: HttpResponse,
    ) -> None:
        self.response = response
        self.received_url: str | None = None
        self.received_headers: dict[str, str] | None = None
        self.received_timeout: float | None = None

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 15.0,
    ) -> HttpResponse:
        """Record the request and return the prepared response."""

        self.received_url = url
        self.received_headers = headers
        self.received_timeout = timeout

        return self.response


def create_valid_payload() -> dict[str, object]:
    """Create complete Topptipset HTTP test data."""

    matches = [
        {
            "match_number": match_number,
            "home_team": f"Home Team {match_number}",
            "away_team": f"Away Team {match_number}",
            "competition": "Test League",
            "kickoff": "2026-08-01T16:00:00+02:00",
        }
        for match_number in range(1, 9)
    ]

    return {
        "game_type": "Topptipset",
        "coupon_id": "TT-HTTP-TEST-001",
        "deadline": "2026-08-01T15:00:00+02:00",
        "matches": matches,
    }


def create_json_response(
    payload: dict[str, object],
) -> HttpResponse:
    """Create an HTTP JSON response for tests."""

    return HttpResponse(
        status_code=200,
        body=json.dumps(payload).encode("utf-8"),
        content_type="application/json",
    )


def test_http_client_fetches_and_parses_coupon() -> None:
    transport = FakeHttpTransport(
        create_json_response(
            create_valid_payload()
        )
    )

    client = SvenskaSpelHttpClient(
        transport,
        timeout=10.0,
    )

    coupon_data = client.fetch_coupon(
        "https://example.test/topptipset"
    )

    assert transport.received_url == (
        "https://example.test/topptipset"
    )
    assert transport.received_headers is not None
    assert (
        transport.received_headers["Accept"]
        == "application/json"
    )
    assert transport.received_timeout == 10.0

    assert coupon_data.game_type == "Topptipset"
    assert coupon_data.coupon_id == "TT-HTTP-TEST-001"
    assert len(coupon_data.matches) == 8


def test_http_client_satisfies_client_protocol() -> None:
    transport = FakeHttpTransport(
        create_json_response(
            create_valid_payload()
        )
    )

    client = SvenskaSpelHttpClient(transport)

    assert isinstance(client, SvenskaSpelClient)


def test_urllib_transport_satisfies_transport_protocol() -> None:
    transport = UrllibHttpTransport()

    assert isinstance(transport, HttpTransport)


def test_http_client_rejects_error_status() -> None:
    transport = FakeHttpTransport(
        HttpResponse(
            status_code=404,
            body=b'{"error": "not found"}',
            content_type="application/json",
        )
    )

    client = SvenskaSpelHttpClient(transport)

    with pytest.raises(
        SvenskaSpelHttpClientError,
        match="status 404",
    ):
        client.fetch_coupon(
            "https://example.test/missing"
        )


def test_http_client_rejects_non_json_response() -> None:
    transport = FakeHttpTransport(
        HttpResponse(
            status_code=200,
            body=b"<html></html>",
            content_type="text/html",
        )
    )

    client = SvenskaSpelHttpClient(transport)

    with pytest.raises(
        SvenskaSpelHttpClientError,
        match="must contain JSON",
    ):
        client.fetch_coupon(
            "https://example.test/html"
        )


def test_http_client_rejects_invalid_json() -> None:
    transport = FakeHttpTransport(
        HttpResponse(
            status_code=200,
            body=b"{invalid json",
            content_type="application/json",
        )
    )

    client = SvenskaSpelHttpClient(transport)

    with pytest.raises(
        SvenskaSpelHttpClientError,
        match="invalid JSON",
    ):
        client.fetch_coupon(
            "https://example.test/invalid"
        )


def test_complete_http_import_chain() -> None:
    transport = FakeHttpTransport(
        create_json_response(
            create_valid_payload()
        )
    )

    client = SvenskaSpelHttpClient(transport)
    importer = SvenskaSpelImporter(client)
    service = CouponImportService(importer)

    coupon = service.import_coupon(
        "https://example.test/topptipset"
    )

    assert coupon.game_type is GameType.TOPPTIPSET
    assert coupon.source is ImportSource.SVENSKA_SPEL
    assert coupon.coupon_id == "TT-HTTP-TEST-001"
    assert len(coupon) == 8