"""Tests for export-ready final match summaries."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.final_match_summary import (
    FinalDecisionType,
    FinalMatchSummary,
)
from src.models.integrated_recommendation import (
    IntegratedRiskFactor,
)
from src.models.market_recommendation import (
    RecommendationCoverage,
    RecommendationRiskLevel,
)
from src.models.market_snapshot import MarketSnapshot
from src.models.match_analysis_input import MatchAnalysisInput
from src.models.outcome import Outcome
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
    """Create one compact team performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=datetime(
            2026,
            10,
            10,
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
    """Create one compact market snapshot."""

    return MarketSnapshot(
        captured_at=datetime(
            2026,
            10,
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
        source_name="combined-market",
    )


def create_summary() -> FinalMatchSummary:
    """Create the standard completed final summary."""

    analysis_input = MatchAnalysisInput(
        home_team_name="Arsenal",
        away_team_name="Chelsea",
        home_performances=(
            create_performance(
                team_name="Arsenal",
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

    return (
        FinalMatchAnalysisEngine()
        .analyze_summary(
            analysis_input
        )
    )


def test_summary_exposes_expected_values() -> None:
    summary = create_summary()

    assert summary.home_team_name == "Arsenal"
    assert summary.away_team_name == "Chelsea"
    assert summary.projected_home_xg == Decimal("1.65")
    assert summary.projected_away_xg == Decimal("1.00")
    assert summary.recommendation_symbols == "12"


def test_summary_exposes_final_decision_helpers() -> None:
    summary = create_summary()

    assert (
        summary.decision_type
        is FinalDecisionType.DOUBLE
    )
    assert summary.requires_guard is True
    assert summary.is_full_cover is False
    assert summary.is_spike_candidate is False


def test_summary_probability_lookup_helpers() -> None:
    summary = create_summary()

    assert (
        summary.statistical_probability_for(
            Outcome.HOME
        )
        == Decimal("52.58")
    )
    assert (
        summary.combined_probability_for(
            Outcome.HOME
        )
        == Decimal("52.89")
    )


def test_summary_exposes_expected_risk() -> None:
    summary = create_summary()

    assert (
        summary.risk_level
        is RecommendationRiskLevel.HIGH
    )
    assert summary.risk_score == 6
    assert summary.risk_factors == (
        IntegratedRiskFactor.HIGH_MARKET_RISK,
        IntegratedRiskFactor.MODEL_VALUE_CHALLENGER,
        IntegratedRiskFactor.GUARD_REQUIRED,
    )


def test_summary_rejects_invalid_probability_total() -> None:
    summary = create_summary()

    with pytest.raises(
        ValueError,
        match="Combined probabilities",
    ):
        replace(
            summary,
            combined_home_probability=Decimal("51.89"),
        )


def test_summary_rejects_wrong_primary_outcome() -> None:
    summary = create_summary()

    with pytest.raises(
        ValueError,
        match="highest combined probability",
    ):
        replace(
            summary,
            primary_outcome=Outcome.DRAW,
        )


def test_summary_rejects_wrong_decision_type() -> None:
    summary = create_summary()

    with pytest.raises(
        ValueError,
        match="decision_type",
    ):
        replace(
            summary,
            decision_type=FinalDecisionType.SPIKE,
        )


def test_summary_rejects_risk_score_mismatch() -> None:
    summary = create_summary()

    with pytest.raises(
        ValueError,
        match="risk-factor weight",
    ):
        replace(
            summary,
            risk_score=7,
        )