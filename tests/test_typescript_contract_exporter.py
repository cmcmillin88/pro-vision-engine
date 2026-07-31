"""Tests for the TypeScript contract exporter."""

from pathlib import Path

import pytest

from src.exporters.typescript_contract_exporter import (
    TypeScriptContractError,
    TypeScriptContractExporter,
)


def create_openapi_document() -> dict[str, object]:
    """Create a representative OpenAPI test document."""

    return {
        "components": {
            "schemas": {
                "CouponMetadataResponse": {
                    "type": "object",
                    "properties": {
                        "deadline": {
                            "anyOf": [
                                {
                                    "format": "date-time",
                                    "type": "string",
                                },
                                {
                                    "type": "null",
                                },
                            ]
                        },
                        "expected_match_count": {
                            "anyOf": [
                                {
                                    "type": "integer",
                                },
                                {
                                    "type": "null",
                                },
                            ]
                        },
                        "id": {
                            "anyOf": [
                                {
                                    "type": "string",
                                },
                                {
                                    "type": "null",
                                },
                            ]
                        },
                    },
                    "required": [
                        "id",
                        "deadline",
                    ],
                },
                "CouponResponse": {
                    "type": "object",
                    "properties": {
                        "coupon": {
                            "$ref": (
                                "#/components/schemas/"
                                "CouponMetadataResponse"
                            )
                        },
                        "matches": {
                            "type": "array",
                            "items": {
                                "$ref": (
                                    "#/components/schemas/"
                                    "MatchResponse"
                                )
                            },
                        },
                    },
                    "required": [
                        "coupon",
                        "matches",
                    ],
                },
                "MatchResponse": {
                    "type": "object",
                    "properties": {
                        "competition": {
                            "anyOf": [
                                {
                                    "type": "string",
                                },
                                {
                                    "type": "null",
                                },
                            ]
                        },
                        "number": {
                            "type": "integer",
                        },
                    },
                    "required": [
                        "competition",
                        "number",
                    ],
                },
                "ValidationError": {
                    "type": "object",
                    "properties": {
                        "ctx": {
                            "type": "object",
                        },
                        "input": {
                            "title": "Input",
                        },
                    },
                },
            }
        }
    }


def test_types_include_expected_interfaces() -> None:
    exporter = TypeScriptContractExporter()

    typescript = exporter.types_to_string(
        create_openapi_document()
    )

    assert (
        "export interface CouponResponse"
        in typescript
    )
    assert (
        "export interface MatchResponse"
        in typescript
    )


def test_types_map_nullable_and_optional_fields() -> None:
    exporter = TypeScriptContractExporter()

    typescript = exporter.types_to_string(
        create_openapi_document()
    )

    assert (
        "deadline: string | null;"
        in typescript
    )
    assert (
        "id: string | null;"
        in typescript
    )
    assert (
        "expected_match_count?: "
        "number | null;"
        in typescript
    )


def test_types_map_references_and_arrays() -> None:
    exporter = TypeScriptContractExporter()

    typescript = exporter.types_to_string(
        create_openapi_document()
    )

    assert (
        "coupon: CouponMetadataResponse;"
        in typescript
    )
    assert (
        "matches: Array<MatchResponse>;"
        in typescript
    )


def test_types_use_unknown_for_untyped_fields() -> None:
    exporter = TypeScriptContractExporter()

    typescript = exporter.types_to_string(
        create_openapi_document()
    )

    assert (
        "ctx?: Record<string, unknown>;"
        in typescript
    )
    assert (
        "input?: unknown;"
        in typescript
    )


def test_types_are_deterministic() -> None:
    exporter = TypeScriptContractExporter()
    document = create_openapi_document()

    first_result = exporter.types_to_string(
        document
    )
    second_result = exporter.types_to_string(
        document
    )

    assert first_result == second_result


def test_client_contains_typed_endpoints() -> None:
    exporter = TypeScriptContractExporter()

    client = exporter.client_to_string()

    assert (
        "getHealth(): Promise<HealthResponse>"
        in client
    )
    assert (
        "listCoupons(): "
        "Promise<CouponListResponse>"
        in client
    )
    assert (
        "getCoupon(gameType: string): "
        "Promise<CouponResponse>"
        in client
    )
    assert (
        "encodeURIComponent(gameType)"
        in client
    )
    assert (
        "class ProVisionApiError"
        in client
    )


def test_exporter_writes_complete_contract(
    tmp_path: Path,
) -> None:
    exporter = TypeScriptContractExporter()

    written_paths = exporter.write(
        create_openapi_document(),
        tmp_path / "typescript",
    )

    assert [
        path.name
        for path in written_paths
    ] == [
        "api-types.ts",
        "api-client.ts",
        "index.ts",
    ]

    for path in written_paths:
        assert path.exists()
        assert path.read_text(
            encoding="utf-8"
        ).endswith("\n")


def test_exporter_rejects_missing_component_schemas() -> None:
    exporter = TypeScriptContractExporter()

    with pytest.raises(
        TypeScriptContractError,
        match="missing components.schemas",
    ):
        exporter.types_to_string(
            {
                "openapi": "3.1.0",
            }
        )