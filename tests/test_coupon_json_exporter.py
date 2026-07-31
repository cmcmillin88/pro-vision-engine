"""Tests for the coupon JSON exporter."""

import json
from datetime import datetime, timezone

from src.exporters.coupon_json_exporter import (
    CouponJsonExporter,
)
from src.models.coupon import Coupon
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.models.match import Match


def create_coupon() -> Coupon:
    """Create a complete coupon for exporter tests."""

    coupon = Coupon(
        game_type=GameType.TOPPTIPSET,
        source=ImportSource.SVENSKA_SPEL,
        coupon_id="TT-EXPORT-001",
        deadline=datetime(
            2026,
            8,
            1,
            15,
            0,
            tzinfo=timezone.utc,
        ),
        imported_at=datetime(
            2026,
            7,
            31,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    coupon.add_match(
        Match(
            match_number=1,
            home_team="Malmö FF",
            away_team="AIK",
            competition="Allsvenskan",
            kickoff=datetime(
                2026,
                8,
                1,
                16,
                0,
                tzinfo=timezone.utc,
            ),
            status="NEW",
        )
    )

    return coupon


def test_exporter_creates_versioned_payload() -> None:
    exporter = CouponJsonExporter()
    payload = exporter.to_dict(
        create_coupon()
    )

    assert payload["schema_version"] == "1.0"
    assert "coupon" in payload
    assert "matches" in payload


def test_exporter_serializes_coupon_metadata() -> None:
    exporter = CouponJsonExporter()
    payload = exporter.to_dict(
        create_coupon()
    )

    coupon_data = payload["coupon"]

    assert coupon_data["id"] == "TT-EXPORT-001"
    assert coupon_data["game_type"] == "topptipset"
    assert coupon_data["game_type_display"] == "Topptipset"
    assert coupon_data["source"] == "svenska_spel"
    assert coupon_data["source_display"] == "Svenska Spel"
    assert coupon_data["match_count"] == 1
    assert coupon_data["expected_match_count"] == 8


def test_exporter_serializes_match_data() -> None:
    exporter = CouponJsonExporter()
    payload = exporter.to_dict(
        create_coupon()
    )

    match_data = payload["matches"][0]

    assert match_data["number"] == 1
    assert match_data["home_team"] == "Malmö FF"
    assert match_data["away_team"] == "AIK"
    assert match_data["competition"] == "Allsvenskan"
    assert match_data["status"] == "NEW"


def test_exporter_serializes_datetimes_as_iso_strings() -> None:
    exporter = CouponJsonExporter()
    payload = exporter.to_dict(
        create_coupon()
    )

    coupon_data = payload["coupon"]
    match_data = payload["matches"][0]

    assert coupon_data["deadline"] == (
        "2026-08-01T15:00:00+00:00"
    )
    assert coupon_data["imported_at"] == (
        "2026-07-31T12:00:00+00:00"
    )
    assert match_data["kickoff"] == (
        "2026-08-01T16:00:00+00:00"
    )


def test_exporter_preserves_unicode_in_json() -> None:
    exporter = CouponJsonExporter()

    json_text = exporter.to_json(
        create_coupon()
    )

    decoded_payload = json.loads(json_text)

    assert "Malmö FF" in json_text
    assert (
        decoded_payload["matches"][0]["home_team"]
        == "Malmö FF"
    )


def test_exporter_serializes_missing_values_as_null() -> None:
    coupon = Coupon(
        game_type=GameType.UNKNOWN,
        source=ImportSource.MANUAL,
    )

    coupon.add_match(
        Match(
            match_number=1,
            home_team="Home Team",
            away_team="Away Team",
        )
    )

    exporter = CouponJsonExporter()
    payload = exporter.to_dict(coupon)

    coupon_data = payload["coupon"]
    match_data = payload["matches"][0]

    assert coupon_data["id"] is None
    assert coupon_data["deadline"] is None
    assert coupon_data["expected_match_count"] is None
    assert match_data["competition"] is None
    assert match_data["kickoff"] is None