"""Tests for the market recommendation engine."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_classification import (
    MarketClassificationReport,
)
from src.models.market_recommendation import (
    RecommendationCoverage,
    RecommendationRiskFactor,
    RecommendationRiskLevel,
)
from src.models.market_recommendation_thresholds import (
    MarketRecommendationThresholds,
)
from src.models.market_snapshot import MarketSnapshot
from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.market_alert_analyzer import (
    MarketAlertAnalyzer,
)
from src.services.market_classifier import (
    MarketClassifier,
)
from src.services.market_movement_analyzer import (
    MarketMovementAnalyzer,
)
from src.services.market_recommendation_engine import (
    MarketRecommendationEngine,
)
from src.services.market_value_analyzer import (
    MarketValueAnalyzer,
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
            8,
            1,
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
    )


def classify_snapshot(
    *,
    odds: tuple[str, str, str],
    percentages: tuple[str, str, str],
) -> MarketClassificationReport:
    """Classify one current market without movement alerts."""

    snapshot = create_snapshot(
        hour=14,
        odds=odds,
        percentages=percentages,
    )
    value_analysis = MarketValueAnalyzer().analyze(
        snapshot.odds,
        snapshot.public_percentages,
    )

    return MarketClassifier().classify(
        value_analysis
    )


def create_sample_classification() -> MarketClassificationReport:
    """Create the standard classification with alerts."""

    earlier = create_snapshot(
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
    )
    later = create_snapshot(
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
    )

    movement = MarketMovementAnalyzer().analyze(
        earlier,
        later,
    )
    alert_report = MarketAlertAnalyzer().analyze(
        movement
    )

    return MarketClassifier().classify(
        movement.later_value_analysis,
        alert_report,
    )


def test_sample_recommends_favorite_and_value_challenger() -> None:
    recommendation = (
        MarketRecommendationEngine().recommend(
            create_sample_classification()
        )
    )

    assert recommendation.primary_outcome is Outcome.HOME
    assert recommendation.recommended_outcomes == (
        Outcome.HOME,
        Outcome.AWAY,
    )
    assert (
        recommendation.coverage
        is RecommendationCoverage.DOUBLE
    )
    assert recommendation.recommendation_symbols == "12"


def test_sample_is_high_risk() -> None:
    recommendation = (
        MarketRecommendationEngine().recommend(
            create_sample_classification()
        )
    )

    assert recommendation.risk_score == 8
    assert (
        recommendation.risk_level
        is RecommendationRiskLevel.HIGH
    )
    assert recommendation.is_spike_candidate is False


def test_sample_has_expected_risk_factors() -> None:
    recommendation = (
        MarketRecommendationEngine().recommend(
            create_sample_classification()
        )
    )

    assert recommendation.risk_factors == (
        RecommendationRiskFactor.PUBLIC_TRAP,
        RecommendationRiskFactor.VALUE_CHALLENGER,
        RecommendationRiskFactor
        .CONTRARIAN_CHALLENGER,
        RecommendationRiskFactor
        .SURGING_PUBLIC_TRAP,
    )


def test_strong_stable_favorite_becomes_single_candidate() -> None:
    classification = classify_snapshot(
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
    )

    recommendation = (
        MarketRecommendationEngine().recommend(
            classification
        )
    )

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


def test_weak_market_favorite_receives_guard() -> None:
    classification = classify_snapshot(
        odds=(
            "2.60",
            "3.20",
            "2.90",
        ),
        percentages=(
            "38",
            "31",
            "31",
        ),
    )

    recommendation = (
        MarketRecommendationEngine().recommend(
            classification
        )
    )

    assert recommendation.recommended_outcomes == (
        Outcome.HOME,
        Outcome.AWAY,
    )
    assert recommendation.requires_guard is True
    assert recommendation.has_risk_factor(
        RecommendationRiskFactor
        .WEAK_MARKET_FAVORITE
    )


def test_market_public_disagreement_includes_both() -> None:
    classification = classify_snapshot(
        odds=(
            "2.00",
            "3.50",
            "4.00",
        ),
        percentages=(
            "35",
            "25",
            "40",
        ),
    )

    recommendation = (
        MarketRecommendationEngine().recommend(
            classification
        )
    )

    assert recommendation.recommended_outcomes == (
        Outcome.HOME,
        Outcome.AWAY,
    )
    assert recommendation.has_risk_factor(
        RecommendationRiskFactor
        .FAVORITE_DISAGREEMENT
    )
    assert (
        recommendation.risk_level
        is RecommendationRiskLevel.MEDIUM
    )


def test_three_distinct_signals_create_full_cover() -> None:
    classification = classify_snapshot(
        odds=(
            "2.00",
            "3.50",
            "4.00",
        ),
        percentages=(
            "40",
            "45",
            "15",
        ),
    )

    recommendation = (
        MarketRecommendationEngine().recommend(
            classification
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


def test_custom_risk_thresholds_change_risk_level() -> None:
    classification = classify_snapshot(
        odds=(
            "2.60",
            "3.20",
            "2.90",
        ),
        percentages=(
            "38",
            "31",
            "31",
        ),
    )
    thresholds = MarketRecommendationThresholds(
        medium_risk_score=1,
        high_risk_score=2,
        extreme_risk_score=4,
    )

    recommendation = MarketRecommendationEngine(
        thresholds
    ).recommend(
        classification
    )

    assert recommendation.risk_score == 2
    assert (
        recommendation.risk_level
        is RecommendationRiskLevel.HIGH
    )


def test_engine_rejects_invalid_classification() -> None:
    with pytest.raises(
        TypeError,
        match="requires a MarketClassificationReport",
    ):
        MarketRecommendationEngine().recommend(
            object()  # type: ignore[arg-type]
        )