"""Tests for the complete football match-analysis engine."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.models.market_snapshot import MarketSnapshot
from src.models.match_analysis import MatchAnalysisReport
from src.models.match_analysis_input import (
    MatchAnalysisInput,
)
from src.models.outcome import Outcome
from src.models.statistical_analysis_settings import (
    StatisticalAnalysisSettings,
)
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
)
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.match_analysis_engine import (
    MatchAnalysisEngine,
)
from src.services.statistical_analysis_engine import (
    StatisticalAnalysisEngine,
)


BASE_TIME = datetime(
    2026,
    9,
    10,
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
    xg_for: str,
    xg_against: str,
) -> TeamMatchPerformance:
    """Create one configurable team performance."""

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
        goals_for=1,
        goals_against=1,
        expected_goals_for=Decimal(xg_for),
        expected_goals_against=Decimal(xg_against),
        shots_for=12,
        shots_against=10,
        shots_on_target_for=5,
        shots_on_target_against=4,
    )


def create_snapshot(
    *,
    hour: int,
    odds: tuple[str, str, str],
    percentages: tuple[str, str, str],
    source_name: str = "combined-market",
) -> MarketSnapshot:
    """Create one configurable market snapshot."""

    return MarketSnapshot(
        captured_at=datetime(
            2026,
            9,
            10,
            hour,
            0,
            tzinfo=timezone.utc,
        ),
        odds=ThreeWayOdds(
            Decimal(odds[0]),
            Decimal(odds[1]),
            Decimal(odds[2]),
        ),
        public_percentages=ThreeWayPercentages(
            Decimal(percentages[0]),
            Decimal(percentages[1]),
            Decimal(percentages[2]),
        ),
        source_name=source_name,
    )


def create_input() -> MatchAnalysisInput:
    """Create the standard complete match-analysis input."""

    home_performances = (
        create_performance(
            team_name="Arsenal",
            opponent_name="Tottenham",
            days_ago=1,
            venue=MatchVenue.HOME,
            xg_for="2.00",
            xg_against="0.70",
        ),
        create_performance(
            team_name="Arsenal",
            opponent_name="Chelsea",
            days_ago=8,
            venue=MatchVenue.HOME,
            xg_for="1.80",
            xg_against="1.00",
        ),
        create_performance(
            team_name="Arsenal",
            opponent_name="Liverpool",
            days_ago=15,
            venue=MatchVenue.HOME,
            xg_for="1.60",
            xg_against="0.70",
        ),
        create_performance(
            team_name="Arsenal",
            opponent_name="Manchester City",
            days_ago=2,
            venue=MatchVenue.AWAY,
            xg_for="0.40",
            xg_against="2.50",
        ),
    )
    away_performances = (
        create_performance(
            team_name="Chelsea",
            opponent_name="Liverpool",
            days_ago=2,
            venue=MatchVenue.AWAY,
            xg_for="1.30",
            xg_against="1.40",
        ),
        create_performance(
            team_name="Chelsea",
            opponent_name="Newcastle",
            days_ago=9,
            venue=MatchVenue.AWAY,
            xg_for="1.00",
            xg_against="1.60",
        ),
        create_performance(
            team_name="Chelsea",
            opponent_name="Everton",
            days_ago=16,
            venue=MatchVenue.AWAY,
            xg_for="1.30",
            xg_against="1.50",
        ),
        create_performance(
            team_name="Chelsea",
            opponent_name="Tottenham",
            days_ago=1,
            venue=MatchVenue.HOME,
            xg_for="2.50",
            xg_against="0.50",
        ),
    )

    return MatchAnalysisInput(
        home_team_name="Arsenal",
        away_team_name="Chelsea",
        home_performances=home_performances,
        away_performances=away_performances,
        earlier_market_snapshot=create_snapshot(
            hour=12,
            odds=(
                "2.00",
                "3.50",
                "4.00",
            ),
            percentages=(
                "55",
                "25",
                "20",
            ),
        ),
        later_market_snapshot=create_snapshot(
            hour=14,
            odds=(
                "1.80",
                "3.80",
                "4.50",
            ),
            percentages=(
                "60",
                "23",
                "17",
            ),
        ),
        match_reference="Coupon match 1",
    )


def test_engine_builds_complete_match_report() -> None:
    report = MatchAnalysisEngine().analyze(
        create_input()
    )

    assert isinstance(
        report,
        MatchAnalysisReport,
    )
    assert (
        report.evidence_comparison
        .statistical_prediction
        == report.statistical_analysis.prediction
    )
    assert (
        report.evidence_comparison.market_analysis
        == report.market_analysis
    )


def test_engine_returns_expected_integrated_summary() -> None:
    report = MatchAnalysisEngine().analyze(
        create_input()
    )

    assert report.projected_scoreline == "1.65-1.00"
    assert report.statistical_favorite is Outcome.HOME
    assert report.market_favorite is Outcome.HOME
    assert report.public_favorite is Outcome.HOME
    assert report.full_consensus is True
    assert report.recommendation_symbols == "12"
    assert (
        report.strongest_model_value.outcome
        is Outcome.AWAY
    )
    assert (
        report.conflict_level
        is ModelMarketConflictLevel.LOW
    )


def test_engine_uses_relevant_venue_contexts() -> None:
    report = MatchAnalysisEngine().analyze(
        create_input()
    )

    assert report.statistical_analysis.home_match_count == 3
    assert report.statistical_analysis.away_match_count == 3
    assert all(
        match.venue is MatchVenue.HOME
        for match in (
            report.statistical_analysis
            .home_form.matches
        )
    )
    assert all(
        match.venue is MatchVenue.AWAY
        for match in (
            report.statistical_analysis
            .away_form.matches
        )
    )


def test_engine_accepts_custom_statistical_window() -> None:
    statistical_engine = StatisticalAnalysisEngine(
        StatisticalAnalysisSettings(
            home_match_limit=2,
            away_match_limit=1,
        )
    )
    engine = MatchAnalysisEngine(
        statistical_engine=statistical_engine
    )

    report = engine.analyze(
        create_input()
    )

    assert report.statistical_analysis.home_match_count == 2
    assert report.statistical_analysis.away_match_count == 1


def test_engine_rejects_invalid_analysis_input() -> None:
    with pytest.raises(
        TypeError,
        match="requires a MatchAnalysisInput",
    ):
        MatchAnalysisEngine().analyze(
            object()  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    (
        "dependency_name",
        "dependency_value",
        "expected_message",
    ),
    [
        (
            "statistical_engine",
            object(),
            "StatisticalAnalysisEngine",
        ),
        (
            "market_engine",
            object(),
            "MarketAnalysisEngine",
        ),
        (
            "comparison_analyzer",
            object(),
            "StatisticalMarketComparisonAnalyzer",
        ),
    ],
)
def test_engine_rejects_invalid_dependencies(
    dependency_name: str,
    dependency_value: object,
    expected_message: str,
) -> None:
    with pytest.raises(
        TypeError,
        match=expected_message,
    ):
        MatchAnalysisEngine(
            **{
                dependency_name: dependency_value,
            }  # type: ignore[arg-type]
        )


def test_engine_propagates_invalid_market_chronology() -> None:
    analysis_input = create_input()
    invalid_later = MarketSnapshot(
        captured_at=(
            analysis_input
            .earlier_market_snapshot
            .captured_at
        ),
        odds=(
            analysis_input
            .later_market_snapshot
            .odds
        ),
        public_percentages=(
            analysis_input
            .later_market_snapshot
            .public_percentages
        ),
        source_name=(
            analysis_input
            .later_market_snapshot
            .source_name
        ),
    )
    invalid_input = replace(
        analysis_input,
        later_market_snapshot=invalid_later,
    )

    with pytest.raises(
        ValueError,
        match="captured after",
    ):
        MatchAnalysisEngine().analyze(
            invalid_input
        )


def test_strong_consensus_creates_joint_spike_candidate() -> None:
    strong_home = (
        create_performance(
            team_name="Arsenal",
            opponent_name="Tottenham",
            days_ago=1,
            venue=MatchVenue.HOME,
            xg_for="2.00",
            xg_against="0.80",
        ),
    )
    weak_away = (
        create_performance(
            team_name="Chelsea",
            opponent_name="Liverpool",
            days_ago=1,
            venue=MatchVenue.AWAY,
            xg_for="0.80",
            xg_against="2.00",
        ),
    )
    analysis_input = MatchAnalysisInput(
        home_team_name="Arsenal",
        away_team_name="Chelsea",
        home_performances=strong_home,
        away_performances=weak_away,
        earlier_market_snapshot=create_snapshot(
            hour=12,
            odds=(
                "1.55",
                "4.40",
                "6.50",
            ),
            percentages=(
                "60",
                "23",
                "17",
            ),
        ),
        later_market_snapshot=create_snapshot(
            hour=14,
            odds=(
                "1.50",
                "4.50",
                "7.00",
            ),
            percentages=(
                "62",
                "22",
                "16",
            ),
        ),
    )

    report = MatchAnalysisEngine().analyze(
        analysis_input
    )

    assert report.statistical_favorite is Outcome.HOME
    assert report.market_favorite is Outcome.HOME
    assert report.public_favorite is Outcome.HOME
    assert (
        report.conflict_level
        is ModelMarketConflictLevel.LOW
    )
    assert report.market_spike_candidate is True
    assert report.is_joint_spike_candidate is True


def test_engine_is_deterministic() -> None:
    analysis_input = create_input()
    engine = MatchAnalysisEngine()

    first_report = engine.analyze(
        analysis_input
    )
    second_report = engine.analyze(
        analysis_input
    )

    assert first_report == second_report