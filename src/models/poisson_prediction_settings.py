"""Configuration for Poisson football predictions."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class PoissonPredictionSettings:
    """Contains score-matrix and probability-mass settings."""

    maximum_goals: int = 10
    minimum_included_mass: Decimal = Decimal("99.00")

    def __post_init__(self) -> None:
        """Normalize and validate all settings."""

        if isinstance(
            self.maximum_goals,
            bool,
        ) or not isinstance(
            self.maximum_goals,
            int,
        ):
            raise TypeError(
                "maximum_goals must be an integer."
            )

        if not (
            1
            <= self.maximum_goals
            <= 30
        ):
            raise ValueError(
                "maximum_goals must be "
                "between 1 and 30."
            )

        minimum_mass = self._to_decimal(
            self.minimum_included_mass,
            field_name="minimum_included_mass",
        )

        if not (
            Decimal("0")
            <= minimum_mass
            <= Decimal("100")
        ):
            raise ValueError(
                "minimum_included_mass must be "
                "between 0 and 100."
            )

        object.__setattr__(
            self,
            "minimum_included_mass",
            minimum_mass,
        )

    @staticmethod
    def _to_decimal(
        value: object,
        *,
        field_name: str,
    ) -> Decimal:
        """Convert one setting to a finite Decimal."""

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