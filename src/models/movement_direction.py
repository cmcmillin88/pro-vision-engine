"""Direction values for market movements."""

from enum import Enum
from decimal import Decimal


class MovementDirection(str, Enum):
    """Describes whether a measured value moved up or down."""

    INCREASED = "increased"
    DECREASED = "decreased"
    UNCHANGED = "unchanged"

    @classmethod
    def from_delta(
        cls,
        delta: Decimal,
    ) -> "MovementDirection":
        """Resolve movement direction from a Decimal change."""

        if not isinstance(
            delta,
            Decimal,
        ):
            raise TypeError(
                "Movement delta must be a Decimal."
            )

        if delta > Decimal("0"):
            return cls.INCREASED

        if delta < Decimal("0"):
            return cls.DECREASED

        return cls.UNCHANGED