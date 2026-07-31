"""Tests for market recommendation thresholds."""

from decimal import Decimal

import pytest

from src.models.market_recommendation_thresholds import (
    MarketRecommendationThresholds,
)


def test_thresholds_have_expected_defaults() -> None:
    thresholds = MarketRecommendationThresholds()

    assert (
        thresholds.confident_single_probability
        == Decimal("55.00")
    )
    assert (
        thresholds.weak_favorite_probability
        == Decimal("45.00")
    )
    assert thresholds.medium_risk_score == 3
    assert thresholds.high_risk_score == 6
    assert thresholds.extreme_risk_score == 9


def test_thresholds_normalize_numeric_values() -> None:
    thresholds = MarketRecommendationThresholds(
        confident_single_probability="60",  # type: ignore[arg-type]
        weak_favorite_probability=40,  # type: ignore[arg-type]
        single_negative_edge_limit=4.5,  # type: ignore[arg-type]
    )

    assert (
        thresholds.confident_single_probability
        == Decimal("60")
    )
    assert (
        thresholds.weak_favorite_probability
        == Decimal("40")
    )
    assert (
        thresholds.single_negative_edge_limit
        == Decimal("4.5")
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "confident_single_probability",
        "weak_favorite_probability",
        "single_negative_edge_limit",
    ],
)
def test_thresholds_reject_negative_decimal_values(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        MarketRecommendationThresholds(
            **{
                field_name: Decimal("-0.01"),
            }
        )


def test_probability_threshold_cannot_exceed_100() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 100",
    ):
        MarketRecommendationThresholds(
            confident_single_probability=(
                Decimal("100.01")
            )
        )


def test_risk_score_thresholds_must_be_ordered() -> None:
    with pytest.raises(
        ValueError,
        match="must be ordered",
    ):
        MarketRecommendationThresholds(
            medium_risk_score=6,
            high_risk_score=5,
            extreme_risk_score=9,
        )


def test_risk_score_thresholds_reject_boolean_values() -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        MarketRecommendationThresholds(
            medium_risk_score=True,  # type: ignore[arg-type]
        )


def test_thresholds_reject_non_finite_values() -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        MarketRecommendationThresholds(
            weak_favorite_probability=(
                Decimal("NaN")
            )
        )