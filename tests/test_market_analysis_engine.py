"""Tests for the complete market analysis engine."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.models.market_alert import (
    MarketAlertSeverity,
    MarketAlertType,
)
from src.models.market_alert_thresholds import (
    MarketAlertThresholds,
)
from src.models.market_analysis import MarketAnalysisReport
from src.models.market_classification import MarketRole
from src.models.market_recommendation import (
    RecommendationCoverage,
    RecommendationRiskLevel,
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
from src.services.market_analysis_engine import (
    MarketAnalysisEngine,
)


def create_snapshot(
    *,
    hour: int,
    odds: tuple[str, str, str],
    percentages: tuple[str, str, str],
    source_name: str = "combined-market",
) -> MarketSnapshot:
    """Create one configurable test snapshot."""

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
        source_name=source_name,
    )


def create_sample_snapshots() -> tuple[
    MarketSnapshot,
    MarketSnapshot,
]:
    """Create the standard earlier and later markets."""

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

    return earlier, later


def test_engine_builds_complete_analysis_report() -> None:
    earlier, later = create_sample_snapshots()

    report = MarketAnalysisEngine().analyze(
        earlier,
        later,
    )

    assert isinstance(
        report,
        MarketAnalysisReport,
    )
    assert (
        report.alert_report.movement_analysis
        == report.movement_analysis
    )
    assert (
        report.classification_report.value_analysis
        == report.latest_value_analysis
    )
    assert (
        report.recommendation.classification_report
        == report.classification_report
    )


def test_engine_returns_expected_recommendation() -> None:
    earlier, later = create_sample_snapshots()

    report = MarketAnalysisEngine().analyze(
        earlier,
        later,
    )

    assert report.primary_outcome is Outcome.HOME
    assert report.recommended_outcomes == (
        Outcome.HOME,
        Outcome.AWAY,
    )
    assert report.recommendation_symbols == "12"
    assert (
        report.recommendation.coverage
        is RecommendationCoverage.DOUBLE
    )
    assert (
        report.risk_level
        is RecommendationRiskLevel.HIGH
    )
    assert report.risk_score == 8


def test_engine_returns_expected_alerts_and_roles() -> None:
    earlier, later = create_sample_snapshots()

    report = MarketAnalysisEngine().analyze(
        earlier,
        later,
    )

    assert len(report.alerts) == 3
    assert tuple(
        alert.alert_type
        for alert in report.alerts
    ) == (
        MarketAlertType.ODDS_STEAM,
        MarketAlertType.PUBLIC_SURGE,
        MarketAlertType.CONTRARIAN_VALUE,
    )
    assert report.classification_report.for_outcome(
        Outcome.HOME
    ).has_role(
        MarketRole.PUBLIC_TRAP
    )
    assert report.classification_report.for_outcome(
        Outcome.AWAY
    ).has_role(
        MarketRole.VALUE_PLAY
    )


def test_engine_preserves_snapshots_and_elapsed_time() -> None:
    earlier, later = create_sample_snapshots()

    report = MarketAnalysisEngine().analyze(
        earlier,
        later,
    )

    assert report.earlier_snapshot is earlier
    assert report.latest_snapshot is later
    assert report.elapsed_time == timedelta(
        hours=2
    )


def test_strong_stable_favorite_becomes_spike_candidate() -> None:
    earlier = create_snapshot(
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
    )
    later = create_snapshot(
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
    )

    report = MarketAnalysisEngine().analyze(
        earlier,
        later,
    )

    assert report.recommended_outcomes == (
        Outcome.HOME,
    )
    assert (
        report.recommendation.coverage
        is RecommendationCoverage.SINGLE
    )
    assert (
        report.risk_level
        is RecommendationRiskLevel.LOW
    )
    assert report.risk_score == 0
    assert report.is_spike_candidate is True


def test_engine_accepts_custom_alert_analyzer() -> None:
    earlier, later = create_sample_snapshots()
    thresholds = MarketAlertThresholds(
        public_surge_warning=Decimal("1.00"),
        public_surge_critical=Decimal("3.00"),
    )
    engine = MarketAnalysisEngine(
        alert_analyzer=MarketAlertAnalyzer(
            thresholds
        )
    )

    report = engine.analyze(
        earlier,
        later,
    )

    public_alert = (
        report.alert_report.by_type(
            MarketAlertType.PUBLIC_SURGE
        )[0]
    )

    assert (
        public_alert.severity
        is MarketAlertSeverity.CRITICAL
    )
    assert report.has_critical_alerts is True


def test_engine_rejects_invalid_earlier_snapshot() -> None:
    _, later = create_sample_snapshots()

    with pytest.raises(
        TypeError,
        match="Earlier snapshot",
    ):
        MarketAnalysisEngine().analyze(
            object(),  # type: ignore[arg-type]
            later,
        )


def test_engine_rejects_invalid_later_snapshot() -> None:
    earlier, _ = create_sample_snapshots()

    with pytest.raises(
        TypeError,
        match="Later snapshot",
    ):
        MarketAnalysisEngine().analyze(
            earlier,
            object(),  # type: ignore[arg-type]
        )


def test_engine_rejects_non_chronological_snapshots() -> None:
    earlier, later = create_sample_snapshots()
    invalid_later = MarketSnapshot(
        captured_at=earlier.captured_at,
        odds=later.odds,
        public_percentages=(
            later.public_percentages
        ),
        source_name=later.source_name,
    )

    with pytest.raises(
        ValueError,
        match="captured after",
    ):
        MarketAnalysisEngine().analyze(
            earlier,
            invalid_later,
        )


def test_engine_rejects_different_sources() -> None:
    earlier, _ = create_sample_snapshots()
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
        source_name="other-market",
    )

    with pytest.raises(
        ValueError,
        match="same source name",
    ):
        MarketAnalysisEngine().analyze(
            earlier,
            later,
        )