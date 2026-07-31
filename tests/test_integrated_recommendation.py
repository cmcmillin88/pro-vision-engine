"""Tests for final integrated recommendation models."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.integrated_recommendation import (
    IntegratedMatchRecommendation,
    IntegratedRiskFactor,
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
from src.services.integrated_recommendation_engine import (
    IntegratedRecommendationEngine,
)
from src.services.match_analysis_engine import (
    MatchAnalysisEngine,
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
            9,
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
            9,
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


def create_recommendation() -> IntegratedMatchRecommendation:
    """Create the standard integrated recommendation."""

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
    )

    match_analysis = MatchAnalysisEngine().analyze(
        analysis_input
    )

    return IntegratedRecommendationEngine().recommend(
        match_analysis
    )


def test_recommendation_exposes_summary_helpers() -> None:
    recommendation = create_recommendation()

    assert recommendation.primary_outcome is Outcome.HOME
    assert recommendation.recommendation_symbols == "12"
    assert recommendation.secondary_outcomes == (
        Outcome.AWAY,
    )
    assert recommendation.requires_guard is True
    assert recommendation.is_full_cover is False
    assert recommendation.is_spike_candidate is False


def test_recommendation_exposes_combined_probabilities() -> None:
    recommendation = create_recommendation()

    assert (
        recommendation.for_outcome(
            Outcome.HOME
        ).combined_probability
        == Decimal("52.89")
    )
    assert (
        recommendation.for_outcome(
            Outcome.DRAW
        ).combined_probability
        == Decimal("24.82")
    )
    assert (
        recommendation.for_outcome(
            Outcome.AWAY
        ).combined_probability
        == Decimal("22.29")
    )
    assert (
        recommendation.combined_confidence_margin
        == Decimal("28.07")
    )


def test_recommendation_exposes_risk_summary() -> None:
    recommendation = create_recommendation()

    assert (
        recommendation.risk_level
        is RecommendationRiskLevel.HIGH
    )
    assert recommendation.risk_score == 6
    assert recommendation.risk_factors == (
        IntegratedRiskFactor.HIGH_MARKET_RISK,
        IntegratedRiskFactor.MODEL_VALUE_CHALLENGER,
        IntegratedRiskFactor.GUARD_REQUIRED,
    )


def test_outcome_assessment_exposes_combined_value() -> None:
    recommendation = create_recommendation()
    away = recommendation.for_outcome(
        Outcome.AWAY
    )

    assert (
        away.combined_public_edge
        == Decimal("5.29")
    )
    assert away.has_positive_combined_value is True


def test_recommendation_rejects_invalid_match_analysis() -> None:
    recommendation = create_recommendation()

    with pytest.raises(
        TypeError,
        match="MatchAnalysisReport",
    ):
        IntegratedMatchRecommendation(
            match_analysis=object(),  # type: ignore[arg-type]
            outcome_assessments=(
                recommendation.outcome_assessments
            ),
            primary_outcome=(
                recommendation.primary_outcome
            ),
            recommended_outcomes=(
                recommendation.recommended_outcomes
            ),
            coverage=recommendation.coverage,
            risk_level=recommendation.risk_level,
            risk_score=recommendation.risk_score,
            risk_factors=recommendation.risk_factors,
        )


def test_recommendation_rejects_unordered_assessments() -> None:
    recommendation = create_recommendation()

    with pytest.raises(
        ValueError,
        match="official 1-X-2 order",
    ):
        replace(
            recommendation,
            outcome_assessments=(
                recommendation.outcome_assessments[2],
                recommendation.outcome_assessments[1],
                recommendation.outcome_assessments[0],
            ),
        )


def test_recommendation_rejects_mismatched_source_probability() -> None:
    recommendation = create_recommendation()
    home = recommendation.for_outcome(
        Outcome.HOME
    )
    changed_home = replace(
        home,
        statistical_probability=Decimal("53.58"),
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        replace(
            recommendation,
            outcome_assessments=(
                changed_home,
                recommendation.outcome_assessments[1],
                recommendation.outcome_assessments[2],
            ),
        )


def test_recommendation_rejects_wrong_primary_outcome() -> None:
    recommendation = create_recommendation()

    with pytest.raises(
        ValueError,
        match="highest combined probability",
    ):
        replace(
            recommendation,
            primary_outcome=Outcome.DRAW,
            recommended_outcomes=(
                Outcome.DRAW,
                Outcome.AWAY,
            ),
        )


def test_recommendation_rejects_coverage_mismatch() -> None:
    recommendation = create_recommendation()

    with pytest.raises(
        ValueError,
        match="coverage does not match",
    ):
        replace(
            recommendation,
            coverage=RecommendationCoverage.TRIPLE,
        )


def test_recommendation_rejects_risk_score_mismatch() -> None:
    recommendation = create_recommendation()

    with pytest.raises(
        ValueError,
        match="total risk-factor weight",
    ):
        replace(
            recommendation,
            risk_score=7,
        )