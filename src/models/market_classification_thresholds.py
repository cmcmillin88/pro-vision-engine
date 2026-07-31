"""Thresholds for market role classification."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class MarketClassificationThresholds:
    """Contains thresholds for value and public-trap roles."""

    value_play_edge: Decimal = Decimal("3.00")
    public_trap_public_minimum: Decimal = Decimal("50.00")
    public_trap_negative_edge: Decimal = Decimal("5.00")

    def __post_init__(self) -> None:
        """Normalize and validate all classification thresholds."""

        for field_name in (
            "value_play_edge",
            "public_trap_public_minimum",
            "public_trap_negative_edge",
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

        if (
            self.public_trap_public_minimum
            > Decimal("100")
        ):
            raise ValueError(
                "public_trap_public_minimum "
                "must not exceed 100."
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