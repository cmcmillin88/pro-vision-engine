"""Percentage distributions for 1-X-2 football markets."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from src.models.outcome import Outcome


@dataclass(frozen=True, slots=True)
class ThreeWayPercentages:
    """Stores a rounded percentage distribution for 1-X-2 outcomes."""

    home: Decimal
    draw: Decimal
    away: Decimal

    _minimum_total = Decimal("99")
    _maximum_total = Decimal("101")

    def __post_init__(self) -> None:
        """Normalize and validate all percentage values."""

        for field_name in (
            "home",
            "draw",
            "away",
        ):
            value = self._to_decimal(
                getattr(self, field_name),
                field_name=field_name,
            )

            if not Decimal("0") <= value <= Decimal("100"):
                raise ValueError(
                    f"{field_name.capitalize()} percentage "
                    "must be between 0 and 100."
                )

            object.__setattr__(
                self,
                field_name,
                value,
            )

        if not (
            self._minimum_total
            <= self.total
            <= self._maximum_total
        ):
            raise ValueError(
                "1-X-2 percentages must total between 99 and 101 "
                "to allow normal rounding differences."
            )

    @property
    def total(self) -> Decimal:
        """Return the total percentage."""

        return (
            self.home
            + self.draw
            + self.away
        )

    def for_outcome(
        self,
        outcome: Outcome,
    ) -> Decimal:
        """Return the percentage for one outcome."""

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
        """Return percentages in official 1-X-2 order."""

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
        """Convert one percentage value to a finite Decimal."""

        if isinstance(value, bool):
            raise TypeError(
                f"{field_name.capitalize()} percentage "
                "must be numeric."
            )

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise TypeError(
                f"{field_name.capitalize()} percentage "
                "must be numeric."
            ) from error

        if not decimal_value.is_finite():
            raise ValueError(
                f"{field_name.capitalize()} percentage "
                "must be finite."
            )

        return decimal_value