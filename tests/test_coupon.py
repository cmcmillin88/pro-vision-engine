"""Tests for the Pro Vision coupon model."""

from src.models.coupon import Coupon
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.models.match import Match


def create_match(
    match_number: int,
    home_team: str,
    away_team: str,
) -> Match:
    """Create a match for coupon tests."""

    return Match(
        match_number=match_number,
        home_team=home_team,
        away_team=away_team,
    )


def test_coupon_can_add_match() -> None:
    coupon = Coupon()

    coupon.add_match(
        create_match(1, "Arsenal", "Chelsea")
    )

    assert len(coupon) == 1
    assert coupon.matches[0].home_team == "Arsenal"
    assert coupon.matches[0].away_team == "Chelsea"


def test_coupon_can_hold_multiple_matches() -> None:
    coupon = Coupon()

    coupon.add_match(
        create_match(1, "Arsenal", "Chelsea")
    )
    coupon.add_match(
        create_match(2, "Liverpool", "Everton")
    )

    assert len(coupon) == 2
    assert coupon.matches[0].match_number == 1
    assert coupon.matches[1].match_number == 2


def test_coupon_has_safe_default_metadata() -> None:
    coupon = Coupon()

    assert coupon.game_type is GameType.UNKNOWN
    assert coupon.source is ImportSource.MANUAL
    assert coupon.coupon_id is None
    assert coupon.deadline is None
    assert coupon.imported_at is not None


def test_topptipset_coupon_expects_eight_matches() -> None:
    coupon = Coupon(
        game_type=GameType.TOPPTIPSET,
    )

    assert coupon.expected_match_count == 8


def test_coupon_string_contains_metadata_and_matches() -> None:
    coupon = Coupon(
        game_type=GameType.EUROPATIPSET,
        source=ImportSource.SVENSKA_SPEL,
        coupon_id="ET-12345",
    )

    coupon.add_match(
        create_match(1, "Arsenal", "Chelsea")
    )

    coupon_text = str(coupon)

    assert "Europatipset" in coupon_text
    assert "Svenska Spel" in coupon_text
    assert "ET-12345" in coupon_text
    assert "Arsenal" in coupon_text
    assert "Chelsea" in coupon_text
    assert "Total matches: 1" in coupon_text