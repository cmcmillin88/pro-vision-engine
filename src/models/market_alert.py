"""Alert models for significant football market movements."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.models.market_movement import (
    MarketMovementAnalysis,
)
from src.models.outcome import Outcome


class MarketAlertSeverity(str, Enum):
    """Describes the importance of a market alert."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        """Return a sortable severity rank."""

        ranks = {
            MarketAlertSeverity.INFO: 1,
            MarketAlertSeverity.WARNING: 2,
            MarketAlertSeverity.CRITICAL: 3,
        }

        return ranks[self]


class MarketAlertType(str, Enum):
    """Describes the detected market signal."""

    ODDS_STEAM = "odds_steam"
    PUBLIC_SURGE = "public_surge"
    VALUE_EROSION = "value_erosion"
    CONTRARIAN_VALUE = "contrarian_value"


@dataclass(frozen=True, slots=True)
class MarketAlert:
    """Describes one detected market signal."""

    alert_type: MarketAlertType
    severity: MarketAlertSeverity
    outcome: Outcome
    title: str
    message: str
    metric_value: Decimal
    threshold: Decimal

    def __post_init__(self) -> None:
        """Validate and normalize the market alert."""

        if not isinstance(
            self.alert_type,
            MarketAlertType,
        ):
            raise TypeError(
                "MarketAlert alert_type must be "
                "a MarketAlertType."
            )

        if not isinstance(
            self.severity,
            MarketAlertSeverity,
        ):
            raise TypeError(
                "MarketAlert severity must be "
                "a MarketAlertSeverity."
            )

        if not isinstance(
            self.outcome,
            Outcome,
        ):
            raise TypeError(
                "MarketAlert outcome must be an Outcome."
            )

        for field_name in (
            "title",
            "message",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"MarketAlert {field_name} "
                    "must be a string."
                )

            normalized_value = value.strip()

            if not normalized_value:
                raise ValueError(
                    f"MarketAlert {field_name} "
                    "must not be empty."
                )

            object.__setattr__(
                self,
                field_name,
                normalized_value,
            )

        for field_name in (
            "metric_value",
            "threshold",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                Decimal,
            ):
                raise TypeError(
                    f"MarketAlert {field_name} "
                    "must be a Decimal."
                )

            if not value.is_finite():
                raise ValueError(
                    f"MarketAlert {field_name} "
                    "must be finite."
                )

            if value < Decimal("0"):
                raise ValueError(
                    f"MarketAlert {field_name} "
                    "must not be negative."
                )

    @property
    def is_critical(self) -> bool:
        """Return whether this is a critical alert."""

        return (
            self.severity
            is MarketAlertSeverity.CRITICAL
        )


@dataclass(frozen=True, slots=True)
class MarketAlertReport:
    """Contains all alerts generated from one movement analysis."""

    movement_analysis: MarketMovementAnalysis
    alerts: tuple[MarketAlert, ...]

    def __post_init__(self) -> None:
        """Validate the alert report."""

        if not isinstance(
            self.movement_analysis,
            MarketMovementAnalysis,
        ):
            raise TypeError(
                "MarketAlertReport movement_analysis "
                "must be a MarketMovementAnalysis."
            )

        if not isinstance(
            self.alerts,
            tuple,
        ):
            raise TypeError(
                "MarketAlertReport alerts must be a tuple."
            )

        for alert in self.alerts:
            if not isinstance(
                alert,
                MarketAlert,
            ):
                raise TypeError(
                    "MarketAlertReport may only "
                    "contain MarketAlert objects."
                )

    @property
    def has_alerts(self) -> bool:
        """Return whether any alert was generated."""

        return bool(self.alerts)

    @property
    def highest_severity(
        self,
    ) -> MarketAlertSeverity | None:
        """Return the highest severity in the report."""

        if not self.alerts:
            return None

        return max(
            (
                alert.severity
                for alert in self.alerts
            ),
            key=lambda severity: severity.rank,
        )

    @property
    def critical_alerts(
        self,
    ) -> tuple[MarketAlert, ...]:
        """Return all critical alerts."""

        return tuple(
            alert
            for alert in self.alerts
            if alert.is_critical
        )

    def for_outcome(
        self,
        outcome: Outcome,
    ) -> tuple[MarketAlert, ...]:
        """Return all alerts for one outcome."""

        resolved_outcome = Outcome.parse(
            outcome
        )

        return tuple(
            alert
            for alert in self.alerts
            if alert.outcome is resolved_outcome
        )

    def by_type(
        self,
        alert_type: MarketAlertType,
    ) -> tuple[MarketAlert, ...]:
        """Return all alerts of one type."""

        if not isinstance(
            alert_type,
            MarketAlertType,
        ):
            raise TypeError(
                "Alert type must be a MarketAlertType."
            )

        return tuple(
            alert
            for alert in self.alerts
            if alert.alert_type is alert_type
        )