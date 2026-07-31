"""Tests for the complete statistical-analysis engine."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.models.outcome import Outcome
from src.models.poisson_prediction_settings import (
    PoissonPredictionSettings,
)
from src.models.statistical_analysis import (
    StatisticalAnalysisReport,
)
from src.models.statistical_analysis_settings import (
    StatisticalAnalysisSettings,
)
from src.models.team_form_comparison import (
    FormEdgeStrength,
    MatchupLean,
)
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.services.poisson_match_predictor import (
    PoissonMatchPredictor,
)
from src.services.statistical_analysis_engine import (
    StatisticalAnalysisEngine,
)


BASE_TIME = datetime(
    2026,
    8,
    30,
    15,
    0,
    tzinfo=timezone.utc,
)


def create_performance(
    *,
    team_name: str,
    opponent_name: str,
    days_ago: int,
    venue: MatchVenue,
    competition: str,
    xg_for: str,
    xg_against: str,
    goals_for: int = 1,
    goals_against: int = 1,
) -> TeamMatchPerformance:
    """Create one configurable performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=(
            BASE_TIME
            - timedelta(
                days=days_ago
            )
        ),
        venue=venue,
        goals_for=goals_for,
        goals_against=goals_against,
        expected_goals_for=Decimal(xg_for),
        expected_goals_against=Decimal(xg_against),
        shots_for=12,
        shots_against=10,
        shots_on_target_for=5,
        shots_on_target_against=4,
        competition=competition,
    )


def create_home_performances() -> tuple[
    TeamMatchPerformance,
    ...,
]:
    """Create mixed Arsenal home and away performances."""

    return (
        create_performance(
            team_name="Arsenal",
            opponent_name="Manchester City",
            days_ago=1,
            venue=MatchVenue.AWAY,
            competition="Premier League",
            xg_for="0.40",
            xg_against="2.50",
            goals_for=0,
            goals_against=2,
        ),
        create_performance(
            team_name="Arsenal",
            opponent_name="Tottenham",
            days_ago=2,
            venue=MatchVenue.HOME,
            competition="Premier League",
            xg_for="2.00",
            xg_against="0.70",
            goals_for=2,
            goals_against=0,
        ),
        create_performance(
            team_name="Arsenal",
            opponent_name="Chelsea",
            days_ago=9,
            venue=MatchVenue.HOME,
            competition="Premier League",
            xg_for="1.80",
            xg_against="1.00",
            goals_for=2,
            goals_against=1,
        ),
        create_performance(
            team_name="Arsenal",
            opponent_name="Liverpool",
            days_ago=16,
            venue=MatchVenue.HOME,
            competition="Premier League",
            xg_for="1.60",
            xg_against="0.70",
            goals_for=1,
            goals_against=1,
        ),
        create_performance(
            team_name="Arsenal",
            opponent_name="Inter",
            days_ago=23,
            venue=MatchVenue.HOME,
            competition="Champions League",
            xg_for="3.00",
            xg_against="0.20",
            goals_for=3,
            goals_against=0,
        ),
    )


def create_away_performances() -> tuple[
    TeamMatchPerformance,
    ...,
]:
    """Create mixed Chelsea away and home performances."""

    return (
        create_performance(
            team_name="Chelsea",
            opponent_name="Everton",
            days_ago=1,
            venue=MatchVenue.HOME,
            competition="Premier League",
            xg_for="2.50",
            xg_against="0.50",
            goals_for=3,
            goals_against=0,
        ),
        create_performance(
            team_name="Chelsea",
            opponent_name="Liverpool",
            days_ago=3,
            venue=MatchVenue.AWAY,
            competition="Premier League",
            xg_for="1.30",
            xg_against="1.40",
            goals_for=1,
            goals_against=2,
        ),
        create_performance(
            team_name="Chelsea",
            opponent_name="Newcastle",
            days_ago=10,
            venue=MatchVenue.AWAY,
            competition="Premier League",
            xg_for="1.00",
            xg_against="1.60",
            goals_for=0,
            goals_against=1,
        ),
        create_performance(
            team_name="Chelsea",
            opponent_name="Everton",
            days_ago=17,
            venue=MatchVenue.AWAY,
            competition="Premier League",
            xg_for="1.30",
            xg_against="1.50",
            goals_for=2,
            goals_against=1,
        ),
        create_performance(
            team_name="Chelsea",
            opponent_name="Milan",
            days_ago=24,
            venue=MatchVenue.AWAY,
            competition="Champions League",
            xg_for="2.40",
            xg_against="0.60",
            goals_for=2,
            goals_against=0,
        ),
    )


