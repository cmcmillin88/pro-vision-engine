"""Tests for the final Project 13 match-analysis engine."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.final_match_analysis import (
    FinalMatchAnalysisReport,
)
from src.models.final_match_summary import (
    FinalDecisionType,
    FinalMatchSummary,
)
from src.models.market_recommendation import (
    RecommendationCoverage,
    RecommendationRiskLevel,
)
from src.models.market_snapshot import MarketSnapshot
from src.models.match_analysis_input import MatchAnalysisInput
from src.models.outcome import Outcome
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.final_match_analysis_engine import (
    FinalMatchAnalysisEngine,
)


def create_performance(
    *,
    team_name: str,
    opponent_name: str,
    venue: MatchVenue,
    xg_for: str,
    xg_against: str,
) -> TeamMatchPerformance:
    """Create one configurable performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=datetime(
            2026,
            10,
            30,
            15,
            0,
            tzinfo=timezone.utc,
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
) -> MarketSnapshot:
    """Create one configurable snapshot."""

    return MarketSnapshot(
        captured_at=datetime(
            2026,
            10,
            30,
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
        source_name="combined-market",
    )


def create_input(
    *,
    home_xg_for: str = "1.80",
    home_xg_against: str = "0.80",
    away_xg_for: str = "1.20",
    away_xg_against: str = "1.50",
    earlier_odds: tuple[str, str, str] = (
        "2.00",
        "3.50",
        "4.00",
    ),
    later_odds: tuple[str, str, str] = (
        "1.80",
        "3.80",
        "4.50",
    ),
    earlier_percentages: tuple[str, str, str] = (
        "55",
        "25",
        "20",
    ),
    later_percentages: tuple[str, str, str] = (
        "60",
        "23",
        "17",
    ),
) -> MatchAnalysisInput:
    """Create one configurable complete input."""

    return MatchAnalysisInput(
        home_team_name="Arsenal",
        away_team_name="Chelsea",
        home_performances=(
            create_performance(
                team_name="Arsenal",
                opponent_name="Tottenham",
                venue=MatchVenue.HOME,
                xg_for=home_xg_for,
                xg_against=home_xg_against,
            ),
        ),
        away_performances=(
            create_performance(
                team_name="Chelsea",
                opponent_name="Liverpool",
                venue=MatchVenue.AWAY,
                xg_for=away_xg_for,
                xg_against=away_xg_against,
            ),
        ),
        earlier_market_snapshot=create_snapshot(
            hour=12,
            odds=earlier_odds,
            percentages=earlier_percentages,
        ),
        later_market_snapshot=create_snapshot(
            hour=14,
            odds=later_odds,
            percentages=later_percentages,
        ),
        match_reference="Coupon match 1",
    )


def test_engine_builds_complete_final_report() -> None:
    report = FinalMatchAnalysisEngine().analyze(
        create_input()
    )

    assert isinstance(
        report,
        FinalMatchAnalysisReport,
    )
    assert (
        report.recommendation.match_analysis
        == report.match_analysis
    )


def test_engine_returns_expected_standard_summary() -> None:
    report = FinalMatchAnalysisEngine().analyze(
        create_input()
    )

    assert report.primary_outcome is Outcome.HOME
    assert report.recommendation_symbols == "12"
    assert report.risk_score == 6
    assert (
        report.final_decision_type
        is FinalDecisionType.DOUBLE
    )


def test_engine_can_return_flat_summary_directly() -> None:
    summary = (
        FinalMatchAnalysisEngine()
        .analyze_summary(
            create_input()
        )
    )

    assert isinstance(
        summary,
        FinalMatchSummary,
    )
    assert summary.combined_home_probability == Decimal("52.89")
    assert summary.recommendation_symbols == "12"


def test_strong_consensus_creates_final_spike() -> None:
    report = FinalMatchAnalysisEngine().analyze(
        create_input(
            home_xg_for="2.10",
            home_xg_against="0.60",
            away_xg_for="0.60",
            away_xg_against="2.10",
            earlier_odds=(
                "1.40",
                "5.20",
                "9.00",
            ),
            later_odds=(
                "1.35",
                "5.50",
                "10.00",
            ),
            earlier_percentages=(
                "67",
                "19",
                "14",
            ),
            later_percentages=(
                "68",
                "18",
                "14",
            ),
        )
    )

    assert report.primary_outcome is Outcome.HOME
    assert report.recommended_outcomes == (
        Outcome.HOME,
    )
    assert (
        report.coverage
        is RecommendationCoverage.SINGLE
    )
    assert (
        report.risk_level
        is RecommendationRiskLevel.LOW
    )
    assert report.is_spike_candidate is True
    assert (
        report.final_decision_type
        is FinalDecisionType.SPIKE
    )
    assert report.requires_extended_review is False


def test_engine_rejects_invalid_analysis_input() -> None:
    with pytest.raises(
        TypeError,
        match="requires a MatchAnalysisInput",
    ):
        FinalMatchAnalysisEngine().analyze(
            object()  # type: ignore[arg-type]
        )


def test_engine_rejects_invalid_match_engine_dependency() -> None:
    with pytest.raises(
        TypeError,
        match="MatchAnalysisEngine",
    ):
        FinalMatchAnalysisEngine(
            match_analysis_engine=object(),  # type: ignore[arg-type]
        )


def test_engine_rejects_invalid_recommendation_dependency() -> None:
    with pytest.raises(
        TypeError,
        match="IntegratedRecommendationEngine",
    ):
        FinalMatchAnalysisEngine(
            recommendation_engine=object(),  # type: ignore[arg-type]
        )


def test_engine_is_deterministic() -> None:
    analysis_input = create_input()
    engine = FinalMatchAnalysisEngine()

    first_report = engine.analyze(
        analysis_input
    )
    second_report = engine.analyze(
        analysis_input
    )

    assert first_report == second_report