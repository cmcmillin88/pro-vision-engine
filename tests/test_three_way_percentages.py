"""Tests for three-way percentage distributions."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from src.models.outcome import Outcome
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)


def test_percentages_are_normalized_and_totalled() -> None:
    percentages = ThreeWayPercentages(
        home="50",  # type: ignore[arg-type]
        draw=30,  # type: ignore[arg-type]
        away=20.0,  # type: ignore[arg-type]
    )

    assert percentages.home == Decimal("50")
    assert percentages.draw == Decimal("30")
    assert percentages.away == Decimal("20.0")
    assert percentages.total == Decimal("100.0")


@pytest.mark.parametrize(
    ("outcome", "expected_percentage"),
    [
        (Outcome.HOME, Decimal("50")),
        (Outcome.DRAW, Decimal("30")),
        (Outcome.AWAY, Decimal("20")),
    ],
)
def test_percentages_can_be_read_by_outcome(
    outcome: Outcome,
    expected_percentage: Decimal,
) -> None:
    percentages = ThreeWayPercentages(
        home=Decimal("50"),
        draw=Decimal("30"),
        away=Decimal("20"),
    )

    assert (
        percentages.for_outcome(outcome)
        == expected_percentage
    )


def test_percentages_allow_normal_rounding_difference() -> None:
    percentages = ThreeWayPercentages(
        home=Decimal("33.33"),
        draw=Decimal("33.33"),
        away=Decimal("33.33"),
    )

    assert percentages.total == Decimal("99.99")


@pytest.mark.parametrize(
    "invalid_value",
    [
        Decimal("-0.01"),
        Decimal("100.01"),
    ],
)
def test_percentages_reject_values_outside_range(
    invalid_value: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 100",
    ):
        ThreeWayPercentages(
            home=invalid_value,
            draw=Decimal("50"),
            away=Decimal("50"),
        )


@pytest.mark.parametrize(
    ("home", "draw", "away"),
    [
        (
            Decimal("20"),
            Decimal("20"),
            Decimal("20"),
        ),
        (
            Decimal("50"),
            Decimal("50"),
            Decimal("50"),
        ),
    ],
)
def test_percentages_reject_invalid_total(
    home: Decimal,
    draw: Decimal,
    away: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="must total between 99 and 101",
    ):
        ThreeWayPercentages(
            home=home,
            draw=draw,
            away=away,
        )


def test_percentages_are_immutable() -> None:
    percentages = ThreeWayPercentages(
        home=Decimal("50"),
        draw=Decimal("30"),
        away=Decimal("20"),
    )

    with pytest.raises(FrozenInstanceError):
        percentages.home = Decimal("60")  # type: ignore[misc]