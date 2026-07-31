"""Thresholds for statistical and market comparisons."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class StatisticalMarketComparisonThresholds:
    """Contains agreement, conflict and model-value thresholds."""

    agreement_margin: Decimal = Decimal("3.00")
    disagreement_warning: Decimal = Decimal("5.00")
    disagreement_strong: Decimal = Decimal("10.00")
    model_value_threshold: Decimal = Decimal("3.00")
    strong_model_value_threshold: Decimal = Decimal("6.00")

    def __post_init__(self) -> None:
        """Normalize and validate all thresholds."""

        for field_name in (
            "agreement_margin",
            "disagreement_warning",
            "disagreement_strong",
            "model_value_threshold",
            "strong_model_value_threshold",
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
            self.agreement_margin
            < self.disagreement_warning
            < self.disagreement_strong
        ):
            raise ValueError(
                "Comparison thresholds must be ordered "
                "agreement, warning and strong."
            )

        if not (
            self.model_value_threshold
            < self.strong_model_value_threshold
        ):
            raise ValueError(
                "Model-value thresholds must be ordered "
                "value and strong value."
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