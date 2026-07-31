"""Tests for football market alert models."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_alert import (
    MarketAlert,
    MarketAlertReport,
    MarketAlertSeverity,
    MarketAlertType,
)
from src.models.market_snapshot import MarketSnapshot
from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.market_movement_analyzer import (
    MarketMovementAnalyzer,
)


def create_movement_analysis():
    """Create a representative movement analysis."""

    earlier = MarketSnapshot(
        captured_at=datetime(
            2026,
            8,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        odds=ThreeWayOdds(
            Decimal("2.00"),
            Decimal("3.50"),
            Decimal("4.00"),
        ),
        public_percentages=ThreeWayPercentages(
            Decimal("55"),
            Decimal("25"),
            Decimal("20"),
        ),
    )
    later = MarketSnapshot(
        captured_at=datetime(
            2026,
            8,
            1,
            14,
            0,
            tzinfo=timezone.utc,
        ),
        odds=ThreeWayOdds(
            Decimal("1.80"),
            Decimal("3.80"),
            Decimal("4.50"),
        ),
        public_percentages=ThreeWayPercentages(
            Decimal("60"),
            Decimal("23"),
            Decimal("17"),
        ),
    )

    return MarketMovementAnalyzer().analyze(
        earlier,
        later,
    )


def create_alert(
    *,
    alert_type: MarketAlertType = (
        MarketAlertType.ODDS_STEAM
    ),
    severity: MarketAlertSeverity = (
        MarketAlertSeverity.WARNING
    ),
    outcome: Outcome = Outcome.HOME,
) -> MarketAlert:
    """Create one valid alert."""

    return MarketAlert(
        alert_type=alert_type,
        severity=severity,
        outcome=outcome,
        title="Odds steam",
        message="A significant market movement was detected.",
        metric_value=Decimal("1.00"),
        threshold=Decimal("0.50"),
    )


@pytest.mark.parametrize(
    ("severity", "expected_rank"),
    [
        (MarketAlertSeverity.INFO, 1),
        (MarketAlertSeverity.WARNING, 2),
        (MarketAlertSeverity.CRITICAL, 3),
    ],
)
def test_severity_has_expected_rank(
    severity: MarketAlertSeverity,
    expected_rank: int,
) -> None:
    assert severity.rank == expected_rank


def test_alert_normalizes_text() -> None:
    alert = MarketAlert(
        alert_type=MarketAlertType.ODDS_STEAM,
        severity=MarketAlertSeverity.WARNING,
        outcome=Outcome.HOME,
        title="  Odds steam  ",
        message="  Market support increased.  ",
        metric_value=Decimal("0.20"),
        threshold=Decimal("0.15"),
    )

    assert alert.title == "Odds steam"
    assert alert.message == "Market support increased."


def test_alert_rejects_invalid_metric_type() -> None:
    with pytest.raises(
        TypeError,
        match="metric_value",
    ):
        MarketAlert(
            alert_type=MarketAlertType.ODDS_STEAM,
            severity=MarketAlertSeverity.WARNING,
            outcome=Outcome.HOME,
            title="Odds steam",
            message="Market support increased.",
            metric_value="0.20",  # type: ignore[arg-type]
            threshold=Decimal("0.15"),
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "metric_value",
        "threshold",
    ],
)
def test_alert_rejects_non_finite_values(
    field_name: str,
) -> None:
    values = {
        "metric_value": Decimal("0.20"),
        "threshold": Decimal("0.15"),
    }
    values[field_name] = Decimal("NaN")

    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        MarketAlert(
            alert_type=MarketAlertType.ODDS_STEAM,
            severity=MarketAlertSeverity.WARNING,
            outcome=Outcome.HOME,
            title="Odds steam",
            message="Market support increased.",
            **values,
        )


def test_report_exposes_summary_properties() -> None:
    report = MarketAlertReport(
        movement_analysis=create_movement_analysis(),
        alerts=(
            create_alert(),
            create_alert(
                severity=MarketAlertSeverity.CRITICAL,
                outcome=Outcome.AWAY,
            ),
        ),
    )

    assert report.has_alerts is True
    assert (
        report.highest_severity
        is MarketAlertSeverity.CRITICAL
    )
    assert len(report.critical_alerts) == 1


def test_report_filters_by_outcome_and_type() -> None:
    home_alert = create_alert()
    away_alert = create_alert(
        alert_type=(
            MarketAlertType.CONTRARIAN_VALUE
        ),
        outcome=Outcome.AWAY,
    )
    report = MarketAlertReport(
        movement_analysis=create_movement_analysis(),
        alerts=(
            home_alert,
            away_alert,
        ),
    )

    assert report.for_outcome(
        Outcome.HOME
    ) == (home_alert,)
    assert report.by_type(
        MarketAlertType.CONTRARIAN_VALUE
    ) == (away_alert,)


def test_report_rejects_invalid_analysis() -> None:
    with pytest.raises(
        TypeError,
        match="movement_analysis",
    ):
        MarketAlertReport(
            movement_analysis=object(),  # type: ignore[arg-type]
            alerts=(),
        )