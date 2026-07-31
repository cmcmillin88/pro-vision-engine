"""Comparison service for time-stamped 1-X-2 markets."""

from decimal import Decimal, ROUND_HALF_UP

from src.models.market_movement import (
    MarketMovementAnalysis,
    OutcomeMovement,
)
from src.models.market_snapshot import MarketSnapshot
from src.models.outcome import Outcome
from src.services.market_value_analyzer import (
    MarketValueAnalyzer,
)


class MarketMovementAnalyzer:
    """Compares odds, probabilities, public support and value over time."""

    _quantum = Decimal("0.01")

    def __init__(
        self,
        value_analyzer: MarketValueAnalyzer | None = None,
    ) -> None:
        """Create the movement analyzer."""

        self._value_analyzer = (
            value_analyzer
            or MarketValueAnalyzer()
        )

    def analyze(
        self,
        earlier_snapshot: MarketSnapshot,
        later_snapshot: MarketSnapshot,
    ) -> MarketMovementAnalysis:
        """Compare an earlier market snapshot with a later one."""

        self._validate_snapshots(
            earlier_snapshot,
            later_snapshot,
        )

        earlier_value_analysis = (
            self._value_analyzer.analyze(
                earlier_snapshot.odds,
                earlier_snapshot.public_percentages,
            )
        )
        later_value_analysis = (
            self._value_analyzer.analyze(
                later_snapshot.odds,
                later_snapshot.public_percentages,
            )
        )

        outcome_movements = tuple(
            self._create_outcome_movement(
                outcome=outcome,
                earlier_snapshot=earlier_snapshot,
                later_snapshot=later_snapshot,
                earlier_value_analysis=(
                    earlier_value_analysis
                ),
                later_value_analysis=(
                    later_value_analysis
                ),
            )
            for outcome in Outcome.ordered()
        )

        return MarketMovementAnalysis(
            earlier_snapshot=earlier_snapshot,
            later_snapshot=later_snapshot,
            earlier_value_analysis=(
                earlier_value_analysis
            ),
            later_value_analysis=(
                later_value_analysis
            ),
            outcome_movements=outcome_movements,
        )

    def _create_outcome_movement(
        self,
        *,
        outcome: Outcome,
        earlier_snapshot: MarketSnapshot,
        later_snapshot: MarketSnapshot,
        earlier_value_analysis: object,
        later_value_analysis: object,
    ) -> OutcomeMovement:
        """Calculate movements for one outcome."""

        earlier_value = (
            earlier_value_analysis.for_outcome(  # type: ignore[attr-defined]
                outcome
            )
        )
        later_value = (
            later_value_analysis.for_outcome(  # type: ignore[attr-defined]
                outcome
            )
        )

        return OutcomeMovement(
            outcome=outcome,
            odds_change=self._round(
                later_snapshot.odds.for_outcome(
                    outcome
                )
                - earlier_snapshot.odds.for_outcome(
                    outcome
                )
            ),
            market_probability_change=self._round(
                later_value.market_probability
                - earlier_value.market_probability
            ),
            public_percentage_change=self._round(
                later_snapshot.public_percentages.for_outcome(
                    outcome
                )
                - earlier_snapshot.public_percentages.for_outcome(
                    outcome
                )
            ),
            edge_change=self._round(
                later_value.edge_percentage_points
                - earlier_value.edge_percentage_points
            ),
        )

    @staticmethod
    def _validate_snapshots(
        earlier_snapshot: MarketSnapshot,
        later_snapshot: MarketSnapshot,
    ) -> None:
        """Validate the two snapshots before comparison."""

        if not isinstance(
            earlier_snapshot,
            MarketSnapshot,
        ):
            raise TypeError(
                "Earlier snapshot must be "
                "a MarketSnapshot."
            )

        if not isinstance(
            later_snapshot,
            MarketSnapshot,
        ):
            raise TypeError(
                "Later snapshot must be "
                "a MarketSnapshot."
            )

        if (
            later_snapshot.captured_at
            <= earlier_snapshot.captured_at
        ):
            raise ValueError(
                "Later market snapshot must be "
                "captured after the earlier snapshot."
            )

        if (
            later_snapshot.source_name
            != earlier_snapshot.source_name
        ):
            raise ValueError(
                "Market snapshots must use "
                "the same source name."
            )

    def _round(
        self,
        value: Decimal,
    ) -> Decimal:
        """Round one movement to two decimal places."""

        return value.quantize(
            self._quantum,
            rounding=ROUND_HALF_UP,
        )