"""Tests for the reduction-configuration JSON Schema exporter."""

import json

import pytest

from src.exporters.reduction_configuration_json_schema_exporter import (
    ReductionConfigurationJsonSchemaExporter,
)
from tests.reduction_configuration_helpers import (
    SCHEMA_PATH,
)


def test_schema_exporter_exposes_contract_version() -> None:
    assert (
        ReductionConfigurationJsonSchemaExporter.schema_version
        == "p13-reduction-input-v1"
    )


def test_schema_uses_json_schema_2020_12() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert schema["$schema"] == (
        "https://json-schema.org/draft/2020-12/schema"
    )


def test_schema_has_stable_identifier() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert schema["$id"].endswith(
        "/reduction-configuration.schema.json"
    )


def test_schema_requires_all_top_level_fields() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert schema["required"] == [
        "schema_version",
        "target",
        "row_price",
        "conditions",
    ]


def test_schema_rejects_unknown_top_level_fields() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert schema["additionalProperties"] is False


def test_schema_supports_all_game_types() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert schema["$defs"]["target"]["properties"][
        "game_type"
    ]["enum"] == [
        "topptipset",
        "stryktipset",
        "europatipset",
    ]


def test_schema_supports_all_reduction_colors() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert schema["$defs"]["colorRule"]["properties"][
        "color"
    ]["enum"] == [
        "red",
        "yellow",
        "blue",
        "pink",
        "purple",
        "green",
    ]


def test_schema_supports_official_outcomes() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert schema["$defs"]["outcome"]["enum"] == [
        "1",
        "X",
        "2",
    ]


def test_schema_supports_earlier_and_later_snapshots() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert schema["$defs"]["marketSnapshotSelection"][
        "enum"
    ] == [
        "earlier",
        "later",
    ]


def test_schema_contains_all_condition_groups() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert set(
        schema["$defs"]["conditions"]["properties"]
    ) == {
        "colors",
        "one_x_two",
        "points",
        "odds",
        "payout",
    }


def test_schema_requires_at_least_one_condition_group() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    assert schema["$defs"]["conditions"]["minProperties"] == 1


def test_schema_limits_point_values_to_99() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    points = schema["$defs"]["pointAssignment"][
        "properties"
    ]["points"]

    assert points["minimum"] == 1
    assert points["maximum"] == 99


def test_schema_supports_numeric_values_and_numeric_strings() -> None:
    schema = ReductionConfigurationJsonSchemaExporter().to_dict()

    numeric_types = schema["$defs"]["numericValue"]["oneOf"]

    assert numeric_types[0]["type"] == "number"
    assert numeric_types[1]["type"] == "string"
    assert "pattern" in numeric_types[1]


def test_schema_json_round_trips() -> None:
    exporter = ReductionConfigurationJsonSchemaExporter()

    assert json.loads(
        exporter.to_json()
    ) == exporter.to_dict()


def test_schema_returns_defensive_copy() -> None:
    exporter = ReductionConfigurationJsonSchemaExporter()
    first = exporter.to_dict()
    first["title"] = "Changed"

    assert exporter.to_dict()["title"] == (
        "Project 13 reduction configuration"
    )


def test_static_schema_matches_exporter() -> None:
    exported = ReductionConfigurationJsonSchemaExporter().to_json()
    stored = SCHEMA_PATH.read_text(
        encoding="utf-8"
    ).rstrip("\n")

    assert exported == stored


def test_schema_preserves_swedish_unicode() -> None:
    text = ReductionConfigurationJsonSchemaExporter().to_json()

    assert "utdelning" in text
    assert "\\u00f6" not in text


@pytest.mark.parametrize(
    "indent",
    (
        True,
        "2",
    ),
)
def test_schema_rejects_invalid_indent_type(
    indent: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="indent",
    ):
        ReductionConfigurationJsonSchemaExporter().to_json(
            indent=indent  # type: ignore[arg-type]
        )


def test_schema_rejects_negative_indent() -> None:
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        ReductionConfigurationJsonSchemaExporter().to_json(
            indent=-1
        )


def test_static_schema_contains_no_mojibake() -> None:
    text = SCHEMA_PATH.read_text(
        encoding="utf-8"
    )

    assert "Ã" not in text
    assert "Â" not in text
    assert "â€" not in text