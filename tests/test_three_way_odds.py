"""Tests for three-way decimal odds."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds


def test_odds_are_normalized_to_decimal() -> None:
    odds = ThreeWayOdds(
        home="2.10",  # type: ignore[arg-type]
        draw=3.4,  # type: ignore[arg-type]
        away=4,  # type: ignore[arg-type]
    )

    assert odds.home == Decimal("2.10")
    assert odds.draw == Decimal("3.4")
    assert odds.away == Decimal("4")


@pytest.mark.parametrize(
    ("outcome", "expected_odds"),
    [
        (Outcome.HOME, Decimal("2.10")),
        (Outcome.DRAW, Decimal("3.40")),
        (Outcome.AWAY, Decimal("4.00")),
    ],
)
def test_odds_can_be_read_by_outcome(
    outcome: Outcome,
    expected_odds: Decimal,
) -> None:
    odds = ThreeWayOdds(
        home=Decimal("2.10"),
        draw=Decimal("3.40"),
        away=Decimal("4.00"),
    )

    assert odds.for_outcome(outcome) == expected_odds


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("home", Decimal("1")),
        ("draw", Decimal("0.99")),
        ("away", Decimal("0")),
    ],
)
def test_odds_reject_values_not_above_one(
    field_name: str,
    invalid_value: Decimal,
) -> None:
    values = {
        "home": Decimal("2"),
        "draw": Decimal("3"),
        "away": Decimal("4"),
    }
    values[field_name] = invalid_value

    with pytest.raises(
        ValueError,
        match="must be greater than 1",
    ):
        ThreeWayOdds(**values)


def test_odds_reject_non_numeric_values() -> None:
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        ThreeWayOdds(
            home="invalid",  # type: ignore[arg-type]
            draw=Decimal("3"),
            away=Decimal("4"),
        )


def test_odds_are_immutable() -> None:
    odds = ThreeWayOdds(
        home=Decimal("2"),
        draw=Decimal("3"),
        away=Decimal("4"),
    )

    with pytest.raises(FrozenInstanceError):
        odds.home = Decimal("5")  # type: ignore[misc]