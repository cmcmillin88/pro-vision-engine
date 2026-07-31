"""Tests for market recommendation models."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_recommendation import (
    MatchRecommendation,
    RecommendationCoverage,
    RecommendationRiskFactor,
    RecommendationRiskLevel,
)
from src.models.market_snapshot import MarketSnapshot
from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.market_classifier import (
    MarketClassifier,
)
from src.services.market_value_analyzer import (
    MarketValueAnalyzer,
)


def create_classification_report():
    """Create a stable representative classification."""

    snapshot = MarketSnapshot(
        captured_at=datetime(
            2026,
            8,
            1,
            14,
            0,
            tzinfo=timezone.utc,
        ),
        odds=ThreeWayOdds(
            Decimal("2.00"),
            Decimal("3.50"),
            Decimal("4.00"),
        ),
        public_percentages=ThreeWayPercentages(
            Decimal("48"),
            Decimal("28"),
            Decimal("24"),
        ),
    )
    value_analysis = MarketValueAnalyzer().analyze(
        snapshot.odds,
        snapshot.public_percentages,
    )

    return MarketClassifier().classify(
        value_analysis
    )


def create_recommendation() -> MatchRecommendation:
    """Create one valid double recommendation."""

    return MatchRecommendation(
        classification_report=(
            create_classification_report()
        ),
        primary_outcome=Outcome.HOME,
        recommended_outcomes=(
            Outcome.HOME,
            Outcome.AWAY,
        ),
        coverage=RecommendationCoverage.DOUBLE,
        risk_level=RecommendationRiskLevel.LOW,
        risk_score=2,
        risk_factors=(
            RecommendationRiskFactor
            .WEAK_MARKET_FAVORITE,
        ),
    )


@pytest.mark.parametrize(
    ("sign_count", "expected_coverage"),
    [
        (
            1,
            RecommendationCoverage.SINGLE,
        ),
        (
            2,
            RecommendationCoverage.DOUBLE,
        ),
        (
            3,
            RecommendationCoverage.TRIPLE,
        ),
    ],
)
def test_coverage_is_resolved_from_sign_count(
    sign_count: int,
    expected_coverage: RecommendationCoverage,
) -> None:
    assert (
        RecommendationCoverage.from_sign_count(
            sign_count
        )
        is expected_coverage
    )


def test_coverage_rejects_invalid_sign_count() -> None:
    with pytest.raises(
        ValueError,
        match="must be 1, 2 or 3",
    ):
        RecommendationCoverage.from_sign_count(
            4
        )


@pytest.mark.parametrize(
    ("risk_factor", "expected_weight"),
    [
        (
            RecommendationRiskFactor.PUBLIC_TRAP,
            3,
        ),
        (
            RecommendationRiskFactor
            .FAVORITE_DISAGREEMENT,
            3,
        ),
        (
            RecommendationRiskFactor
            .WEAK_MARKET_FAVORITE,
            2,
        ),
        (
            RecommendationRiskFactor
            .VALUE_CHALLENGER,
            2,
        ),
        (
            RecommendationRiskFactor.VALUE_EROSION,
            2,
        ),
        (
            RecommendationRiskFactor
            .CONTRARIAN_CHALLENGER,
            2,
        ),
        (
            RecommendationRiskFactor
            .SURGING_PUBLIC_TRAP,
            1,
        ),
    ],
)
def test_risk_factors_have_expected_weights(
    risk_factor: RecommendationRiskFactor,
    expected_weight: int,
) -> None:
    assert risk_factor.weight == expected_weight


def test_recommendation_exposes_helpers() -> None:
    recommendation = create_recommendation()

    assert recommendation.recommendation_symbols == "12"
    assert recommendation.secondary_outcomes == (
        Outcome.AWAY,
    )
    assert recommendation.requires_guard is True
    assert recommendation.is_full_cover is False
    assert recommendation.is_spike_candidate is False
    assert recommendation.has_risk_factor(
        RecommendationRiskFactor
        .WEAK_MARKET_FAVORITE
    )


def test_recommendation_rejects_unordered_outcomes() -> None:
    with pytest.raises(
        ValueError,
        match="official 1-X-2 order",
    ):
        MatchRecommendation(
            classification_report=(
                create_classification_report()
            ),
            primary_outcome=Outcome.HOME,
            recommended_outcomes=(
                Outcome.AWAY,
                Outcome.HOME,
            ),
            coverage=RecommendationCoverage.DOUBLE,
            risk_level=RecommendationRiskLevel.LOW,
            risk_score=0,
            risk_factors=(),
        )


def test_recommendation_rejects_coverage_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="coverage does not match",
    ):
        MatchRecommendation(
            classification_report=(
                create_classification_report()
            ),
            primary_outcome=Outcome.HOME,
            recommended_outcomes=(
                Outcome.HOME,
                Outcome.AWAY,
            ),
            coverage=RecommendationCoverage.SINGLE,
            risk_level=RecommendationRiskLevel.LOW,
            risk_score=0,
            risk_factors=(),
        )


def test_recommendation_rejects_risk_score_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="Risk score must equal",
    ):
        MatchRecommendation(
            classification_report=(
                create_classification_report()
            ),
            primary_outcome=Outcome.HOME,
            recommended_outcomes=(
                Outcome.HOME,
            ),
            coverage=RecommendationCoverage.SINGLE,
            risk_level=RecommendationRiskLevel.LOW,
            risk_score=10,
            risk_factors=(),
        )


def test_recommendation_rejects_duplicate_risk_factors() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain duplicates",
    ):
        MatchRecommendation(
            classification_report=(
                create_classification_report()
            ),
            primary_outcome=Outcome.HOME,
            recommended_outcomes=(
                Outcome.HOME,
            ),
            coverage=RecommendationCoverage.SINGLE,
            risk_level=RecommendationRiskLevel.MEDIUM,
            risk_score=6,
            risk_factors=(
                RecommendationRiskFactor.PUBLIC_TRAP,
                RecommendationRiskFactor.PUBLIC_TRAP,
            ),
        )