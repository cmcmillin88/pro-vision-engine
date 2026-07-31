"""Tests for rule-based football market alerts."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_alert import (
    MarketAlertSeverity,
    MarketAlertType,
)
from src.models.market_alert_thresholds import (
    MarketAlertThresholds,
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
from src.services.market_movement_analyzer import (
    MarketMovementAnalyzer,
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


def create_report(
    *,
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
    thresholds: MarketAlertThresholds | None = None,
):
    """Create an alert report from two snapshots."""

    earlier = create_snapshot(
        hour=12,
        odds=earlier_odds,
        percentages=earlier_percentages,
    )
    later = create_snapshot(
        hour=14,
        odds=later_odds,
        percentages=later_percentages,
    )
    movement_analysis = (
        MarketMovementAnalyzer().analyze(
            earlier,
            later,
        )
    )

    return MarketAlertAnalyzer(
        thresholds
    ).analyze(
        movement_analysis
    )


def test_sample_report_has_deterministic_alert_order() -> None:
    report = create_report()

    assert tuple(
        (
            alert.outcome,
            alert.alert_type,
        )
        for alert in report.alerts
    ) == (
        (
            Outcome.HOME,
            MarketAlertType.ODDS_STEAM,
        ),
        (
            Outcome.HOME,
            MarketAlertType.PUBLIC_SURGE,
        ),
        (
            Outcome.AWAY,
            MarketAlertType.CONTRARIAN_VALUE,
        ),
    )


def test_sample_odds_steam_is_warning() -> None:
    report = create_report()
    alert = report.by_type(
        MarketAlertType.ODDS_STEAM
    )[0]

    assert alert.outcome is Outcome.HOME
    assert (
        alert.severity
        is MarketAlertSeverity.WARNING
    )
    assert alert.metric_value == Decimal("0.20")


def test_sample_public_surge_is_warning() -> None:
    report = create_report()
    alert = report.by_type(
        MarketAlertType.PUBLIC_SURGE
    )[0]

    assert alert.outcome is Outcome.HOME
    assert (
        alert.severity
        is MarketAlertSeverity.WARNING
    )
    assert alert.metric_value == Decimal("5.00")


def test_sample_contrarian_value_is_warning() -> None:
    report = create_report()
    alert = report.by_type(
        MarketAlertType.CONTRARIAN_VALUE
    )[0]

    assert alert.outcome is Outcome.AWAY
    assert (
        alert.severity
        is MarketAlertSeverity.WARNING
    )
    assert alert.metric_value == Decimal("4.35")


def test_sample_report_exposes_warning_summary() -> None:
    report = create_report()

    assert report.has_alerts is True
    assert len(report.alerts) == 3
    assert (
        report.highest_severity
        is MarketAlertSeverity.WARNING
    )
    assert report.critical_alerts == ()


def test_strong_odds_steam_becomes_critical() -> None:
    report = create_report(
        earlier_odds=(
            "2.50",
            "3.20",
            "2.80",
        ),
        later_odds=(
            "1.70",
            "4.20",
            "5.00",
        ),
        earlier_percentages=(
            "40",
            "30",
            "30",
        ),
        later_percentages=(
            "40",
            "30",
            "30",
        ),
    )

    steam_alert = report.by_type(
        MarketAlertType.ODDS_STEAM
    )[0]

    assert (
        steam_alert.severity
        is MarketAlertSeverity.CRITICAL
    )


def test_large_public_surge_becomes_critical() -> None:
    report = create_report(
        earlier_odds=(
            "2.50",
            "3.20",
            "2.80",
        ),
        later_odds=(
            "2.50",
            "3.20",
            "2.80",
        ),
        earlier_percentages=(
            "40",
            "30",
            "30",
        ),
        later_percentages=(
            "50",
            "25",
            "25",
        ),
    )

    surge_alert = report.by_type(
        MarketAlertType.PUBLIC_SURGE
    )[0]

    assert (
        surge_alert.severity
        is MarketAlertSeverity.CRITICAL
    )


def test_value_erosion_generates_warning() -> None:
    report = create_report(
        earlier_odds=(
            "2.50",
            "3.20",
            "2.80",
        ),
        later_odds=(
            "2.50",
            "3.20",
            "2.80",
        ),
        earlier_percentages=(
            "40",
            "30",
            "30",
        ),
        later_percentages=(
            "43",
            "28",
            "29",
        ),
    )

    erosion_alert = report.by_type(
        MarketAlertType.VALUE_EROSION
    )[0]

    assert erosion_alert.outcome is Outcome.HOME
    assert (
        erosion_alert.severity
        is MarketAlertSeverity.WARNING
    )
    assert erosion_alert.metric_value == Decimal("3.00")


def test_large_value_erosion_becomes_critical() -> None:
    report = create_report(
        earlier_odds=(
            "2.50",
            "3.20",
            "2.80",
        ),
        later_odds=(
            "2.50",
            "3.20",
            "2.80",
        ),
        earlier_percentages=(
            "40",
            "30",
            "30",
        ),
        later_percentages=(
            "46",
            "27",
            "27",
        ),
    )

    erosion_alert = report.by_type(
        MarketAlertType.VALUE_EROSION
    )[0]

    assert (
        erosion_alert.severity
        is MarketAlertSeverity.CRITICAL
    )


def test_unchanged_market_generates_no_alerts() -> None:
    report = create_report(
        later_odds=(
            "2.00",
            "3.50",
            "4.00",
        ),
        later_percentages=(
            "55",
            "25",
            "20",
        ),
    )

    assert report.alerts == ()
    assert report.has_alerts is False
    assert report.highest_severity is None


def test_analyzer_rejects_invalid_movement_analysis() -> None:
    with pytest.raises(
        TypeError,
        match="requires a MarketMovementAnalysis",
    ):
        MarketAlertAnalyzer().analyze(
            object()  # type: ignore[arg-type]
        )


def test_custom_threshold_changes_alert_sensitivity() -> None:
    thresholds = MarketAlertThresholds(
        public_surge_warning=Decimal("1.00"),
        public_surge_critical=Decimal("3.00"),
    )
    report = create_report(
        earlier_odds=(
            "2.50",
            "3.20",
            "2.80",
        ),
        later_odds=(
            "2.50",
            "3.20",
            "2.80",
        ),
        earlier_percentages=(
            "40",
            "30",
            "30",
        ),
        later_percentages=(
            "41.5",
            "29.5",
            "29",
        ),
        thresholds=thresholds,
    )

    surge_alert = report.by_type(
        MarketAlertType.PUBLIC_SURGE
    )[0]

    assert (
        surge_alert.severity
        is MarketAlertSeverity.WARNING
    )
    assert surge_alert.metric_value == Decimal("1.50")