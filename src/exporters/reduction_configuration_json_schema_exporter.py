"""JSON Schema exporter for practical reduction configuration."""

import json
from copy import deepcopy
from typing import Any

from src.models.reduction_configuration_document import (
    ReductionConfigurationDocument,
)


class ReductionConfigurationJsonSchemaExporter:
    """Exports the strict p13-reduction-input-v1 JSON Schema."""

    schema_version = ReductionConfigurationDocument.CURRENT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return a defensive copy of the complete JSON Schema."""

        return deepcopy(
            self._schema()
        )

    def to_json(
        self,
        *,
        indent: int | None = 2,
    ) -> str:
        """Return UTF-8-safe formatted JSON Schema text."""

        if (
            indent is not None
            and (
                isinstance(indent, bool)
                or not isinstance(indent, int)
            )
        ):
            raise TypeError(
                "indent must be an integer or None."
            )

        if indent is not None and indent < 0:
            raise ValueError(
                "indent must not be negative."
            )

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=indent,
        )

    @classmethod
    def _schema(cls) -> dict[str, Any]:
        """Build the complete deterministic JSON Schema mapping."""

        numeric_value = {
            "oneOf": [
                {
                    "type": "number",
                },
                {
                    "type": "string",
                    "pattern": (
                        "^-?(?:0|[1-9][0-9]*)"
                        "(?:\\.[0-9]+)?$"
                    ),
                },
            ]
        }
        integer_range = {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "min",
                "max",
            ],
            "properties": {
                "min": {
                    "type": "integer",
                    "minimum": 0,
                },
                "max": {
                    "type": "integer",
                    "minimum": 0,
                },
            },
        }
        market_rule = {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "market_snapshot",
                "min",
                "max",
            ],
            "properties": {
                "market_snapshot": {
                    "$ref": "#/$defs/marketSnapshotSelection",
                },
                "min": {
                    "$ref": "#/$defs/numericValue",
                },
                "max": {
                    "$ref": "#/$defs/numericValue",
                },
            },
        }

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://project13.local/contracts/reduction-configuration.schema.json",
            "title": "Project 13 reduction configuration",
            "description": (
                "Strict configuration for color, 1X2, point, odds "
                "and transparent payout reduction."
            ),
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "target",
                "row_price",
                "conditions",
            ],
            "properties": {
                "schema_version": {
                    "const": cls.schema_version,
                },
                "target": {
                    "$ref": "#/$defs/target",
                },
                "row_price": {
                    "$ref": "#/$defs/numericValue",
                },
                "conditions": {
                    "$ref": "#/$defs/conditions",
                },
            },
            "$defs": {
                "numericValue": numeric_value,
                "outcome": {
                    "type": "string",
                    "enum": [
                        "1",
                        "X",
                        "2",
                    ],
                },
                "marketSnapshotSelection": {
                    "type": "string",
                    "enum": [
                        "earlier",
                        "later",
                    ],
                },
                "target": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "game_type",
                    ],
                    "properties": {
                        "coupon_id": {
                            "type": [
                                "string",
                                "null",
                            ],
                            "minLength": 1,
                        },
                        "game_type": {
                            "type": "string",
                            "enum": [
                                "topptipset",
                                "stryktipset",
                                "europatipset",
                            ],
                        },
                        "frame_pattern": {
                            "type": [
                                "string",
                                "null",
                            ],
                            "minLength": 1,
                        },
                    },
                },
                "cell": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "match",
                        "outcome",
                    ],
                    "properties": {
                        "match": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "outcome": {
                            "$ref": "#/$defs/outcome",
                        },
                    },
                },
                "colorRule": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "color",
                        "cells",
                        "min",
                        "max",
                    ],
                    "properties": {
                        "color": {
                            "type": "string",
                            "enum": [
                                "red",
                                "yellow",
                                "blue",
                                "pink",
                                "purple",
                                "green",
                            ],
                        },
                        "cells": {
                            "type": "array",
                            "minItems": 1,
                            "uniqueItems": True,
                            "items": {
                                "$ref": "#/$defs/cell",
                            },
                        },
                        "min": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "max": {
                            "type": "integer",
                            "minimum": 0,
                        },
                    },
                },
                "pointAssignment": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "match",
                        "outcome",
                        "points",
                    ],
                    "properties": {
                        "match": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "outcome": {
                            "$ref": "#/$defs/outcome",
                        },
                        "points": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 99,
                        },
                    },
                },
                "pointRule": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "assignments",
                        "min",
                        "max",
                    ],
                    "properties": {
                        "assignments": {
                            "type": "array",
                            "minItems": 1,
                            "uniqueItems": True,
                            "items": {
                                "$ref": "#/$defs/pointAssignment",
                            },
                        },
                        "min": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "max": {
                            "type": "integer",
                            "minimum": 0,
                        },
                    },
                },
                "integerRange": integer_range,
                "oneXTwoRule": {
                    "type": "object",
                    "additionalProperties": False,
                    "minProperties": 1,
                    "properties": {
                        "1": {
                            "$ref": "#/$defs/integerRange",
                        },
                        "X": {
                            "$ref": "#/$defs/integerRange",
                        },
                        "2": {
                            "$ref": "#/$defs/integerRange",
                        },
                    },
                },
                "marketRule": market_rule,
                "payoutRule": {
                    "description": (
                        "Transparent uppskattad utdelning med "
                        "versionerad Project 13-modell."
                    ),
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "market_snapshot",
                        "turnover",
                        "top_prize_pool",
                        "base_unit_stake",
                        "min",
                        "max",
                    ],
                    "properties": {
                        "market_snapshot": {
                            "$ref": "#/$defs/marketSnapshotSelection",
                        },
                        "turnover": {
                            "$ref": "#/$defs/numericValue",
                        },
                        "top_prize_pool": {
                            "$ref": "#/$defs/numericValue",
                        },
                        "base_unit_stake": {
                            "$ref": "#/$defs/numericValue",
                        },
                        "min": {
                            "$ref": "#/$defs/numericValue",
                        },
                        "max": {
                            "$ref": "#/$defs/numericValue",
                        },
                    },
                },
                "conditions": {
                    "type": "object",
                    "additionalProperties": False,
                    "minProperties": 1,
                    "properties": {
                        "colors": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 6,
                            "items": {
                                "$ref": "#/$defs/colorRule",
                            },
                        },
                        "one_x_two": {
                            "$ref": "#/$defs/oneXTwoRule",
                        },
                        "points": {
                            "$ref": "#/$defs/pointRule",
                        },
                        "odds": {
                            "$ref": "#/$defs/marketRule",
                        },
                        "payout": {
                            "$ref": "#/$defs/payoutRule",
                        },
                    },
                },
            },
        }