def create_engine() -> StatisticalAnalysisEngine:
    """Create the standard configured statistical engine."""

    return StatisticalAnalysisEngine(
        StatisticalAnalysisSettings(
            home_match_limit=3,
            away_match_limit=3,
            competition="Premier League",
        )
    )


def test_engine_builds_complete_statistical_report() -> None:
    report = create_engine().analyze(
        create_home_performances(),
        create_away_performances(),
    )

    assert isinstance(
        report,
        StatisticalAnalysisReport,
    )
    assert (
        report.prediction.comparison
        == report.form_comparison
    )


def test_engine_filters_home_and_away_contexts() -> None:
    report = create_engine().analyze(
        create_home_performances(),
        create_away_performances(),
    )

    assert report.home_match_count == 3
    assert report.away_match_count == 3
    assert all(
        match.venue is MatchVenue.HOME
        for match in report.home_form.matches
    )
    assert all(
        match.venue is MatchVenue.AWAY
        for match in report.away_form.matches
    )


def test_engine_filters_requested_competition() -> None:
    report = create_engine().analyze(
        create_home_performances(),
        create_away_performances(),
    )

    assert all(
        match.competition == "Premier League"
        for match in (
            report.home_form.matches
            + report.away_form.matches
        )
    )


def test_engine_calculates_expected_form_averages() -> None:
    report = create_engine().analyze(
        create_home_performances(),
        create_away_performances(),
    )

    assert (
        report.home_form
        .expected_goals_for_average
        == Decimal("1.80")
    )
    assert (
        report.home_form
        .expected_goals_against_average
        == Decimal("0.80")
    )
    assert (
        report.away_form
        .expected_goals_for_average
        == Decimal("1.20")
    )
    assert (
        report.away_form
        .expected_goals_against_average
        == Decimal("1.50")
    )


def test_engine_calculates_expected_projection() -> None:
    report = create_engine().analyze(
        create_home_performances(),
        create_away_performances(),
    )

    assert report.projected_scoreline == "1.65-1.00"
    assert report.matchup_lean is MatchupLean.HOME
    assert (
        report.edge_strength
        is FormEdgeStrength.CLEAR
    )


def test_engine_calculates_expected_probabilities() -> None:
    report = create_engine().analyze(
        create_home_performances(),
        create_away_performances(),
    )

    assert (
        report.probability_for(
            Outcome.HOME
        )
        == Decimal("52.58")
    )
    assert (
        report.probability_for(
            Outcome.DRAW
        )
        == Decimal("24.51")
    )
    assert (
        report.probability_for(
            Outcome.AWAY
        )
        == Decimal("22.91")
    )


def test_engine_identifies_expected_scoreline() -> None:
    report = create_engine().analyze(
        create_home_performances(),
        create_away_performances(),
    )

    assert (
        report.most_likely_scoreline.scoreline
        == "1-0"
    )
    assert (
        report.most_likely_scoreline.probability
        == Decimal("11.66")
    )


def test_custom_limits_change_form_window() -> None:
    engine = StatisticalAnalysisEngine(
        StatisticalAnalysisSettings(
            home_match_limit=2,
            away_match_limit=1,
            competition="Premier League",
        )
    )

    report = engine.analyze(
        create_home_performances(),
        create_away_performances(),
    )

    assert report.home_match_count == 2
    assert report.away_match_count == 1


def test_engine_accepts_custom_predictor() -> None:
    predictor = PoissonMatchPredictor(
        PoissonPredictionSettings(
            maximum_goals=5
        )
    )
    engine = StatisticalAnalysisEngine(
        StatisticalAnalysisSettings(
            home_match_limit=3,
            away_match_limit=3,
            competition="Premier League",
        ),
        predictor=predictor,
    )

    report = engine.analyze(
        create_home_performances(),
        create_away_performances(),
    )

    assert report.prediction.maximum_goals == 5
    assert len(
        report.prediction.scorelines
    ) == 36


def test_engine_rejects_invalid_settings_dependency() -> None:
    with pytest.raises(
        TypeError,
        match="StatisticalAnalysisSettings",
    ):
        StatisticalAnalysisEngine(
            settings=object()  # type: ignore[arg-type]
        )


def test_engine_fails_when_no_home_performance_matches() -> None:
    away_only_home_team = tuple(
        performance
        for performance in create_home_performances()
        if performance.venue is MatchVenue.AWAY
    )

    with pytest.raises(
        ValueError,
        match="requested filters",
    ):
        create_engine().analyze(
            away_only_home_team,
            create_away_performances(),
        )


def test_engine_is_deterministic() -> None:
    engine = create_engine()
    home_performances = create_home_performances()
    away_performances = create_away_performances()

    first_report = engine.analyze(
        home_performances,
        away_performances,
    )
    second_report = engine.analyze(
        home_performances,
        away_performances,
    )

    assert first_report == second_report