"""Tests for market classification thresholds."""

from decimal import Decimal

import pytest

from src.models.market_classification_thresholds import (
    MarketClassificationThresholds,
)


def test_thresholds_have_expected_defaults() -> None:
    thresholds = MarketClassificationThresholds()

    assert (
        thresholds.value_play_edge
        == Decimal("3.00")
    )
    assert (
        thresholds.public_trap_public_minimum
        == Decimal("50.00")
    )
    assert (
        thresholds.public_trap_negative_edge
        == Decimal("5.00")
    )


def test_thresholds_normalize_numeric_values() -> None:
    thresholds = MarketClassificationThresholds(
        value_play_edge="4.50",  # type: ignore[arg-type]
        public_trap_public_minimum=55,  # type: ignore[arg-type]
    )

    assert (
        thresholds.value_play_edge
        == Decimal("4.50")
    )
    assert (
        thresholds.public_trap_public_minimum
        == Decimal("55")
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "value_play_edge",
        "public_trap_public_minimum",
        "public_trap_negative_edge",
    ],
)
def test_thresholds_reject_negative_values(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        MarketClassificationThresholds(
            **{
                field_name: Decimal("-0.01"),
            }
        )


def test_public_trap_minimum_cannot_exceed_100() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 100",
    ):
        MarketClassificationThresholds(
            public_trap_public_minimum=(
                Decimal("100.01")
            )
        )


def test_thresholds_reject_boolean_values() -> None:
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        MarketClassificationThresholds(
            value_play_edge=True,  # type: ignore[arg-type]
        )


def test_thresholds_reject_non_finite_values() -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        MarketClassificationThresholds(
            public_trap_negative_edge=(
                Decimal("NaN")
            )
        )