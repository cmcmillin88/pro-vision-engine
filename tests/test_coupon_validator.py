"""Tests for the Pro Vision coupon validator."""

import pytest

from src.models.coupon import Coupon
from src.models.game_type import GameType
from src.models.match import Match
from src.validators.coupon_validator import (
    CouponValidationError,
    CouponValidator,
)


def create_match(match_number: int) -> Match:
    """Create a simple match for validator tests."""

    return Match(
        match_number=match_number,
        home_team=f"Home Team {match_number}",
        away_team=f"Away Team {match_number}",
    )


def create_coupon(
    game_type: GameType,
    match_count: int,
) -> Coupon:
    """Create a coupon with sequentially numbered matches."""

    coupon = Coupon(game_type=game_type)

    for match_number in range(1, match_count + 1):
        coupon.add_match(
            create_match(match_number)
        )

    return coupon


@pytest.mark.parametrize(
    ("game_type", "match_count"),
    [
        (GameType.TOPPTIPSET, 8),
        (GameType.STRYKTIPSET, 13),
        (GameType.EUROPATIPSET, 13),
    ],
)
def test_validator_accepts_complete_coupon(
    game_type: GameType,
    match_count: int,
) -> None:
    validator = CouponValidator()
    coupon = create_coupon(
        game_type,
        match_count,
    )

    result = validator.validate(coupon)

    assert result is None


def test_validator_rejects_unknown_game_type() -> None:
    validator = CouponValidator()
    coupon = Coupon(
        game_type=GameType.UNKNOWN,
    )

    with pytest.raises(
        CouponValidationError,
        match="game type must be specified",
    ):
        validator.validate(coupon)


def test_validator_rejects_empty_topptipset_coupon() -> None:
    validator = CouponValidator()
    coupon = Coupon(
        game_type=GameType.TOPPTIPSET,
    )

    with pytest.raises(
        CouponValidationError,
        match="requires exactly 8 matches",
    ):
        validator.validate(coupon)


def test_validator_rejects_wrong_match_count() -> None:
    validator = CouponValidator()
    coupon = create_coupon(
        GameType.TOPPTIPSET,
        7,
    )

    with pytest.raises(
        CouponValidationError,
        match="contains 7",
    ):
        validator.validate(coupon)


def test_validator_rejects_duplicate_match_numbers() -> None:
    validator = CouponValidator()
    coupon = create_coupon(
        GameType.TOPPTIPSET,
        8,
    )

    coupon.matches[-1] = create_match(1)

    with pytest.raises(
        CouponValidationError,
        match="must be unique",
    ):
        validator.validate(coupon)


def test_validator_rejects_incorrect_match_order() -> None:
    validator = CouponValidator()
    coupon = create_coupon(
        GameType.TOPPTIPSET,
        8,
    )

    coupon.matches[0], coupon.matches[1] = (
        coupon.matches[1],
        coupon.matches[0],
    )

    with pytest.raises(
        CouponValidationError,
        match="sequential and ordered",
    ):
        validator.validate(coupon)