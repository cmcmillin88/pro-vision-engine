"""Tests for strict practical coupon-analysis JSON import."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from src.importer.coupon_analysis_json_importer import (
    CouponAnalysisJsonImporter,
)
from src.models.game_type import GameType
from src.models.team_match_performance import MatchVenue
from tests.analysis_input_helpers import (
    EXAMPLE_PATH,
    load_example_payload,
)


def import_payload(payload=None):
    """Import a supplied or standard mutable payload."""

    return CouponAnalysisJsonImporter().from_dict(
        payload
        if payload is not None
        else load_example_payload(),
        source_name="Testkälla",
    )


def test_importer_loads_official_example_file() -> None:
    document = CouponAnalysisJsonImporter().from_file(
        EXAMPLE_PATH
    )

    assert document.game_type is GameType.TOPPTIPSET
    assert document.match_count == 8
    assert document.source_name == str(EXAMPLE_PATH)


def test_importer_loads_json_text() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"]["earlier"][
        "captured_at"
    ] = "2026-07-30T16:00:00Z"

    document = CouponAnalysisJsonImporter().from_json(
        json.dumps(payload),
        source_name="JSON-text",
    )

    assert (
        document.matches[0]
        .earlier_market_snapshot
        .captured_at
        .utcoffset()
        .total_seconds()
        == 0
    )


def test_importer_creates_complete_domain_models() -> None:
    document = import_payload()
    first = document.matches[0]

    assert first.home_team_name == "Exempel Hemma 1"
    assert first.away_team_name == "Exempel Borta 1"
    assert first.match_reference == "TT-2026-08-01-01"
    assert first.home_performances[0].venue is MatchVenue.HOME
    assert first.away_performances[0].venue is MatchVenue.AWAY


def test_importer_injects_parent_team_name_into_performance() -> None:
    first = import_payload().matches[0]

    assert (
        first.home_performances[0].team_name
        == first.home_team_name
    )
    assert (
        first.away_performances[0].team_name
        == first.away_team_name
    )


def test_importer_preserves_decimal_precision() -> None:
    first = import_payload().matches[0]

    assert (
        first.home_performances[0].expected_goals_for
        == Decimal("1.70")
    )
    assert (
        first.later_market_snapshot.odds.home
        == Decimal("2.00")
    )


def test_importer_supports_omitted_optional_fields() -> None:
    payload = load_example_payload()
    payload["coupon"].pop("id")
    first = payload["matches"][0]
    first.pop("reference")
    performance = first["home_performances"][0]
    performance.pop("possession_percentage")
    performance.pop("competition")

    document = import_payload(payload)

    assert document.coupon_id is None
    assert document.matches[0].match_reference is None
    assert (
        document.matches[0]
        .home_performances[0]
        .possession_percentage
        is None
    )


def test_importer_rejects_unknown_top_level_field() -> None:
    payload = load_example_payload()
    payload["unexpected"] = True

    with pytest.raises(
        ValueError,
        match=r"\$: unknown field",
    ):
        import_payload(payload)


def test_importer_rejects_missing_top_level_field() -> None:
    payload = load_example_payload()
    payload.pop("matches")

    with pytest.raises(
        ValueError,
        match="missing required field.*matches",
    ):
        import_payload(payload)


def test_importer_rejects_unsupported_schema_version() -> None:
    payload = load_example_payload()
    payload["schema_version"] = "p13-analysis-input-v2"

    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        import_payload(payload)


def test_importer_rejects_invalid_game_type() -> None:
    payload = load_example_payload()
    payload["coupon"]["game_type"] = "bomben"

    with pytest.raises(
        ValueError,
        match="topptipset",
    ):
        import_payload(payload)


def test_importer_rejects_unknown_game_type() -> None:
    payload = load_example_payload()
    payload["coupon"]["game_type"] = "unknown"

    with pytest.raises(
        ValueError,
        match="not a supported",
    ):
        import_payload(payload)


def test_importer_rejects_unknown_coupon_field() -> None:
    payload = load_example_payload()
    payload["coupon"]["deadline"] = "2026-08-01T15:00:00+02:00"

    with pytest.raises(
        ValueError,
        match="deadline",
    ):
        import_payload(payload)


def test_importer_rejects_wrong_match_count() -> None:
    payload = load_example_payload()
    payload["matches"].pop()

    with pytest.raises(
        ValueError,
        match="requires exactly 8",
    ):
        import_payload(payload)


def test_importer_rejects_unordered_match_numbers() -> None:
    payload = load_example_payload()
    payload["matches"][0]["number"] = 2

    with pytest.raises(
        ValueError,
        match="strict coupon order",
    ):
        import_payload(payload)


def test_importer_rejects_duplicate_references() -> None:
    payload = load_example_payload()
    payload["matches"][1]["reference"] = (
        payload["matches"][0]["reference"]
    )

    with pytest.raises(
        ValueError,
        match="references",
    ):
        import_payload(payload)


def test_importer_rejects_unknown_match_field() -> None:
    payload = load_example_payload()
    payload["matches"][0]["kickoff"] = "2026-08-01T18:00:00+02:00"

    with pytest.raises(
        ValueError,
        match="kickoff",
    ):
        import_payload(payload)


def test_importer_rejects_missing_match_field() -> None:
    payload = load_example_payload()
    payload["matches"][0].pop("home_team")

    with pytest.raises(
        ValueError,
        match="home_team",
    ):
        import_payload(payload)


def test_importer_rejects_same_home_and_away_team() -> None:
    payload = load_example_payload()
    payload["matches"][0]["away_team"] = (
        payload["matches"][0]["home_team"]
    )

    with pytest.raises(
        ValueError,
        match="different",
    ):
        import_payload(payload)


def test_importer_rejects_empty_performance_history() -> None:
    payload = load_example_payload()
    payload["matches"][0]["home_performances"] = []

    with pytest.raises(
        ValueError,
        match="at least one performance",
    ):
        import_payload(payload)


def test_importer_rejects_invalid_venue() -> None:
    payload = load_example_payload()
    payload["matches"][0]["home_performances"][0][
        "venue"
    ] = "stadium"

    with pytest.raises(
        ValueError,
        match="home, away, neutral",
    ):
        import_payload(payload)


def test_importer_rejects_unknown_performance_field() -> None:
    payload = load_example_payload()
    payload["matches"][0]["home_performances"][0][
        "xg_total"
    ] = 2.5

    with pytest.raises(
        ValueError,
        match="xg_total",
    ):
        import_payload(payload)


def test_importer_rejects_missing_performance_field() -> None:
    payload = load_example_payload()
    payload["matches"][0]["home_performances"][0].pop(
        "xg_for"
    )

    with pytest.raises(
        ValueError,
        match="xg_for",
    ):
        import_payload(payload)


def test_importer_rejects_naive_performance_datetime() -> None:
    payload = load_example_payload()
    payload["matches"][0]["home_performances"][0][
        "played_at"
    ] = "2026-07-19T18:00:00"

    with pytest.raises(
        ValueError,
        match="timezone",
    ):
        import_payload(payload)


def test_importer_rejects_shots_on_target_above_shots() -> None:
    payload = load_example_payload()
    payload["matches"][0]["home_performances"][0][
        "shots_on_target_for"
    ] = 14

    with pytest.raises(ValueError):
        import_payload(payload)


def test_importer_rejects_earlier_snapshot_after_later() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"]["earlier"][
        "captured_at"
    ] = "2026-08-01T18:00:00+02:00"

    with pytest.raises(
        ValueError,
        match="earlier snapshot",
    ):
        import_payload(payload)


def test_importer_rejects_unknown_market_field() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"]["current"] = {}

    with pytest.raises(
        ValueError,
        match="current",
    ):
        import_payload(payload)


def test_importer_rejects_missing_market_snapshot() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"].pop("earlier")

    with pytest.raises(
        ValueError,
        match="earlier",
    ):
        import_payload(payload)


def test_importer_rejects_unknown_snapshot_field() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"]["earlier"][
        "bookmaker"
    ] = "Test"

    with pytest.raises(
        ValueError,
        match="bookmaker",
    ):
        import_payload(payload)


def test_importer_rejects_missing_snapshot_field() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"]["earlier"].pop(
        "source_name"
    )

    with pytest.raises(
        ValueError,
        match="source_name",
    ):
        import_payload(payload)


def test_importer_rejects_unknown_distribution_field() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"]["earlier"]["odds"][
        "home"
    ] = 2.1

    with pytest.raises(
        ValueError,
        match="home",
    ):
        import_payload(payload)


def test_importer_rejects_missing_distribution_field() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"]["earlier"]["odds"].pop(
        "X"
    )

    with pytest.raises(
        ValueError,
        match="X",
    ):
        import_payload(payload)


def test_importer_rejects_invalid_numeric_string() -> None:
    payload = load_example_payload()
    payload["matches"][0]["home_performances"][0][
        "xg_for"
    ] = "många"

    with pytest.raises(
        ValueError,
        match="valid numeric",
    ):
        import_payload(payload)


def test_importer_rejects_non_finite_numeric_value() -> None:
    payload = load_example_payload()
    payload["matches"][0]["home_performances"][0][
        "xg_for"
    ] = float("nan")

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        import_payload(payload)


def test_importer_rejects_invalid_odds() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"]["earlier"]["odds"][
        "1"
    ] = 1

    with pytest.raises(ValueError):
        import_payload(payload)


def test_importer_rejects_invalid_public_total() -> None:
    payload = load_example_payload()
    payload["matches"][0]["market"]["earlier"][
        "public_percentages"
    ] = {
        "1": 20,
        "X": 20,
        "2": 20,
    }

    with pytest.raises(ValueError):
        import_payload(payload)


def test_importer_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        CouponAnalysisJsonImporter().from_file(
            tmp_path / "missing.json"
        )


def test_importer_rejects_empty_json_text() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        CouponAnalysisJsonImporter().from_json(
            "   "
        )


def test_importer_rejects_malformed_json() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid coupon-analysis JSON",
    ):
        CouponAnalysisJsonImporter().from_json(
            "{bad json}"
        )


def test_importer_rejects_non_string_json_text() -> None:
    with pytest.raises(
        TypeError,
        match="json_text",
    ):
        CouponAnalysisJsonImporter().from_json(
            {}  # type: ignore[arg-type]
        )


def test_importer_rejects_non_mapping_payload() -> None:
    with pytest.raises(
        TypeError,
        match="expected an object",
    ):
        CouponAnalysisJsonImporter().from_dict(
            []  # type: ignore[arg-type]
        )


def test_importer_rejects_string_instead_of_match_array() -> None:
    payload = load_example_payload()
    payload["matches"] = "not-an-array"

    with pytest.raises(
        TypeError,
        match="expected an array",
    ):
        import_payload(payload)