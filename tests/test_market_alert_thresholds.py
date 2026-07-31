"""Tests for configurable market alert thresholds."""

from decimal import Decimal

import pytest

from src.models.market_alert_thresholds import (
    MarketAlertThresholds,
)


def test_thresholds_have_expected_defaults() -> None:
    thresholds = MarketAlertThresholds()

    assert (
        thresholds.odds_shortening_warning
        == Decimal("0.15")
    )
    assert (
        thresholds.public_surge_critical
        == Decimal("8.00")
    )
    assert (
        thresholds.contrarian_edge_warning
        == Decimal("3.00")
    )


def test_thresholds_normalize_numeric_values() -> None:
    thresholds = MarketAlertThresholds(
        odds_shortening_warning="0.20",  # type: ignore[arg-type]
        odds_shortening_critical=1,  # type: ignore[arg-type]
    )

    assert (
        thresholds.odds_shortening_warning
        == Decimal("0.20")
    )
    assert (
        thresholds.odds_shortening_critical
        == Decimal("1")
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "odds_shortening_warning",
        "public_surge_warning",
        "value_erosion_warning",
        "contrarian_public_drop",
    ],
)
def test_thresholds_reject_negative_values(
    field_name: str,
) -> None:
    values = {
        field_name: Decimal("-0.01"),
    }

    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        MarketAlertThresholds(
            **values
        )


@pytest.mark.parametrize(
    ("warning_field", "critical_field"),
    [
        (
            "odds_shortening_warning",
            "odds_shortening_critical",
        ),
        (
            "market_probability_gain_warning",
            "market_probability_gain_critical",
        ),
        (
            "public_surge_warning",
            "public_surge_critical",
        ),
        (
            "value_erosion_warning",
            "value_erosion_critical",
        ),
        (
            "contrarian_edge_warning",
            "contrarian_edge_critical",
        ),
    ],
)
def test_critical_threshold_cannot_be_below_warning(
    warning_field: str,
    critical_field: str,
) -> None:
    values = {
        warning_field: Decimal("5"),
        critical_field: Decimal("4"),
    }

    with pytest.raises(
        ValueError,
        match="greater than or equal",
    ):
        MarketAlertThresholds(
            **values
        )


def test_thresholds_reject_boolean_values() -> None:
    with pytest.raises(
        TypeError,
        match="must be numeric",
    ):
        MarketAlertThresholds(
            odds_shortening_warning=True,  # type: ignore[arg-type]
        )


def test_thresholds_reject_non_finite_values() -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        MarketAlertThresholds(
            public_surge_warning=Decimal("NaN"),
        )