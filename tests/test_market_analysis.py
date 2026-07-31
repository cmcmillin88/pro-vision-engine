"""Tests for the complete market analysis result."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_alert import MarketAlertReport
from src.models.market_analysis import MarketAnalysisReport
from src.models.market_snapshot import MarketSnapshot
from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.market_alert_analyzer import (
    MarketAlertAnalyzer,
)
from src.services.market_classifier import MarketClassifier
from src.services.market_movement_analyzer import (
    MarketMovementAnalyzer,
)
from src.services.market_recommendation_engine import (
    MarketRecommendationEngine,
)


def create_snapshot(
    *,
    hour: int,
    odds: tuple[str, str, str],
    percentages: tuple[str, str, str],
) -> MarketSnapshot:
    """Create one test market snapshot."""

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


def create_components():
    """Create one complete linked analysis chain."""

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
    alerts = MarketAlertAnalyzer().analyze(
        movement
    )
    classification = MarketClassifier().classify(
        movement.later_value_analysis,
        alerts,
    )
    recommendation = (
        MarketRecommendationEngine().recommend(
            classification
        )
    )

    return (
        movement,
        alerts,
        classification,
        recommendation,
    )


def create_report() -> MarketAnalysisReport:
    """Create one valid complete report."""

    (
        movement,
        alerts,
        classification,
        recommendation,
    ) = create_components()

    return MarketAnalysisReport(
        movement_analysis=movement,
        alert_report=alerts,
        classification_report=classification,
        recommendation=recommendation,
    )


def test_report_exposes_complete_component_chain() -> None:
    report = create_report()

    assert (
        report.alert_report.movement_analysis
        == report.movement_analysis
    )
    assert (
        report.classification_report.alert_report
        == report.alert_report
    )
    assert (
        report.recommendation.classification_report
        == report.classification_report
    )


def test_report_exposes_recommendation_summary() -> None:
    report = create_report()

    assert report.primary_outcome is Outcome.HOME
    assert report.recommended_outcomes == (
        Outcome.HOME,
        Outcome.AWAY,
    )
    assert report.recommendation_symbols == "12"
    assert report.risk_score == 8
    assert report.is_spike_candidate is False


def test_report_exposes_market_summary() -> None:
    report = create_report()

    assert report.market_favorite.outcome is Outcome.HOME
    assert report.public_favorite.outcome is Outcome.HOME
    assert report.best_value.outcome is Outcome.AWAY
    assert tuple(
        profile.outcome
        for profile in report.public_traps
    ) == (
        Outcome.HOME,
    )
    assert tuple(
        profile.outcome
        for profile in report.value_plays
    ) == (
        Outcome.AWAY,
    )


def test_report_rejects_invalid_movement_analysis() -> None:
    (
        _,
        alerts,
        classification,
        recommendation,
    ) = create_components()

    with pytest.raises(
        TypeError,
        match="movement_analysis",
    ):
        MarketAnalysisReport(
            movement_analysis=object(),  # type: ignore[arg-type]
            alert_report=alerts,
            classification_report=classification,
            recommendation=recommendation,
        )


def test_report_rejects_mismatched_alert_report() -> None:
    (
        movement,
        _,
        classification,
        recommendation,
    ) = create_components()

    other_earlier = create_snapshot(
        hour=15,
        odds=(
            "2.20",
            "3.40",
            "3.70",
        ),
        percentages=(
            "45",
            "30",
            "25",
        ),
    )
    other_later = create_snapshot(
        hour=16,
        odds=(
            "2.10",
            "3.50",
            "3.90",
        ),
        percentages=(
            "47",
            "29",
            "24",
        ),
    )
    other_movement = (
        MarketMovementAnalyzer().analyze(
            other_earlier,
            other_later,
        )
    )
    other_alerts = MarketAlertReport(
        movement_analysis=other_movement,
        alerts=(),
    )

    with pytest.raises(
        ValueError,
        match="same movement analysis",
    ):
        MarketAnalysisReport(
            movement_analysis=movement,
            alert_report=other_alerts,
            classification_report=classification,
            recommendation=recommendation,
        )


def test_report_rejects_mismatched_classification() -> None:
    (
        movement,
        alerts,
        _,
        recommendation,
    ) = create_components()

    earlier_classification = (
        MarketClassifier().classify(
            movement.earlier_value_analysis
        )
    )

    with pytest.raises(
        ValueError,
        match="latest value analysis",
    ):
        MarketAnalysisReport(
            movement_analysis=movement,
            alert_report=alerts,
            classification_report=(
                earlier_classification
            ),
            recommendation=recommendation,
        )


def test_report_rejects_mismatched_recommendation() -> None:
    (
        movement,
        alerts,
        classification,
        _,
    ) = create_components()

    earlier_classification = (
        MarketClassifier().classify(
            movement.earlier_value_analysis
        )
    )
    earlier_recommendation = (
        MarketRecommendationEngine().recommend(
            earlier_classification
        )
    )

    with pytest.raises(
        ValueError,
        match="supplied classification report",
    ):
        MarketAnalysisReport(
            movement_analysis=movement,
            alert_report=alerts,
            classification_report=classification,
            recommendation=earlier_recommendation,
        )