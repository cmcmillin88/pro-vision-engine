"""Rule-based alert detection for football market movements."""

from decimal import Decimal

from src.models.market_alert import (
    MarketAlert,
    MarketAlertReport,
    MarketAlertSeverity,
    MarketAlertType,
)
from src.models.market_alert_thresholds import (
    MarketAlertThresholds,
)
from src.models.market_movement import (
    MarketMovementAnalysis,
    OutcomeMovement,
)
from src.models.market_value import OutcomeValue
from src.models.outcome import Outcome


class MarketAlertAnalyzer:
    """Detects significant odds, public and value movements."""

    def __init__(
        self,
        thresholds: MarketAlertThresholds | None = None,
    ) -> None:
        """Create the analyzer with configurable thresholds."""

        self._thresholds = (
            thresholds
            or MarketAlertThresholds()
        )

    def analyze(
        self,
        movement_analysis: MarketMovementAnalysis,
    ) -> MarketAlertReport:
        """Generate alerts from one market movement analysis."""

        if not isinstance(
            movement_analysis,
            MarketMovementAnalysis,
        ):
            raise TypeError(
                "MarketAlertAnalyzer requires "
                "a MarketMovementAnalysis."
            )

        alerts: list[MarketAlert] = []

        for outcome in Outcome.ordered():
            movement = movement_analysis.for_outcome(
                outcome
            )
            later_value = (
                movement_analysis
                .later_value_analysis
                .for_outcome(
                    outcome
                )
            )

            possible_alerts = (
                self._create_odds_steam_alert(
                    movement
                ),
                self._create_public_surge_alert(
                    movement
                ),
                self._create_value_erosion_alert(
                    movement
                ),
                self._create_contrarian_value_alert(
                    movement,
                    later_value,
                ),
            )

            alerts.extend(
                alert
                for alert in possible_alerts
                if alert is not None
            )

        return MarketAlertReport(
            movement_analysis=movement_analysis,
            alerts=tuple(alerts),
        )

    def _create_odds_steam_alert(
        self,
        movement: OutcomeMovement,
    ) -> MarketAlert | None:
        """Create an alert for strong market support."""

        shortening = abs(
            movement.odds_change
        )

        if (
            movement.odds_change
            > -self._thresholds.odds_shortening_warning
            or movement.market_probability_change
            < (
                self._thresholds
                .market_probability_gain_warning
            )
        ):
            return None

        is_critical = (
            shortening
            >= self._thresholds.odds_shortening_critical
            and movement.market_probability_change
            >= (
                self._thresholds
                .market_probability_gain_critical
            )
        )
        severity = (
            MarketAlertSeverity.CRITICAL
            if is_critical
            else MarketAlertSeverity.WARNING
        )
        threshold = (
            self._thresholds.odds_shortening_critical
            if is_critical
            else self._thresholds.odds_shortening_warning
        )

        return MarketAlert(
            alert_type=MarketAlertType.ODDS_STEAM,
            severity=severity,
            outcome=movement.outcome,
            title="Odds steam",
            message=(
                f"{movement.outcome.value} odds shortened by "
                f"{shortening} while normalized market "
                f"probability increased by "
                f"{movement.market_probability_change} "
                "percentage points."
            ),
            metric_value=shortening,
            threshold=threshold,
        )

    def _create_public_surge_alert(
        self,
        movement: OutcomeMovement,
    ) -> MarketAlert | None:
        """Create an alert for a strong public percentage rise."""

        public_change = (
            movement.public_percentage_change
        )

        if (
            public_change
            < self._thresholds.public_surge_warning
        ):
            return None

        is_critical = (
            public_change
            >= self._thresholds.public_surge_critical
        )
        severity = (
            MarketAlertSeverity.CRITICAL
            if is_critical
            else MarketAlertSeverity.WARNING
        )
        threshold = (
            self._thresholds.public_surge_critical
            if is_critical
            else self._thresholds.public_surge_warning
        )

        return MarketAlert(
            alert_type=MarketAlertType.PUBLIC_SURGE,
            severity=severity,
            outcome=movement.outcome,
            title="Public surge",
            message=(
                f"Public support for "
                f"{movement.outcome.value} increased by "
                f"{public_change} percentage points."
            ),
            metric_value=public_change,
            threshold=threshold,
        )

    def _create_value_erosion_alert(
        self,
        movement: OutcomeMovement,
    ) -> MarketAlert | None:
        """Create an alert when value deteriorates materially."""

        erosion = -movement.edge_change

        if (
            erosion
            < self._thresholds.value_erosion_warning
        ):
            return None

        is_critical = (
            erosion
            >= self._thresholds.value_erosion_critical
        )
        severity = (
            MarketAlertSeverity.CRITICAL
            if is_critical
            else MarketAlertSeverity.WARNING
        )
        threshold = (
            self._thresholds.value_erosion_critical
            if is_critical
            else self._thresholds.value_erosion_warning
        )

        return MarketAlert(
            alert_type=MarketAlertType.VALUE_EROSION,
            severity=severity,
            outcome=movement.outcome,
            title="Value erosion",
            message=(
                f"The value edge for "
                f"{movement.outcome.value} deteriorated by "
                f"{erosion} percentage points."
            ),
            metric_value=erosion,
            threshold=threshold,
        )

    def _create_contrarian_value_alert(
        self,
        movement: OutcomeMovement,
        later_value: OutcomeValue,
    ) -> MarketAlert | None:
        """Create an alert for improving contrarian pool value."""

        public_drop = -movement.public_percentage_change
        later_edge = later_value.edge_percentage_points

        if (
            movement.odds_change
            < self._thresholds.contrarian_odds_drift
            or public_drop
            < self._thresholds.contrarian_public_drop
            or later_edge
            < self._thresholds.contrarian_edge_warning
        ):
            return None

        is_critical = (
            later_edge
            >= self._thresholds.contrarian_edge_critical
        )
        severity = (
            MarketAlertSeverity.CRITICAL
            if is_critical
            else MarketAlertSeverity.WARNING
        )
        threshold = (
            self._thresholds.contrarian_edge_critical
            if is_critical
            else self._thresholds.contrarian_edge_warning
        )

        return MarketAlert(
            alert_type=(
                MarketAlertType.CONTRARIAN_VALUE
            ),
            severity=severity,
            outcome=movement.outcome,
            title="Contrarian value",
            message=(
                f"{movement.outcome.value} odds drifted by "
                f"{movement.odds_change}, public support fell "
                f"by {public_drop} percentage points and the "
                f"current value edge is {later_edge}."
            ),
            metric_value=max(
                later_edge,
                Decimal("0"),
            ),
            threshold=threshold,
        )