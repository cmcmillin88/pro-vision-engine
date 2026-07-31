"""Tests for statistical-market comparison thresholds."""

from decimal import Decimal

import pytest

from src.models.statistical_market_comparison_thresholds import (
    StatisticalMarketComparisonThresholds,
)


def test_thresholds_have_expected_defaults() -> None:
    thresholds = StatisticalMarketComparisonThresholds()

    assert (
        thresholds.agreement_margin
        == Decimal("3.00")
    )
    assert (
        thresholds.disagreement_warning
        == Decimal("5.00")
    )
    assert (
        thresholds.disagreement_strong
        == Decimal("10.00")
    )
    assert (
        thresholds.model_value_threshold
        == Decimal("3.00")
    )
    assert (
        thresholds.strong_model_value_threshold
        == Decimal("6.00")
    )


def test_thresholds_normalize_numeric_values() -> None:
    thresholds = StatisticalMarketComparisonThresholds(
        agreement_margin="2.00",  # type: ignore[arg-type]
        disagreement_warning=4,  # type: ignore[arg-type]
        disagreement_strong=8.5,  # type: ignore[arg-type]
        model_value_threshold="2.5",  # type: ignore[arg-type]
        strong_model_value_threshold=5,  # type: ignore[arg-type]
    )

    assert thresholds.agreement_margin == Decimal("2.00")
    assert thresholds.disagreement_warning == Decimal("4")
    assert thresholds.disagreement_strong == Decimal("8.5")
    assert (
        thresholds.model_value_threshold
        == Decimal("2.5")
    )
    assert (
        thresholds.strong_model_value_threshold
        == Decimal("5")
    )


def test_thresholds_reject_negative_values() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        StatisticalMarketComparisonThresholds(
            agreement_margin=Decimal("-0.01")
        )


def test_comparison_thresholds_must_be_ordered() -> None:
    with pytest.raises(
        ValueError,
        match="must be ordered",
    ):
        StatisticalMarketComparisonThresholds(
            agreement_margin=Decimal("5"),
            disagreement_warning=Decimal("5"),
            disagreement_strong=Decimal("10"),
        )


def test_model_value_thresholds_must_be_ordered() -> None:
    with pytest.raises(
        ValueError,
        match="Model-value thresholds",
    ):
        StatisticalMarketComparisonThresholds(
            model_value_threshold=Decimal("6"),
            strong_model_value_threshold=Decimal("6"),
        )


def test_thresholds_reject_non_finite_values() -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        StatisticalMarketComparisonThresholds(
            disagreement_strong=Decimal("NaN")
        )


def test_thresholds_reject_boolean_values() -> None:
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        StatisticalMarketComparisonThresholds(
            agreement_margin=True,  # type: ignore[arg-type]
        )