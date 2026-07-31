"""Tests for the OpenAPI JSON exporter."""

import json
from pathlib import Path

import pytest

from src.api.app import create_app
from src.exporters.openapi_json_exporter import (
    OpenApiJsonExporter,
)


def test_exporter_creates_openapi_document() -> None:
    application = create_app()
    exporter = OpenApiJsonExporter()

    payload = exporter.to_dict(
        application
    )

    assert payload["openapi"].startswith("3.")
    assert (
        payload["info"]["title"]
        == "Pro Vision Engine API"
    )
    assert (
        payload["info"]["version"]
        == "0.1.0-alpha"
    )


def test_exporter_includes_expected_endpoints() -> None:
    application = create_app()
    exporter = OpenApiJsonExporter()

    payload = exporter.to_dict(
        application
    )

    paths = payload["paths"]

    assert "/api/v1/health" in paths
    assert "/api/v1/coupons" in paths
    assert (
        "/api/v1/coupons/{game_type}"
        in paths
    )


def test_exporter_includes_typed_schemas() -> None:
    application = create_app()
    exporter = OpenApiJsonExporter()

    payload = exporter.to_dict(
        application
    )

    schemas = payload[
        "components"
    ]["schemas"]

    expected_schemas = {
        "HealthResponse",
        "CouponListResponse",
        "CouponMetadataResponse",
        "MatchResponse",
        "CouponResponse",
        "ErrorResponse",
    }

    assert expected_schemas.issubset(
        schemas
    )


def test_exporter_returns_independent_copy() -> None:
    application = create_app()
    exporter = OpenApiJsonExporter()

    payload = exporter.to_dict(
        application
    )

    payload["info"]["title"] = (
        "Changed title"
    )

    original_schema = application.openapi()

    assert (
        original_schema["info"]["title"]
        == "Pro Vision Engine API"
    )


def test_exporter_serializes_deterministic_json() -> None:
    application = create_app()
    exporter = OpenApiJsonExporter()

    first_result = exporter.to_json(
        application
    )
    second_result = exporter.to_json(
        application
    )

    assert first_result == second_result

    decoded_payload = json.loads(
        first_result
    )

    assert (
        decoded_payload["info"]["title"]
        == "Pro Vision Engine API"
    )


def test_exporter_writes_json_file(
    tmp_path: Path,
) -> None:
    application = create_app()
    exporter = OpenApiJsonExporter()

    destination = (
        tmp_path
        / "nested"
        / "openapi.json"
    )

    written_path = exporter.write(
        application,
        destination,
    )

    assert written_path == destination
    assert destination.exists()

    file_content = destination.read_text(
        encoding="utf-8"
    )

    assert file_content.endswith("\n")

    decoded_payload = json.loads(
        file_content
    )

    assert (
        decoded_payload["info"]["title"]
        == "Pro Vision Engine API"
    )


def test_exporter_rejects_invalid_application() -> None:
    exporter = OpenApiJsonExporter()

    with pytest.raises(
        TypeError,
        match="requires a FastAPI application",
    ):
        exporter.to_dict(
            object()  # type: ignore[arg-type]
        )