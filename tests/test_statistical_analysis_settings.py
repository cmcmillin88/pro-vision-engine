"""Tests for complete statistical-analysis settings."""

import pytest

from src.models.statistical_analysis_settings import (
    StatisticalAnalysisSettings,
)


def test_settings_have_expected_defaults() -> None:
    settings = StatisticalAnalysisSettings()

    assert settings.home_match_limit == 5
    assert settings.away_match_limit == 5
    assert settings.competition is None


def test_settings_normalize_competition() -> None:
    settings = StatisticalAnalysisSettings(
        competition="  Premier   League  "
    )

    assert settings.competition == "Premier League"


def test_settings_allow_unlimited_match_windows() -> None:
    settings = StatisticalAnalysisSettings(
        home_match_limit=None,
        away_match_limit=None,
    )

    assert settings.home_match_limit is None
    assert settings.away_match_limit is None


def test_settings_reject_non_positive_home_limit() -> None:
    with pytest.raises(
        ValueError,
        match="home_match_limit",
    ):
        StatisticalAnalysisSettings(
            home_match_limit=0
        )


def test_settings_reject_invalid_away_limit_type() -> None:
    with pytest.raises(
        TypeError,
        match="away_match_limit",
    ):
        StatisticalAnalysisSettings(
            away_match_limit=True  # type: ignore[arg-type]
        )


def test_settings_reject_empty_competition() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        StatisticalAnalysisSettings(
            competition="   "
        )


def test_settings_reject_invalid_competition_type() -> None:
    with pytest.raises(
        TypeError,
        match="string or None",
    ):
        StatisticalAnalysisSettings(
            competition=123  # type: ignore[arg-type]
        )