"""Result models for market movement analysis."""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from src.models.market_snapshot import MarketSnapshot
from src.models.market_value import MarketValueAnalysis
from src.models.movement_direction import (
    MovementDirection,
)
from src.models.outcome import Outcome


@dataclass(frozen=True, slots=True)
class OutcomeMovement:
    """Describes movement for one 1-X-2 outcome."""

    outcome: Outcome
    odds_change: Decimal
    market_probability_change: Decimal
    public_percentage_change: Decimal
    edge_change: Decimal

    def __post_init__(self) -> None:
        """Validate one outcome movement."""

        if not isinstance(
            self.outcome,
            Outcome,
        ):
            raise TypeError(
                "OutcomeMovement outcome "
                "must be an Outcome."
            )

        for field_name in (
            "odds_change",
            "market_probability_change",
            "public_percentage_change",
            "edge_change",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                Decimal,
            ):
                raise TypeError(
                    f"{field_name} "
                    "must be a Decimal."
                )

            if not value.is_finite():
                raise ValueError(
                    f"{field_name} "
                    "must be finite."
                )

    @property
    def odds_direction(
        self,
    ) -> MovementDirection:
        """Return the direction of the odds movement."""

        return MovementDirection.from_delta(
            self.odds_change
        )

    @property
    def market_probability_direction(
        self,
    ) -> MovementDirection:
        """Return the market-probability direction."""

        return MovementDirection.from_delta(
            self.market_probability_change
        )

    @property
    def public_percentage_direction(
        self,
    ) -> MovementDirection:
        """Return the public-percentage direction."""

        return MovementDirection.from_delta(
            self.public_percentage_change
        )

    @property
    def edge_direction(
        self,
    ) -> MovementDirection:
        """Return the value-edge direction."""

        return MovementDirection.from_delta(
            self.edge_change
        )

    @property
    def odds_shortened(self) -> bool:
        """Return whether the decimal odds became lower."""

        return self.odds_change < Decimal("0")

    @property
    def odds_drifted(self) -> bool:
        """Return whether the decimal odds became higher."""

        return self.odds_change > Decimal("0")


@dataclass(frozen=True, slots=True)
class MarketMovementAnalysis:
    """Complete comparison between two market snapshots."""

    earlier_snapshot: MarketSnapshot
    later_snapshot: MarketSnapshot
    earlier_value_analysis: MarketValueAnalysis
    later_value_analysis: MarketValueAnalysis
    outcome_movements: tuple[OutcomeMovement, ...]

    def __post_init__(self) -> None:
        """Validate the complete movement analysis."""

        if not isinstance(
            self.earlier_snapshot,
            MarketSnapshot,
        ):
            raise TypeError(
                "Earlier snapshot must be "
                "a MarketSnapshot."
            )

        if not isinstance(
            self.later_snapshot,
            MarketSnapshot,
        ):
            raise TypeError(
                "Later snapshot must be "
                "a MarketSnapshot."
            )

        if not isinstance(
            self.earlier_value_analysis,
            MarketValueAnalysis,
        ):
            raise TypeError(
                "Earlier value analysis must be "
                "a MarketValueAnalysis."
            )

        if not isinstance(
            self.later_value_analysis,
            MarketValueAnalysis,
        ):
            raise TypeError(
                "Later value analysis must be "
                "a MarketValueAnalysis."
            )

        if (
            self.later_snapshot.captured_at
            <= self.earlier_snapshot.captured_at
        ):
            raise ValueError(
                "Later market snapshot must be "
                "captured after the earlier snapshot."
            )

        outcome_order = tuple(
            movement.outcome
            for movement in self.outcome_movements
        )

        if outcome_order != Outcome.ordered():
            raise ValueError(
                "Market movements must follow "
                "official 1-X-2 order."
            )

    @property
    def elapsed_time(self) -> timedelta:
        """Return the time between the snapshots."""

        return (
            self.later_snapshot.captured_at
            - self.earlier_snapshot.captured_at
        )

    def for_outcome(
        self,
        outcome: Outcome,
    ) -> OutcomeMovement:
        """Return movement data for one outcome."""

        resolved_outcome = Outcome.parse(
            outcome
        )

        for movement in self.outcome_movements:
            if movement.outcome is resolved_outcome:
                return movement

        raise LookupError(
            f"No market movement exists for "
            f"{resolved_outcome.value}."
        )

    @property
    def strongest_market_probability_move(
        self,
    ) -> OutcomeMovement:
        """Return the largest absolute market-probability move."""

        return max(
            self.outcome_movements,
            key=lambda movement: abs(
                movement.market_probability_change
            ),
        )

    @property
    def strongest_public_percentage_move(
        self,
    ) -> OutcomeMovement:
        """Return the largest absolute public-percentage move."""

        return max(
            self.outcome_movements,
            key=lambda movement: abs(
                movement.public_percentage_change
            ),
        )