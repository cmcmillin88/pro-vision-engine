"""Tests for the Pro Vision Engine FastAPI application."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.settings import ApiSettings
from src.services.coupon_catalog_protocol import (
    CouponCatalog,
)
from src.services.coupon_source_registry import (
    CouponSourceRegistry,
)
from src.services.demo_coupon_catalog import (
    DemoCouponCatalog,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COUPON_DIRECTORY = (
    PROJECT_ROOT
    / "examples"
    / "svenska_spel"
)


def create_client(
    settings: ApiSettings | None = None,
    catalog: CouponCatalog | None = None,
    registry: CouponSourceRegistry | None = None,
) -> TestClient:
    """Create a test client for the API."""

    application = create_app(
        settings=settings,
        catalog=catalog,
        registry=registry,
    )

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


def test_openapi_documents_coupon_response_schema() -> None:
    client = create_client()

    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200

    openapi_document = response.json()
    schemas = (
        openapi_document["components"]["schemas"]
    )

    assert "CouponResponse" in schemas
    assert "CouponMetadataResponse" in schemas
    assert "MatchResponse" in schemas

    coupon_operation = openapi_document["paths"][
        "/api/v1/coupons/{game_type}"
    ]["get"]

    response_schema = coupon_operation["responses"][
        "200"
    ]["content"]["application/json"]["schema"]

    assert response_schema["$ref"] == (
        "#/components/schemas/CouponResponse"
    )


def test_allowed_origin_receives_cors_header() -> None:
    allowed_origin = "https://frontend.example"

    settings = ApiSettings(
        allowed_origins=(
            allowed_origin,
        )
    )
    client = create_client(
        settings
    )

    response = client.get(
        "/api/v1/health",
        headers={
            "Origin": allowed_origin,
        },
    )

    assert response.status_code == 200
    assert response.headers[
        "access-control-allow-origin"
    ] == allowed_origin


def test_disallowed_origin_receives_no_cors_header() -> None:
    settings = ApiSettings(
        allowed_origins=(
            "https://allowed.example",
        )
    )
    client = create_client(
        settings
    )

    response = client.get(
        "/api/v1/health",
        headers={
            "Origin": "https://blocked.example",
        },
    )

    assert response.status_code == 200
    assert (
        "access-control-allow-origin"
        not in response.headers
    )


def test_api_accepts_explicit_source_registry() -> None:
    catalog = DemoCouponCatalog(
        COUPON_DIRECTORY
    )
    registry = CouponSourceRegistry(
        [catalog]
    )
    client = create_client(
        registry=registry
    )

    response = client.get(
        "/api/v1/coupons/topptipset"
    )

    assert response.status_code == 200
    assert (
        response.json()["coupon"]["id"]
        == "DEMO-TT-JSON-001"
    )


def test_api_rejects_catalog_and_registry_together() -> None:
    catalog = DemoCouponCatalog(
        COUPON_DIRECTORY
    )
    registry = CouponSourceRegistry(
        [catalog]
    )

    with pytest.raises(
        ValueError,
        match="either catalog or registry",
    ):
        create_app(
            catalog=catalog,
            registry=registry,
        )