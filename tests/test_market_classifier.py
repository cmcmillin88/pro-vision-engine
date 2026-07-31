"""Tests for football pool market classification."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_alert import (
    MarketAlertReport,
)
from src.models.market_classification import (
    MarketRole,
)
from src.models.market_classification_thresholds import (
    MarketClassificationThresholds,
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


def create_sample_data():
    """Create the standard value analysis and alert report."""

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

    return (
        movement.later_value_analysis,
        alert_report,
    )


def test_sample_classification_has_deterministic_roles() -> None:
    value_analysis, alert_report = create_sample_data()

    report = MarketClassifier().classify(
        value_analysis,
        alert_report,
    )

    assert report.for_outcome(
        Outcome.HOME
    ).roles == (
        MarketRole.MARKET_FAVORITE,
        MarketRole.PUBLIC_FAVORITE,
        MarketRole.PUBLIC_TRAP,
        MarketRole.ODDS_STEAM,
        MarketRole.PUBLIC_SURGE,
    )

    assert report.for_outcome(
        Outcome.DRAW
    ).roles == ()

    assert report.for_outcome(
        Outcome.AWAY
    ).roles == (
        MarketRole.VALUE_PLAY,
        MarketRole.CONTRARIAN_VALUE,
    )


def test_sample_identifies_market_and_public_favorite() -> None:
    value_analysis, alert_report = create_sample_data()

    report = MarketClassifier().classify(
        value_analysis,
        alert_report,
    )

    assert (
        report.market_favorite.outcome
        is Outcome.HOME
    )
    assert (
        report.public_favorite.outcome
        is Outcome.HOME
    )
    assert report.market_and_public_agree is True


def test_sample_identifies_public_trap() -> None:
    value_analysis, alert_report = create_sample_data()

    report = MarketClassifier().classify(
        value_analysis,
        alert_report,
    )

    assert tuple(
        profile.outcome
        for profile in report.public_traps
    ) == (
        Outcome.HOME,
    )


def test_sample_identifies_value_play_and_best_value() -> None:
    value_analysis, alert_report = create_sample_data()

    report = MarketClassifier().classify(
        value_analysis,
        alert_report,
    )

    assert tuple(
        profile.outcome
        for profile in report.value_plays
    ) == (
        Outcome.AWAY,
    )
    assert report.best_value.outcome is Outcome.AWAY
    assert (
        report.best_value.edge_percentage_points
        == Decimal("4.35")
    )


def test_sample_maps_movement_alert_roles() -> None:
    value_analysis, alert_report = create_sample_data()

    report = MarketClassifier().classify(
        value_analysis,
        alert_report,
    )

    assert report.for_outcome(
        Outcome.HOME
    ).has_role(
        MarketRole.ODDS_STEAM
    )
    assert report.for_outcome(
        Outcome.HOME
    ).has_role(
        MarketRole.PUBLIC_SURGE
    )
    assert report.for_outcome(
        Outcome.AWAY
    ).has_role(
        MarketRole.CONTRARIAN_VALUE
    )


def test_classifier_works_without_alert_report() -> None:
    value_analysis, _ = create_sample_data()

    report = MarketClassifier().classify(
        value_analysis
    )

    home_roles = report.for_outcome(
        Outcome.HOME
    ).roles
    away_roles = report.for_outcome(
        Outcome.AWAY
    ).roles

    assert MarketRole.PUBLIC_TRAP in home_roles
    assert MarketRole.VALUE_PLAY in away_roles
    assert MarketRole.ODDS_STEAM not in home_roles
    assert (
        MarketRole.CONTRARIAN_VALUE
        not in away_roles
    )


def test_equal_market_uses_official_outcome_order() -> None:
    snapshot = create_snapshot(
        hour=14,
        odds=(
            "3.00",
            "3.00",
            "3.00",
        ),
        percentages=(
            "33.33",
            "33.33",
            "33.33",
        ),
    )
    value_analysis = MarketValueAnalyzer().analyze(
        snapshot.odds,
        snapshot.public_percentages,
    )

    report = MarketClassifier().classify(
        value_analysis
    )

    assert (
        report.market_favorite.outcome
        is Outcome.HOME
    )
    assert (
        report.public_favorite.outcome
        is Outcome.HOME
    )


def test_custom_thresholds_change_classification() -> None:
    value_analysis, alert_report = create_sample_data()

    thresholds = MarketClassificationThresholds(
        value_play_edge=Decimal("5.00"),
        public_trap_public_minimum=Decimal("50"),
        public_trap_negative_edge=Decimal("7.00"),
    )
    report = MarketClassifier(
        thresholds
    ).classify(
        value_analysis,
        alert_report,
    )

    assert report.value_plays == ()
    assert report.public_traps == ()


def test_classifier_rejects_mismatched_alert_report() -> None:
    value_analysis, alert_report = create_sample_data()

    earlier_value_analysis = (
        alert_report
        .movement_analysis
        .earlier_value_analysis
    )

    with pytest.raises(
        ValueError,
        match="same latest market",
    ):
        MarketClassifier().classify(
            earlier_value_analysis,
            alert_report,
        )


def test_classifier_rejects_invalid_value_analysis() -> None:
    with pytest.raises(
        TypeError,
        match="requires a MarketValueAnalysis",
    ):
        MarketClassifier().classify(
            object()  # type: ignore[arg-type]
        )


def test_classifier_rejects_invalid_alert_report() -> None:
    value_analysis, _ = create_sample_data()

    with pytest.raises(
        TypeError,
        match="MarketAlertReport or None",
    ):
        MarketClassifier().classify(
            value_analysis,
            object(),  # type: ignore[arg-type]
        )