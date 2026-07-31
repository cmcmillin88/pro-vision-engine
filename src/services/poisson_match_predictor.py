"""Poisson-based statistical football match predictor."""

from decimal import Decimal, ROUND_HALF_UP

from src.models.outcome import Outcome
from src.models.poisson_prediction_settings import (
    PoissonPredictionSettings,
)
from src.models.statistical_match_prediction import (
    ScorelineProbability,
    StatisticalMatchPrediction,
    StatisticalOutcomeProbabilities,
)
from src.models.team_form_comparison import (
    TeamFormComparison,
)


class PoissonMatchPredictor:
    """Converts projected xG into 1-X-2 probabilities."""

    _hundred = Decimal("100")
    _probability_quantum = Decimal("0.01")
    _mass_quantum = Decimal("0.000001")

    def __init__(
        self,
        settings: (
            PoissonPredictionSettings
            | None
        ) = None,
    ) -> None:
        """Create the predictor."""

        self._settings = (
            settings
            or PoissonPredictionSettings()
        )

    def predict(
        self,
        comparison: TeamFormComparison,
    ) -> StatisticalMatchPrediction:
        """Create a statistical prediction from projected xG."""

        if not isinstance(
            comparison,
            TeamFormComparison,
        ):
            raise TypeError(
                "PoissonMatchPredictor requires "
                "a TeamFormComparison."
            )

        home_distribution = (
            self._poisson_distribution(
                comparison.projected_home_xg
            )
        )
        away_distribution = (
            self._poisson_distribution(
                comparison.projected_away_xg
            )
        )

        included_mass = (
            sum(
                home_distribution,
                Decimal("0"),
            )
            * sum(
                away_distribution,
                Decimal("0"),
            )
        )
        included_percentage = (
            included_mass
            * self._hundred
        )

        if (
            included_percentage
            < self._settings.minimum_included_mass
        ):
            raise ValueError(
                "Included probability mass "
                f"{self._round_mass(included_percentage)} "
                "is below the configured minimum "
                f"{self._settings.minimum_included_mass}. "
                "Increase maximum_goals."
            )

        outcome_masses = {
            Outcome.HOME: Decimal("0"),
            Outcome.DRAW: Decimal("0"),
            Outcome.AWAY: Decimal("0"),
        }
        raw_scorelines: list[
            tuple[int, int, Decimal]
        ] = []

        for (
            home_goals,
            home_probability,
        ) in enumerate(
            home_distribution
        ):
            for (
                away_goals,
                away_probability,
            ) in enumerate(
                away_distribution
            ):
                raw_probability = (
                    home_probability
                    * away_probability
                )

                raw_scorelines.append(
                    (
                        home_goals,
                        away_goals,
                        raw_probability,
                    )
                )

                if home_goals > away_goals:
                    outcome = Outcome.HOME
                elif home_goals < away_goals:
                    outcome = Outcome.AWAY
                else:
                    outcome = Outcome.DRAW

                outcome_masses[outcome] += (
                    raw_probability
                )

        scorelines = tuple(
            sorted(
                (
                    ScorelineProbability(
                        home_goals=home_goals,
                        away_goals=away_goals,
                        probability=(
                            self._round_probability(
                                raw_probability
                                / included_mass
                                * self._hundred
                            )
                        ),
                    )
                    for (
                        home_goals,
                        away_goals,
                        raw_probability,
                    ) in raw_scorelines
                ),
                key=lambda scoreline: (
                    -scoreline.probability,
                    scoreline.home_goals,
                    scoreline.away_goals,
                ),
            )
        )

        outcome_probabilities = (
            self._create_outcome_probabilities(
                outcome_masses,
                included_mass,
            )
        )

        return StatisticalMatchPrediction(
            comparison=comparison,
            outcome_probabilities=(
                outcome_probabilities
            ),
            scorelines=scorelines,
            included_probability_mass=(
                self._round_mass(
                    included_percentage
                )
            ),
            maximum_goals=(
                self._settings.maximum_goals
            ),
        )

    def _poisson_distribution(
        self,
        expected_goals: Decimal,
    ) -> tuple[Decimal, ...]:
        """Return probabilities from zero to maximum goals."""

        probabilities = [
            (
                -expected_goals
            ).exp()
        ]

        for goals in range(
            1,
            self._settings.maximum_goals
            + 1,
        ):
            next_probability = (
                probabilities[-1]
                * expected_goals
                / Decimal(goals)
            )

            probabilities.append(
                next_probability
            )

        return tuple(
            probabilities
        )

    def _create_outcome_probabilities(
        self,
        outcome_masses: dict[Outcome, Decimal],
        included_mass: Decimal,
    ) -> StatisticalOutcomeProbabilities:
        """Normalize and round all 1-X-2 probabilities."""

        normalized = {
            outcome: (
                outcome_masses[outcome]
                / included_mass
                * self._hundred
            )
            for outcome in Outcome.ordered()
        }
        rounded = {
            outcome: self._round_probability(
                normalized[outcome]
            )
            for outcome in Outcome.ordered()
        }

        residual = (
            self._hundred
            - sum(
                rounded.values(),
                Decimal("0"),
            )
        )
        adjustment_outcome = max(
            Outcome.ordered(),
            key=lambda outcome: normalized[outcome],
        )
        rounded[adjustment_outcome] = (
            rounded[adjustment_outcome]
            + residual
        ).quantize(
            self._probability_quantum,
            rounding=ROUND_HALF_UP,
        )

        return StatisticalOutcomeProbabilities(
            home=rounded[Outcome.HOME],
            draw=rounded[Outcome.DRAW],
            away=rounded[Outcome.AWAY],
        )

    def _round_probability(
        self,
        value: Decimal,
    ) -> Decimal:
        """Round one displayed probability."""

        return value.quantize(
            self._probability_quantum,
            rounding=ROUND_HALF_UP,
        )

    def _round_mass(
        self,
        value: Decimal,
    ) -> Decimal:
        """Round retained probability mass."""

        return value.quantize(
            self._mass_quantum,
            rounding=ROUND_HALF_UP,
        )