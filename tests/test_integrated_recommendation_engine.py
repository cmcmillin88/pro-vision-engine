"""Tests for the final integrated recommendation engine."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.integrated_recommendation import (
    IntegratedMatchRecommendation,
    IntegratedRiskFactor,
)
from src.models.integrated_recommendation_thresholds import (
    IntegratedRecommendationThresholds,
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
    """Create one configurable performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=datetime(
            2026,
            9,
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
    """Create one configurable market snapshot."""

    return MarketSnapshot(
        captured_at=datetime(
            2026,
            9,
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


def create_match_report(
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
):
    """Create one complete match-analysis report."""

    analysis_input = MatchAnalysisInput(
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
    )

    return MatchAnalysisEngine().analyze(
        analysis_input
    )


def test_engine_builds_complete_recommendation() -> None:
    recommendation = (
        IntegratedRecommendationEngine()
        .recommend(
            create_match_report()
        )
    )

    assert isinstance(
        recommendation,
        IntegratedMatchRecommendation,
    )
    assert recommendation.primary_outcome is Outcome.HOME
    assert (
        recommendation.coverage
        is RecommendationCoverage.DOUBLE
    )


def test_engine_calculates_expected_combined_probabilities() -> None:
    recommendation = (
        IntegratedRecommendationEngine()
        .recommend(
            create_match_report()
        )
    )

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


def test_standard_example_returns_expected_signs_and_risk() -> None:
    recommendation = (
        IntegratedRecommendationEngine()
        .recommend(
            create_match_report()
        )
    )

    assert recommendation.recommendation_symbols == "12"
    assert recommendation.risk_score == 6
    assert (
        recommendation.risk_level
        is RecommendationRiskLevel.HIGH
    )
    assert recommendation.is_spike_candidate is False


def test_strong_consensus_returns_low_risk_single() -> None:
    match_report = create_match_report(
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

    recommendation = (
        IntegratedRecommendationEngine()
        .recommend(
            match_report
        )
    )

    assert (
        match_report.conflict_level
        is ModelMarketConflictLevel.LOW
    )
    assert recommendation.primary_outcome is Outcome.HOME
    assert recommendation.recommended_outcomes == (
        Outcome.HOME,
    )
    assert (
        recommendation.coverage
        is RecommendationCoverage.SINGLE
    )
    assert (
        recommendation.risk_level
        is RecommendationRiskLevel.LOW
    )
    assert recommendation.risk_score == 0
    assert recommendation.is_spike_candidate is True


def test_high_model_market_conflict_forces_triple() -> None:
    match_report = create_match_report(
        home_xg_for="0.80",
        home_xg_against="1.80",
        away_xg_for="2.10",
        away_xg_against="0.70",
    )

    assert (
        match_report.conflict_level
        is ModelMarketConflictLevel.HIGH
    )

    recommendation = (
        IntegratedRecommendationEngine()
        .recommend(
            match_report
        )
    )

    assert recommendation.recommended_outcomes == (
        Outcome.HOME,
        Outcome.DRAW,
        Outcome.AWAY,
    )
    assert (
        recommendation.coverage
        is RecommendationCoverage.TRIPLE
    )
    assert recommendation.is_full_cover is True
    assert (
        recommendation.risk_level
        is RecommendationRiskLevel.EXTREME
    )
    assert recommendation.has_risk_factor(
        IntegratedRiskFactor
        .FAVORITE_DISAGREEMENT
    )
    assert recommendation.has_risk_factor(
        IntegratedRiskFactor
        .HIGH_MODEL_MARKET_CONFLICT
    )


def test_statistical_only_weight_matches_statistical_model() -> None:
    thresholds = IntegratedRecommendationThresholds(
        statistical_weight=Decimal("1.00"),
        market_weight=Decimal("0.00"),
    )

    recommendation = IntegratedRecommendationEngine(
        thresholds
    ).recommend(
        create_match_report()
    )

    assert (
        recommendation.for_outcome(
            Outcome.HOME
        ).combined_probability
        == Decimal("52.58")
    )
    assert (
        recommendation.for_outcome(
            Outcome.DRAW
        ).combined_probability
        == Decimal("24.51")
    )
    assert (
        recommendation.for_outcome(
            Outcome.AWAY
        ).combined_probability
        == Decimal("22.91")
    )


def test_market_only_weight_matches_market_probabilities() -> None:
    thresholds = IntegratedRecommendationThresholds(
        statistical_weight=Decimal("0.00"),
        market_weight=Decimal("1.00"),
    )

    recommendation = IntegratedRecommendationEngine(
        thresholds
    ).recommend(
        create_match_report()
    )

    assert (
        recommendation.for_outcome(
            Outcome.HOME
        ).combined_probability
        == Decimal("53.37")
    )
    assert (
        recommendation.for_outcome(
            Outcome.DRAW
        ).combined_probability
        == Decimal("25.28")
    )
    assert (
        recommendation.for_outcome(
            Outcome.AWAY
        ).combined_probability
        == Decimal("21.35")
    )


def test_custom_risk_thresholds_change_risk_level() -> None:
    thresholds = IntegratedRecommendationThresholds(
        medium_risk_score=1,
        high_risk_score=3,
        extreme_risk_score=6,
    )

    recommendation = IntegratedRecommendationEngine(
        thresholds
    ).recommend(
        create_match_report()
    )

    assert recommendation.risk_score == 6
    assert (
        recommendation.risk_level
        is RecommendationRiskLevel.EXTREME
    )


def test_engine_rejects_invalid_match_analysis() -> None:
    with pytest.raises(
        TypeError,
        match="requires a MatchAnalysisReport",
    ):
        IntegratedRecommendationEngine().recommend(
            object()  # type: ignore[arg-type]
        )


def test_engine_is_deterministic() -> None:
    match_report = create_match_report()
    engine = IntegratedRecommendationEngine()

    first_recommendation = engine.recommend(
        match_report
    )
    second_recommendation = engine.recommend(
        match_report
    )

    assert first_recommendation == second_recommendation