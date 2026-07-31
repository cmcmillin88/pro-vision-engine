"""Thresholds for market-based sign recommendations."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class MarketRecommendationThresholds:
    """Contains recommendation and risk thresholds."""

    confident_single_probability: Decimal = Decimal("55.00")
    weak_favorite_probability: Decimal = Decimal("45.00")
    single_negative_edge_limit: Decimal = Decimal("3.00")

    medium_risk_score: int = 3
    high_risk_score: int = 6
    extreme_risk_score: int = 9

    def __post_init__(self) -> None:
        """Normalize and validate all thresholds."""

        for field_name in (
            "confident_single_probability",
            "weak_favorite_probability",
            "single_negative_edge_limit",
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

        for field_name in (
            "confident_single_probability",
            "weak_favorite_probability",
        ):
            if getattr(
                self,
                field_name,
            ) > Decimal("100"):
                raise ValueError(
                    f"{field_name} must not exceed 100."
                )

        for field_name in (
            "medium_risk_score",
            "high_risk_score",
            "extreme_risk_score",
        ):
            value = getattr(
                self,
                field_name,
            )

            if isinstance(
                value,
                bool,
            ) or not isinstance(
                value,
                int,
            ):
                raise TypeError(
                    f"{field_name} must be an integer."
                )

            if value < 0:
                raise ValueError(
                    f"{field_name} must not be negative."
                )

        if not (
            self.medium_risk_score
            <= self.high_risk_score
            <= self.extreme_risk_score
        ):
            raise ValueError(
                "Risk score thresholds must be ordered "
                "medium, high and extreme."
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