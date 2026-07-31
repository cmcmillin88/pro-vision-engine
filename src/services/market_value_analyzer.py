"""Odds-versus-public value analysis for 1-X-2 markets."""

from decimal import Decimal, ROUND_HALF_UP, localcontext

from src.models.market_value import (
    MarketValueAnalysis,
    OutcomeValue,
)
from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)


class MarketValueAnalyzer:
    """Calculates market probabilities and pool value from odds."""

    _hundred = Decimal("100")
    _quantum = Decimal("0.01")

    def analyze(
        self,
        odds: ThreeWayOdds,
        public_percentages: ThreeWayPercentages,
    ) -> MarketValueAnalysis:
        """Compare normalized market probability with public support."""

        if not isinstance(
            odds,
            ThreeWayOdds,
        ):
            raise TypeError(
                "MarketValueAnalyzer requires ThreeWayOdds."
            )

        if not isinstance(
            public_percentages,
            ThreeWayPercentages,
        ):
            raise TypeError(
                "MarketValueAnalyzer requires "
                "ThreeWayPercentages."
            )

        with localcontext() as context:
            context.prec = 28

            raw_probabilities = {
                outcome: (
                    self._hundred
                    / odds.for_outcome(outcome)
                )
                for outcome in Outcome.ordered()
            }
            raw_total = sum(
                raw_probabilities.values(),
                Decimal("0"),
            )
            normalized_probabilities = {
                outcome: self._round(
                    raw_probability
                    / raw_total
                    * self._hundred
                )
                for (
                    outcome,
                    raw_probability,
                ) in raw_probabilities.items()
            }

        market_probabilities = ThreeWayPercentages(
            home=normalized_probabilities[Outcome.HOME],
            draw=normalized_probabilities[Outcome.DRAW],
            away=normalized_probabilities[Outcome.AWAY],
        )
        overround = self._round(
            raw_total
            - self._hundred
        )
        outcome_values = tuple(
            self._create_outcome_value(
                outcome=outcome,
                odds=odds,
                public_percentages=public_percentages,
                market_probabilities=market_probabilities,
            )
            for outcome in Outcome.ordered()
        )

        return MarketValueAnalysis(
            odds=odds,
            public_percentages=public_percentages,
            market_probabilities=market_probabilities,
            overround_percentage_points=overround,
            outcome_values=outcome_values,
        )

    def _create_outcome_value(
        self,
        *,
        outcome: Outcome,
        odds: ThreeWayOdds,
        public_percentages: ThreeWayPercentages,
        market_probabilities: ThreeWayPercentages,
    ) -> OutcomeValue:
        """Build one calculated outcome assessment."""

        market_probability = (
            market_probabilities.for_outcome(
                outcome
            )
        )
        public_percentage = (
            public_percentages.for_outcome(
                outcome
            )
        )
        edge = self._round(
            market_probability
            - public_percentage
        )

        if public_percentage == Decimal("0"):
            value_index = None
        else:
            value_index = self._round(
                market_probability
                / public_percentage
                * self._hundred
            )

        return OutcomeValue(
            outcome=outcome,
            odds=odds.for_outcome(
                outcome
            ),
            market_probability=market_probability,
            public_percentage=public_percentage,
            edge_percentage_points=edge,
            value_index=value_index,
        )

    def _round(
        self,
        value: Decimal,
    ) -> Decimal:
        """Round an analysis value to two decimal places."""

        return value.quantize(
            self._quantum,
            rounding=ROUND_HALF_UP,
        )