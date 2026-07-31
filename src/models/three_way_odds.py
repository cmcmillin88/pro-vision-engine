"""Decimal odds for 1-X-2 football markets."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from src.models.outcome import Outcome


@dataclass(frozen=True, slots=True)
class ThreeWayOdds:
    """Stores decimal odds for home, draw and away outcomes."""

    home: Decimal
    draw: Decimal
    away: Decimal

    def __post_init__(self) -> None:
        """Normalize and validate all decimal odds."""

        for field_name in (
            "home",
            "draw",
            "away",
        ):
            value = self._to_decimal(
                getattr(self, field_name),
                field_name=field_name,
            )

            if value <= Decimal("1"):
                raise ValueError(
                    f"{field_name.capitalize()} odds "
                    "must be greater than 1."
                )

            object.__setattr__(
                self,
                field_name,
                value,
            )

    def for_outcome(
        self,
        outcome: Outcome,
    ) -> Decimal:
        """Return the decimal odds for one outcome."""

        resolved_outcome = Outcome.parse(outcome)

        values = {
            Outcome.HOME: self.home,
            Outcome.DRAW: self.draw,
            Outcome.AWAY: self.away,
        }

        return values[resolved_outcome]

    def items(
        self,
    ) -> tuple[tuple[Outcome, Decimal], ...]:
        """Return odds in official 1-X-2 order."""

        return tuple(
            (
                outcome,
                self.for_outcome(outcome),
            )
            for outcome in Outcome.ordered()
        )

    @staticmethod
    def _to_decimal(
        value: object,
        *,
        field_name: str,
    ) -> Decimal:
        """Convert one odds value to a finite Decimal."""

        if isinstance(value, bool):
            raise TypeError(
                f"{field_name.capitalize()} odds "
                "must be numeric."
            )

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise TypeError(
                f"{field_name.capitalize()} odds "
                "must be numeric."
            ) from error

        if not decimal_value.is_finite():
            raise ValueError(
                f"{field_name.capitalize()} odds "
                "must be finite."
            )

        return decimal_value