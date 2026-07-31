"""Thresholds for statistical team-form comparisons."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class TeamFormComparisonThresholds:
    """Contains xG margins used to classify matchup edges."""

    balanced_xg_margin: Decimal = Decimal("0.20")
    clear_xg_margin: Decimal = Decimal("0.50")
    strong_xg_margin: Decimal = Decimal("1.00")

    def __post_init__(self) -> None:
        """Normalize and validate all comparison thresholds."""

        for field_name in (
            "balanced_xg_margin",
            "clear_xg_margin",
            "strong_xg_margin",
        ):
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

        if not (
            self.balanced_xg_margin
            < self.clear_xg_margin
            < self.strong_xg_margin
        ):
            raise ValueError(
                "xG margins must be ordered "
                "balanced, clear and strong."
            )

    @staticmethod
    def _to_decimal(
        value: object,
        *,
        field_name: str,
    ) -> Decimal:
        """Convert one threshold to a finite Decimal."""

        if isinstance(
            value,
            bool,
        ):
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