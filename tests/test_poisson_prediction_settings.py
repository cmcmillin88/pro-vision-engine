"""Tests for Poisson prediction settings."""

from decimal import Decimal

import pytest

from src.models.poisson_prediction_settings import (
    PoissonPredictionSettings,
)


def test_settings_have_expected_defaults() -> None:
    settings = PoissonPredictionSettings()

    assert settings.maximum_goals == 10
    assert (
        settings.minimum_included_mass
        == Decimal("99.00")
    )


def test_settings_normalize_numeric_mass() -> None:
    settings = PoissonPredictionSettings(
        maximum_goals=12,
        minimum_included_mass="98.5",  # type: ignore[arg-type]
    )

    assert settings.maximum_goals == 12
    assert (
        settings.minimum_included_mass
        == Decimal("98.5")
    )


def test_settings_reject_boolean_maximum_goals() -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        PoissonPredictionSettings(
            maximum_goals=True  # type: ignore[arg-type]
        )


def test_settings_reject_invalid_maximum_goals() -> None:
    with pytest.raises(
        ValueError,
        match="between 1 and 30",
    ):
        PoissonPredictionSettings(
            maximum_goals=0
        )


def test_settings_reject_negative_minimum_mass() -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 100",
    ):
        PoissonPredictionSettings(
            minimum_included_mass=Decimal("-0.01")
        )


def test_settings_reject_minimum_mass_above_100() -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 100",
    ):
        PoissonPredictionSettings(
            minimum_included_mass=Decimal("100.01")
        )


def test_settings_reject_non_finite_minimum_mass() -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        PoissonPredictionSettings(
            minimum_included_mass=Decimal("NaN")
        )