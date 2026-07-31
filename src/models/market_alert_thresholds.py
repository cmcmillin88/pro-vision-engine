"""Configurable thresholds for football market alerts."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class MarketAlertThresholds:
    """Contains all thresholds used by market alert rules."""

    odds_shortening_warning: Decimal = Decimal("0.15")
    odds_shortening_critical: Decimal = Decimal("0.30")

    market_probability_gain_warning: Decimal = Decimal("2.50")
    market_probability_gain_critical: Decimal = Decimal("5.00")

    public_surge_warning: Decimal = Decimal("4.00")
    public_surge_critical: Decimal = Decimal("8.00")

    value_erosion_warning: Decimal = Decimal("2.00")
    value_erosion_critical: Decimal = Decimal("5.00")

    contrarian_edge_warning: Decimal = Decimal("3.00")
    contrarian_edge_critical: Decimal = Decimal("6.00")
    contrarian_public_drop: Decimal = Decimal("2.00")
    contrarian_odds_drift: Decimal = Decimal("0.15")

    _field_names: ClassVar[tuple[str, ...]] = (
        "odds_shortening_warning",
        "odds_shortening_critical",
        "market_probability_gain_warning",
        "market_probability_gain_critical",
        "public_surge_warning",
        "public_surge_critical",
        "value_erosion_warning",
        "value_erosion_critical",
        "contrarian_edge_warning",
        "contrarian_edge_critical",
        "contrarian_public_drop",
        "contrarian_odds_drift",
    )

    _severity_pairs: ClassVar[
        tuple[tuple[str, str], ...]
    ] = (
        (
            "odds_shortening_warning",
            "odds_shortening_critical",
        ),
        (
            "market_probability_gain_warning",
            "market_probability_gain_critical",
        ),
        (
            "public_surge_warning",
            "public_surge_critical",
        ),
        (
            "value_erosion_warning",
            "value_erosion_critical",
        ),
        (
            "contrarian_edge_warning",
            "contrarian_edge_critical",
        ),
    )

    def __post_init__(self) -> None:
        """Normalize and validate all threshold values."""

        for field_name in self._field_names:
            value = self._to_decimal(
                getattr(
                    self,
                    field_name,
                ),
                field_name=field_name,
            )

            if value < Decimal("0"):
                raise ValueError(
                    f"{field_name} must not be negative."
                )

            object.__setattr__(
                self,
                field_name,
                value,
            )

        for (
            warning_field,
            critical_field,
        ) in self._severity_pairs:
            warning_value = getattr(
                self,
                warning_field,
            )
            critical_value = getattr(
                self,
                critical_field,
            )

            if critical_value < warning_value:
                raise ValueError(
                    f"{critical_field} must be greater than "
                    f"or equal to {warning_field}."
                )

    @staticmethod
    def _to_decimal(
        value: object,
        *,
        field_name: str,
    ) -> Decimal:
        """Convert one threshold to a finite Decimal."""

        if isinstance(value, bool):
            raise TypeError(
                f"{field_name} must be numeric."
            )

        try:
            decimal_value = Decimal(
                str(value)
            )
        except (
            InvalidOperation,
            ValueError,
        ) as error:
            raise TypeError(
                f"{field_name} must be numeric."
            ) from error

        if not decimal_value.is_finite():
            raise ValueError(
                f"{field_name} must be finite."
            )

        return decimal_value