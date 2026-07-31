"""Thresholds for final statistical and market recommendations."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class IntegratedRecommendationThresholds:
    """Contains weights, sign thresholds and risk thresholds."""

    statistical_weight: Decimal = Decimal("0.60")
    market_weight: Decimal = Decimal("0.40")

    confident_single_probability: Decimal = Decimal("55.00")
    confident_single_margin: Decimal = Decimal("12.00")

    model_value_guard: Decimal = Decimal("3.00")
    strong_model_value_guard: Decimal = Decimal("6.00")

    weak_combined_favorite: Decimal = Decimal("45.00")
    narrow_combined_margin: Decimal = Decimal("5.00")

    medium_risk_score: int = 3
    high_risk_score: int = 6
    extreme_risk_score: int = 9

    def __post_init__(self) -> None:
        """Normalize and validate all thresholds."""

        decimal_fields = (
            "statistical_weight",
            "market_weight",
            "confident_single_probability",
            "confident_single_margin",
            "model_value_guard",
            "strong_model_value_guard",
            "weak_combined_favorite",
            "narrow_combined_margin",
        )

        for field_name in decimal_fields:
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
            "statistical_weight",
            "market_weight",
        ):
            if getattr(
                self,
                field_name,
            ) > Decimal("1"):
                raise ValueError(
                    f"{field_name} must not exceed 1."
                )

        if (
            self.statistical_weight
            + self.market_weight
            != Decimal("1")
        ):
            raise ValueError(
                "Statistical and market weights "
                "must total exactly 1."
            )

        for field_name in (
            "confident_single_probability",
            "confident_single_margin",
            "weak_combined_favorite",
            "narrow_combined_margin",
        ):
            if getattr(
                self,
                field_name,
            ) > Decimal("100"):
                raise ValueError(
                    f"{field_name} must not exceed 100."
                )

        if not (
            self.model_value_guard
            < self.strong_model_value_guard
        ):
            raise ValueError(
                "Model-value guard thresholds must be "
                "ordered value and strong value."
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
                "Risk thresholds must be ordered "
                "medium, high and extreme."
            )

    @staticmethod
    def _to_decimal(
        value: object,
        *,
        field_name: str,
    ) -> Decimal:
        """Convert one value to a finite Decimal."""

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