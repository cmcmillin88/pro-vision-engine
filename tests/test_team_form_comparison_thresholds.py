"""Tests for team-form comparison thresholds."""

from decimal import Decimal

import pytest

from src.models.team_form_comparison_thresholds import (
    TeamFormComparisonThresholds,
)


def test_thresholds_have_expected_defaults() -> None:
    thresholds = TeamFormComparisonThresholds()

    assert (
        thresholds.balanced_xg_margin
        == Decimal("0.20")
    )
    assert (
        thresholds.clear_xg_margin
        == Decimal("0.50")
    )
    assert (
        thresholds.strong_xg_margin
        == Decimal("1.00")
    )


def test_thresholds_normalize_numeric_values() -> None:
    thresholds = TeamFormComparisonThresholds(
        balanced_xg_margin="0.10",  # type: ignore[arg-type]
        clear_xg_margin=0.40,  # type: ignore[arg-type]
        strong_xg_margin=1,  # type: ignore[arg-type]
    )

    assert (
        thresholds.balanced_xg_margin
        == Decimal("0.10")
    )
    assert (
        thresholds.clear_xg_margin
        == Decimal("0.4")
    )
    assert (
        thresholds.strong_xg_margin
        == Decimal("1")
    )


def test_thresholds_reject_negative_values() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        TeamFormComparisonThresholds(
            balanced_xg_margin=Decimal("-0.01")
        )


def test_thresholds_must_be_strictly_ordered() -> None:
    with pytest.raises(
        ValueError,
        match="must be ordered",
    ):
        TeamFormComparisonThresholds(
            balanced_xg_margin=Decimal("0.50"),
            clear_xg_margin=Decimal("0.50"),
            strong_xg_margin=Decimal("1.00"),
        )


def test_thresholds_reject_non_finite_values() -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        TeamFormComparisonThresholds(
            strong_xg_margin=Decimal("NaN")
        )