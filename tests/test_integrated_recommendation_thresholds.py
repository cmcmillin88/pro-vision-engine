"""Tests for integrated recommendation thresholds."""

from decimal import Decimal

import pytest

from src.models.integrated_recommendation_thresholds import (
    IntegratedRecommendationThresholds,
)


def test_thresholds_have_expected_defaults() -> None:
    thresholds = IntegratedRecommendationThresholds()

    assert (
        thresholds.statistical_weight
        == Decimal("0.60")
    )
    assert (
        thresholds.market_weight
        == Decimal("0.40")
    )
    assert (
        thresholds.confident_single_probability
        == Decimal("55.00")
    )
    assert (
        thresholds.confident_single_margin
        == Decimal("12.00")
    )
    assert (
        thresholds.model_value_guard
        == Decimal("3.00")
    )
    assert (
        thresholds.strong_model_value_guard
        == Decimal("6.00")
    )


def test_thresholds_normalize_numeric_values() -> None:
    thresholds = IntegratedRecommendationThresholds(
        statistical_weight="0.70",  # type: ignore[arg-type]
        market_weight=0.30,  # type: ignore[arg-type]
        confident_single_probability=60,  # type: ignore[arg-type]
    )

    assert (
        thresholds.statistical_weight
        == Decimal("0.70")
    )
    assert (
        thresholds.market_weight
        == Decimal("0.3")
    )
    assert (
        thresholds.confident_single_probability
        == Decimal("60")
    )


def test_weights_must_total_exactly_one() -> None:
    with pytest.raises(
        ValueError,
        match="total exactly 1",
    ):
        IntegratedRecommendationThresholds(
            statistical_weight=Decimal("0.70"),
            market_weight=Decimal("0.40"),
        )


def test_weights_must_not_exceed_one() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 1",
    ):
        IntegratedRecommendationThresholds(
            statistical_weight=Decimal("1.10"),
            market_weight=Decimal("0.00"),
        )


def test_model_value_thresholds_must_be_ordered() -> None:
    with pytest.raises(
        ValueError,
        match="must be ordered",
    ):
        IntegratedRecommendationThresholds(
            model_value_guard=Decimal("6"),
            strong_model_value_guard=Decimal("6"),
        )


def test_risk_thresholds_must_be_ordered() -> None:
    with pytest.raises(
        ValueError,
        match="must be ordered",
    ):
        IntegratedRecommendationThresholds(
            medium_risk_score=5,
            high_risk_score=4,
            extreme_risk_score=9,
        )


def test_thresholds_reject_non_finite_values() -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        IntegratedRecommendationThresholds(
            confident_single_margin=Decimal("NaN")
        )