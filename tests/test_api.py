"""Tests for the Pro Vision Engine FastAPI application."""

from fastapi.testclient import TestClient

from src.api.app import create_app


def create_client() -> TestClient:
    """Create a test client for the API."""

    application = create_app()

    return TestClient(application)


def test_health_endpoint() -> None:
    client = create_client()

    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "pro-vision-engine"
    assert payload["version"] == "0.1.0-alpha"


def test_coupon_list_endpoint() -> None:
    client = create_client()

    response = client.get(
        "/api/v1/coupons"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] == 3
    assert payload["game_types"] == [
        "topptipset",
        "stryktipset",
        "europatipset",
    ]


def test_coupon_endpoint_returns_valid_coupon() -> None:
    client = create_client()

    response = client.get(
        "/api/v1/coupons/topptipset"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["schema_version"] == "1.0"
    assert (
        payload["coupon"]["game_type"]
        == "topptipset"
    )
    assert payload["coupon"]["match_count"] == 8
    assert len(payload["matches"]) == 8

    first_match = payload["matches"][0]

    assert first_match["number"] == 1
    assert first_match["home_team"] == "Arsenal"
    assert first_match["away_team"] == "Chelsea"


def test_unknown_coupon_returns_not_found() -> None:
    client = create_client()

    response = client.get(
        "/api/v1/coupons/unknown"
    )

    assert response.status_code == 404

    payload = response.json()

    assert "Unknown demonstration game type" in (
        payload["detail"]
    )