"""Tests for versioned practical analysis-result JSON export."""

import json

import pytest

from src.exporters.coupon_analysis_result_json_exporter import (
    CouponAnalysisResultJsonExporter,
)
from tests.coupon_analysis_run_helpers import (
    FIXED_ANALYZED_AT,
    create_analysis_run,
)


def create_payload():
    """Create the standard exported dictionary."""

    return CouponAnalysisResultJsonExporter().to_dict(
        create_analysis_run()
    )


def test_exporter_uses_result_schema_version() -> None:
    payload = create_payload()

    assert payload["schema_version"] == (
        "p13-analysis-result-v1"
    )


def test_exporter_serializes_analysis_metadata() -> None:
    analysis = create_payload()["analysis"]

    assert analysis["analyzed_at"] == (
        FIXED_ANALYZED_AT.isoformat()
    )
    assert analysis["input_schema_version"] == (
        "p13-analysis-input-v1"
    )
    assert analysis["source_name"].endswith(
        "topptipset-analysis-input.json"
    )


def test_exporter_serializes_coupon_summary() -> None:
    coupon = create_payload()["coupon"]

    assert coupon["id"] == "TT-EXEMPEL-2026-08-01"
    assert coupon["game_type"] == "topptipset"
    assert coupon["game_type_display"] == "Topptipset"
    assert coupon["match_count"] == 8
    assert coupon["base_row_count"] > 0


def test_exporter_serializes_frame_metadata() -> None:
    run = create_analysis_run()
    frame = create_payload()["frame"]

    assert frame["pattern"] == run.recommendation_pattern
    assert frame["match_count"] == 8
    assert frame["row_count"] == run.base_row_count
    assert frame["first_row"] == run.base_system.first_row.symbols
    assert frame["last_row"] == run.base_system.last_row.symbols


def test_exporter_serializes_all_matches_in_order() -> None:
    matches = create_payload()["matches"]

    assert len(matches) == 8
    assert [
        match["number"]
        for match in matches
    ] == list(
        range(
            1,
            9,
        )
    )


def test_exporter_serializes_match_identity() -> None:
    first = create_payload()["matches"][0]

    assert first["reference"] == "TT-2026-08-01-01"
    assert first["home_team"] == "Exempel Hemma 1"
    assert first["away_team"] == "Exempel Borta 1"


def test_exporter_serializes_decimal_values_as_strings() -> None:
    first = create_payload()["matches"][0]

    assert isinstance(
        first["projected_xg"]["home"],
        str,
    )
    assert isinstance(
        first["combined_probabilities"]["1"],
        str,
    )
    assert isinstance(
        first["scoreline"]["probability"],
        str,
    )


def test_exporter_serializes_recommendation_contract() -> None:
    recommendation = (
        create_payload()["matches"][0]["recommendation"]
    )

    assert recommendation["primary_outcome"] in {
        "1",
        "X",
        "2",
    }
    assert recommendation["symbols"]
    assert recommendation["outcomes"]
    assert recommendation["decision_type"] in {
        "spike",
        "single",
        "double",
        "triple",
    }


def test_exporter_serializes_risk_and_signals() -> None:
    first = create_payload()["matches"][0]

    assert isinstance(
        first["risk"]["score"],
        int,
    )
    assert isinstance(
        first["risk"]["factors"],
        list,
    )
    assert isinstance(
        first["signals"]["full_consensus"],
        bool,
    )
    assert isinstance(
        first["signals"]["requires_extended_review"],
        bool,
    )


def test_exporter_preserves_swedish_unicode() -> None:
    json_text = CouponAnalysisResultJsonExporter().to_json(
        create_analysis_run()
    )

    assert "Topptipset" in json_text
    assert "Turkos" not in json_text
    assert "Ã" not in json_text


def test_exporter_creates_valid_json() -> None:
    json_text = CouponAnalysisResultJsonExporter().to_json(
        create_analysis_run()
    )

    decoded = json.loads(
        json_text
    )

    assert decoded["coupon"]["match_count"] == 8


def test_exporter_supports_compact_json() -> None:
    json_text = CouponAnalysisResultJsonExporter().to_json(
        create_analysis_run(),
        indent=None,
    )

    assert "\n" not in json_text


def test_exporter_rejects_invalid_run() -> None:
    with pytest.raises(
        TypeError,
        match="CouponAnalysisRun",
    ):
        CouponAnalysisResultJsonExporter().to_dict(
            object()  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "indent",
    (
        True,
        "2",
    ),
)
def test_exporter_rejects_invalid_indent_type(
    indent: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="indent",
    ):
        CouponAnalysisResultJsonExporter().to_json(
            create_analysis_run(),
            indent=indent,  # type: ignore[arg-type]
        )


def test_exporter_rejects_negative_indent() -> None:
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        CouponAnalysisResultJsonExporter().to_json(
            create_analysis_run(),
            indent=-1,
        )