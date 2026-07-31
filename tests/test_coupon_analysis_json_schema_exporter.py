"""Tests for the practical coupon-analysis JSON Schema."""

import json

from src.exporters.coupon_analysis_json_schema_exporter import (
    CouponAnalysisJsonSchemaExporter,
)
from src.importer.coupon_analysis_json_importer import (
    CouponAnalysisJsonImporter,
)
from tests.analysis_input_helpers import (
    EXAMPLE_PATH,
    SCHEMA_PATH,
)


def test_schema_exposes_contract_version() -> None:
    exporter = CouponAnalysisJsonSchemaExporter()
    schema = exporter.to_dict()

    assert schema["properties"]["schema_version"]["const"] == (
        "p13-analysis-input-v1"
    )


def test_schema_uses_json_schema_2020_12() -> None:
    schema = CouponAnalysisJsonSchemaExporter().to_dict()

    assert schema["$schema"] == (
        "https://json-schema.org/draft/2020-12/schema"
    )
    assert schema["$id"].endswith(
        "coupon-analysis-input.schema.json"
    )


def test_schema_rejects_unknown_fields_at_every_level() -> None:
    schema = CouponAnalysisJsonSchemaExporter().to_dict()

    assert schema["additionalProperties"] is False
    assert schema["$defs"]["coupon"]["additionalProperties"] is False
    assert schema["$defs"]["match"]["additionalProperties"] is False
    assert schema["$defs"]["performance"]["additionalProperties"] is False
    assert schema["$defs"]["market_snapshot"]["additionalProperties"] is False


def test_schema_contains_topptipset_match_count_rule() -> None:
    schema = CouponAnalysisJsonSchemaExporter().to_dict()
    topptipset_then = schema["allOf"][0]["then"]

    assert topptipset_then["properties"]["matches"] == {
        "minItems": 8,
        "maxItems": 8,
    }


def test_schema_contains_thirteen_match_rule() -> None:
    schema = CouponAnalysisJsonSchemaExporter().to_dict()
    thirteen_then = schema["allOf"][1]["then"]

    assert thirteen_then["properties"]["matches"] == {
        "minItems": 13,
        "maxItems": 13,
    }


def test_schema_uses_official_1x2_keys() -> None:
    schema = CouponAnalysisJsonSchemaExporter().to_dict()

    assert schema["$defs"]["odds"]["required"] == [
        "1",
        "X",
        "2",
    ]


def test_schema_contains_timezone_capable_datetime_formats() -> None:
    schema = CouponAnalysisJsonSchemaExporter().to_dict()

    assert (
        schema["$defs"]["performance"]["properties"]["played_at"]["format"]
        == "date-time"
    )
    assert (
        schema["$defs"]["market_snapshot"]["properties"]["captured_at"]["format"]
        == "date-time"
    )


def test_static_schema_matches_exporter() -> None:
    stored_schema = json.loads(
        SCHEMA_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert stored_schema == (
        CouponAnalysisJsonSchemaExporter().to_dict()
    )


def test_exporter_to_json_preserves_unicode() -> None:
    json_text = CouponAnalysisJsonSchemaExporter().to_json()

    assert "Topptipset" in json_text
    assert json.loads(json_text)["title"] == (
        "Projekt 13 Coupon Analysis Input"
    )


def test_exporter_writes_schema_file(tmp_path) -> None:
    target = tmp_path / "contracts" / "schema.json"

    returned = CouponAnalysisJsonSchemaExporter().write(
        target
    )

    assert returned == target
    assert json.loads(target.read_text(encoding="utf-8")) == (
        CouponAnalysisJsonSchemaExporter().to_dict()
    )


def test_official_example_uses_current_contract() -> None:
    document = CouponAnalysisJsonImporter().from_file(
        EXAMPLE_PATH
    )

    assert document.schema_version == (
        CouponAnalysisJsonSchemaExporter.schema_version
    )


def test_contract_files_contain_no_mojibake() -> None:
    combined_text = (
        SCHEMA_PATH.read_text(encoding="utf-8")
        + EXAMPLE_PATH.read_text(encoding="utf-8")
    )

    assert "Ã" not in combined_text
    assert "Â" not in combined_text
    assert "â€" not in combined_text