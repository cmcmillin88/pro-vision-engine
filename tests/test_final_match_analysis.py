"""Tests for the final end-to-end match-analysis report."""

from dataclasses import replace
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
    """Create one compact performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=datetime(
            2026,
            10,
            20,
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
    """Create one market snapshot."""

    return MarketSnapshot(
        captured_at=datetime(
            2026,
            10,
            20,
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
    home_team_name: str = "Arsenal",
) -> MatchAnalysisInput:
    """Create one valid complete analysis input."""

    return MatchAnalysisInput(
        home_team_name=home_team_name,
        away_team_name="Chelsea",
        home_performances=(
            create_performance(
                team_name=home_team_name,
                opponent_name="Tottenham",
                venue=MatchVenue.HOME,
                xg_for="1.80",
                xg_against="0.80",
            ),
        ),
        away_performances=(
            create_performance(
                team_name="Chelsea",
                opponent_name="Liverpool",
                venue=MatchVenue.AWAY,
                xg_for="1.20",
                xg_against="1.50",
            ),
        ),
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
        match_reference="Match 1",
    )


def create_report() -> FinalMatchAnalysisReport:
    """Create the standard final report."""

    return FinalMatchAnalysisEngine().analyze(
        create_input()
    )


def test_report_exposes_complete_component_chain() -> None:
    report = create_report()

    assert (
        report.match_analysis.analysis_input
        == report.analysis_input
    )
    assert (
        report.recommendation.match_analysis
        == report.match_analysis
    )


def test_report_exposes_match_summary() -> None:
    report = create_report()

    assert report.home_team_name == "Arsenal"
    assert report.away_team_name == "Chelsea"
    assert report.projected_scoreline == "1.65-1.00"
    assert report.primary_outcome is Outcome.HOME


def test_report_exposes_final_recommendation() -> None:
    report = create_report()

    assert report.recommendation_symbols == "12"
    assert (
        report.coverage
        is RecommendationCoverage.DOUBLE
    )
    assert (
        report.final_decision_type
        is FinalDecisionType.DOUBLE
    )
    assert report.is_spike_candidate is False


def test_report_exposes_combined_probabilities() -> None:
    report = create_report()

    assert (
        report.combined_probability_for(
            Outcome.HOME
        )
        == Decimal("52.89")
    )
    assert (
        report.combined_probability_for(
            Outcome.DRAW
        )
        == Decimal("24.82")
    )
    assert (
        report.combined_probability_for(
            Outcome.AWAY
        )
        == Decimal("22.29")
    )


def test_high_final_risk_requires_extended_review() -> None:
    report = create_report()

    assert (
        report.risk_level
        is RecommendationRiskLevel.HIGH
    )
    assert report.requires_extended_review is True


def test_report_creates_flat_summary() -> None:
    report = create_report()
    summary = report.to_summary()

    assert isinstance(
        summary,
        FinalMatchSummary,
    )
    assert summary.recommendation_symbols == "12"
    assert summary.decision_type is FinalDecisionType.DOUBLE


def test_report_rejects_mismatched_analysis_input() -> None:
    report = create_report()
    other_input = create_input(
        home_team_name="Liverpool"
    )

    with pytest.raises(
        ValueError,
        match="same MatchAnalysisInput",
    ):
        replace(
            report,
            analysis_input=other_input,
        )


def test_report_rejects_mismatched_recommendation() -> None:
    report = create_report()
    other_report = FinalMatchAnalysisEngine().analyze(
        create_input(
            home_team_name="Liverpool"
        )
    )

    with pytest.raises(
        ValueError,
        match="supplied MatchAnalysisReport",
    ):
        replace(
            report,
            recommendation=other_report.recommendation,
        )