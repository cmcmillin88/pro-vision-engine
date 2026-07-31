"""JSON Schema exporter for practical coupon-analysis input."""

import json
from pathlib import Path
from typing import Any

from src.models.coupon_analysis_document import (
    CouponAnalysisDocument,
)


class CouponAnalysisJsonSchemaExporter:
    """Builds the stable JSON Schema for real-coupon input."""

    schema_version = CouponAnalysisDocument.CURRENT_SCHEMA_VERSION
    schema_id = (
        "https://projekt13.local/contracts/"
        "coupon-analysis-input.schema.json"
    )

    def to_dict(self) -> dict[str, Any]:
        """Return the complete JSON-compatible schema dictionary."""

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": self.schema_id,
            "title": "Projekt 13 Coupon Analysis Input",
            "description": (
                "Versioned input contract for manual or imported "
                "Topptipset, Stryktipset and Europatipset analysis."
            ),
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "coupon",
                "matches",
            ],
            "properties": {
                "schema_version": {
                    "const": self.schema_version,
                },
                "coupon": {
                    "$ref": "#/$defs/coupon",
                },
                "matches": {
                    "type": "array",
                    "items": {
                        "$ref": "#/$defs/match",
                    },
                },
            },
            "allOf": [
                {
                    "if": {
                        "properties": {
                            "coupon": {
                                "properties": {
                                    "game_type": {
                                        "const": "topptipset",
                                    },
                                },
                                "required": [
                                    "game_type",
                                ],
                            },
                        },
                    },
                    "then": {
                        "properties": {
                            "matches": {
                                "minItems": 8,
                                "maxItems": 8,
                            },
                        },
                    },
                },
                {
                    "if": {
                        "properties": {
                            "coupon": {
                                "properties": {
                                    "game_type": {
                                        "enum": [
                                            "stryktipset",
                                            "europatipset",
                                        ],
                                    },
                                },
                                "required": [
                                    "game_type",
                                ],
                            },
                        },
                    },
                    "then": {
                        "properties": {
                            "matches": {
                                "minItems": 13,
                                "maxItems": 13,
                            },
                        },
                    },
                },
            ],
            "$defs": {
                "coupon": self._coupon_schema(),
                "match": self._match_schema(),
                "performance": self._performance_schema(),
                "market": self._market_schema(),
                "market_snapshot": self._market_snapshot_schema(),
                "odds": self._distribution_schema(
                    minimum_exclusive=1,
                ),
                "public_percentages": self._distribution_schema(
                    minimum=0,
                    maximum=100,
                ),
            },
        }

    def to_json(
        self,
        *,
        indent: int | None = 2,
    ) -> str:
        """Return the schema as formatted UTF-8 JSON text."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=indent,
        )

    def write(
        self,
        path: str | Path,
    ) -> Path:
        """Write the schema as UTF-8 without a byte-order mark."""

        resolved_path = Path(
            path
        )
        resolved_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        resolved_path.write_text(
            f"{self.to_json()}\n",
            encoding="utf-8",
        )

        return resolved_path

    @staticmethod
    def _coupon_schema() -> dict[str, Any]:
        """Return coupon metadata schema."""

        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "game_type",
            ],
            "properties": {
                "id": {
                    "type": [
                        "string",
                        "null",
                    ],
                    "minLength": 1,
                },
                "game_type": {
                    "enum": [
                        "topptipset",
                        "stryktipset",
                        "europatipset",
                    ],
                },
            },
        }

    @staticmethod
    def _match_schema() -> dict[str, Any]:
        """Return one complete match-input schema."""

        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "number",
                "home_team",
                "away_team",
                "home_performances",
                "away_performances",
                "market",
            ],
            "properties": {
                "number": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 13,
                },
                "reference": {
                    "type": [
                        "string",
                        "null",
                    ],
                    "minLength": 1,
                },
                "home_team": {
                    "type": "string",
                    "minLength": 1,
                },
                "away_team": {
                    "type": "string",
                    "minLength": 1,
                },
                "home_performances": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "$ref": "#/$defs/performance",
                    },
                },
                "away_performances": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "$ref": "#/$defs/performance",
                    },
                },
                "market": {
                    "$ref": "#/$defs/market",
                },
            },
        }

    @staticmethod
    def _performance_schema() -> dict[str, Any]:
        """Return one team-performance schema."""

        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "opponent",
                "played_at",
                "venue",
                "goals_for",
                "goals_against",
                "xg_for",
                "xg_against",
                "shots_for",
                "shots_against",
                "shots_on_target_for",
                "shots_on_target_against",
            ],
            "properties": {
                "opponent": {
                    "type": "string",
                    "minLength": 1,
                },
                "played_at": {
                    "type": "string",
                    "format": "date-time",
                },
                "venue": {
                    "enum": [
                        "home",
                        "away",
                        "neutral",
                    ],
                },
                "goals_for": {
                    "type": "integer",
                    "minimum": 0,
                },
                "goals_against": {
                    "type": "integer",
                    "minimum": 0,
                },
                "xg_for": {
                    "type": [
                        "number",
                        "string",
                    ],
                },
                "xg_against": {
                    "type": [
                        "number",
                        "string",
                    ],
                },
                "shots_for": {
                    "type": "integer",
                    "minimum": 0,
                },
                "shots_against": {
                    "type": "integer",
                    "minimum": 0,
                },
                "shots_on_target_for": {
                    "type": "integer",
                    "minimum": 0,
                },
                "shots_on_target_against": {
                    "type": "integer",
                    "minimum": 0,
                },
                "possession_percentage": {
                    "type": [
                        "number",
                        "string",
                        "null",
                    ],
                },
                "competition": {
                    "type": [
                        "string",
                        "null",
                    ],
                    "minLength": 1,
                },
            },
        }

    @staticmethod
    def _market_schema() -> dict[str, Any]:
        """Return earlier/later market schema."""

        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "earlier",
                "later",
            ],
            "properties": {
                "earlier": {
                    "$ref": "#/$defs/market_snapshot",
                },
                "later": {
                    "$ref": "#/$defs/market_snapshot",
                },
            },
        }

    @staticmethod
    def _market_snapshot_schema() -> dict[str, Any]:
        """Return one time-stamped market snapshot schema."""

        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "captured_at",
                "source_name",
                "odds",
                "public_percentages",
            ],
            "properties": {
                "captured_at": {
                    "type": "string",
                    "format": "date-time",
                },
                "source_name": {
                    "type": "string",
                    "minLength": 1,
                },
                "odds": {
                    "$ref": "#/$defs/odds",
                },
                "public_percentages": {
                    "$ref": "#/$defs/public_percentages",
                },
            },
        }

    @staticmethod
    def _distribution_schema(
        *,
        minimum: int | None = None,
        maximum: int | None = None,
        minimum_exclusive: int | None = None,
    ) -> dict[str, Any]:
        """Return an exact 1-X-2 numeric distribution schema."""

        number_schema: dict[str, Any] = {
            "type": [
                "number",
                "string",
            ],
        }

        if minimum is not None:
            number_schema["minimum"] = minimum

        if maximum is not None:
            number_schema["maximum"] = maximum

        if minimum_exclusive is not None:
            number_schema["exclusiveMinimum"] = minimum_exclusive

        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "1",
                "X",
                "2",
            ],
            "properties": {
                symbol: dict(
                    number_schema
                )
                for symbol in (
                    "1",
                    "X",
                    "2",
                )
            },
        }