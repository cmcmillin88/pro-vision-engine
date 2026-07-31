"""Value-analysis result models for football pool markets."""

from dataclasses import dataclass
from decimal import Decimal

from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)


@dataclass(frozen=True, slots=True)
class OutcomeValue:
    """Describes market value for one 1-X-2 outcome."""

    outcome: Outcome
    odds: Decimal
    market_probability: Decimal
    public_percentage: Decimal
    edge_percentage_points: Decimal
    value_index: Decimal | None

    def __post_init__(self) -> None:
        """Validate the calculated outcome value."""

        if not isinstance(self.outcome, Outcome):
            raise TypeError(
                "OutcomeValue outcome must be an Outcome."
            )

        if self.odds <= Decimal("1"):
            raise ValueError(
                "OutcomeValue odds must be greater than 1."
            )

        for field_name in (
            "market_probability",
            "public_percentage",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not Decimal("0") <= value <= Decimal("100"):
                raise ValueError(
                    f"{field_name} must be between 0 and 100."
                )

        if (
            self.value_index is not None
            and self.value_index < Decimal("0")
        ):
            raise ValueError(
                "value_index must not be negative."
            )

    @property
    def has_positive_value(self) -> bool:
        """Return whether market probability exceeds public support."""

        return (
            self.edge_percentage_points
            > Decimal("0")
        )


@dataclass(frozen=True, slots=True)
class MarketValueAnalysis:
    """Complete odds-versus-public analysis for one match."""

    odds: ThreeWayOdds
    public_percentages: ThreeWayPercentages
    market_probabilities: ThreeWayPercentages
    overround_percentage_points: Decimal
    outcome_values: tuple[OutcomeValue, ...]

    def __post_init__(self) -> None:
        """Validate the complete analysis structure."""

        if not isinstance(
            self.odds,
            ThreeWayOdds,
        ):
            raise TypeError(
                "MarketValueAnalysis odds must be ThreeWayOdds."
            )

        if not isinstance(
            self.public_percentages,
            ThreeWayPercentages,
        ):
            raise TypeError(
                "MarketValueAnalysis public percentages must be "
                "ThreeWayPercentages."
            )

        if not isinstance(
            self.market_probabilities,
            ThreeWayPercentages,
        ):
            raise TypeError(
                "MarketValueAnalysis market probabilities must be "
                "ThreeWayPercentages."
            )

        outcome_order = tuple(
            value.outcome
            for value in self.outcome_values
        )

        if outcome_order != Outcome.ordered():
            raise ValueError(
                "MarketValueAnalysis outcome values must follow "
                "official 1-X-2 order."
            )

    def for_outcome(
        self,
        outcome: Outcome,
    ) -> OutcomeValue:
        """Return the value assessment for one outcome."""

        resolved_outcome = Outcome.parse(outcome)

        for outcome_value in self.outcome_values:
            if outcome_value.outcome is resolved_outcome:
                return outcome_value

        raise LookupError(
            f"No value assessment exists for "
            f"{resolved_outcome.value}."
        )

    @property
    def best_value(self) -> OutcomeValue:
        """Return the outcome with the strongest percentage-point edge."""

        return max(
            self.outcome_values,
            key=lambda value: value.edge_percentage_points,
        )

    @property
    def positive_value_outcomes(
        self,
    ) -> tuple[OutcomeValue, ...]:
        """Return all outcomes with a positive market edge."""

        return tuple(
            value
            for value in self.outcome_values
            if value.has_positive_value
        )