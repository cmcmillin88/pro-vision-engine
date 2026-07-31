"""Statistical 1-X-2 and scoreline prediction models."""

from dataclasses import dataclass
from decimal import Decimal

from src.models.outcome import Outcome
from src.models.team_form_comparison import (
    TeamFormComparison,
)


@dataclass(frozen=True, slots=True)
class StatisticalOutcomeProbabilities:
    """Contains normalized statistical 1-X-2 probabilities."""

    home: Decimal
    draw: Decimal
    away: Decimal

    def __post_init__(self) -> None:
        """Validate the complete probability distribution."""

        for field_name in (
            "home",
            "draw",
            "away",
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
                    f"{field_name} must be a Decimal."
                )

            if not value.is_finite():
                raise ValueError(
                    f"{field_name} must be finite."
                )

            if not (
                Decimal("0")
                <= value
                <= Decimal("100")
            ):
                raise ValueError(
                    f"{field_name} must be "
                    "between 0 and 100."
                )

        if self.total != Decimal("100.00"):
            raise ValueError(
                "Statistical outcome probabilities "
                "must total exactly 100.00."
            )

    @property
    def total(self) -> Decimal:
        """Return the total probability."""

        return (
            self.home
            + self.draw
            + self.away
        )

    def for_outcome(
        self,
        outcome: Outcome,
    ) -> Decimal:
        """Return probability for one 1-X-2 outcome."""

        resolved_outcome = Outcome.parse(
            outcome
        )

        values = {
            Outcome.HOME: self.home,
            Outcome.DRAW: self.draw,
            Outcome.AWAY: self.away,
        }

        return values[
            resolved_outcome
        ]

    @property
    def favorite_outcome(self) -> Outcome:
        """Return the most probable outcome."""

        return max(
            Outcome.ordered(),
            key=self.for_outcome,
        )

    @property
    def confidence_margin(self) -> Decimal:
        """Return the gap between the top two outcomes."""

        ordered_probabilities = sorted(
            (
                self.home,
                self.draw,
                self.away,
            ),
            reverse=True,
        )

        return (
            ordered_probabilities[0]
            - ordered_probabilities[1]
        )


@dataclass(frozen=True, slots=True)
class ScorelineProbability:
    """Contains the probability of one exact scoreline."""

    home_goals: int
    away_goals: int
    probability: Decimal

    def __post_init__(self) -> None:
        """Validate one exact-score probability."""

        for field_name in (
            "home_goals",
            "away_goals",
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

        if not isinstance(
            self.probability,
            Decimal,
        ):
            raise TypeError(
                "probability must be a Decimal."
            )

        if not self.probability.is_finite():
            raise ValueError(
                "probability must be finite."
            )

        if not (
            Decimal("0")
            <= self.probability
            <= Decimal("100")
        ):
            raise ValueError(
                "probability must be "
                "between 0 and 100."
            )

    @property
    def scoreline(self) -> str:
        """Return the exact result as compact text."""

        return (
            f"{self.home_goals}-"
            f"{self.away_goals}"
        )

    @property
    def total_goals(self) -> int:
        """Return total goals in the scoreline."""

        return (
            self.home_goals
            + self.away_goals
        )

    @property
    def result(self) -> Outcome:
        """Return the 1-X-2 result represented by the score."""

        if self.home_goals > self.away_goals:
            return Outcome.HOME

        if self.home_goals < self.away_goals:
            return Outcome.AWAY

        return Outcome.DRAW

    @property
    def both_teams_to_score(self) -> bool:
        """Return whether both teams score."""

        return (
            self.home_goals > 0
            and self.away_goals > 0
        )


@dataclass(frozen=True, slots=True)
class StatisticalMatchPrediction:
    """Contains a complete statistical match prediction."""

    comparison: TeamFormComparison
    outcome_probabilities: StatisticalOutcomeProbabilities
    scorelines: tuple[ScorelineProbability, ...]
    included_probability_mass: Decimal
    maximum_goals: int

    def __post_init__(self) -> None:
        """Validate the complete prediction."""

        if not isinstance(
            self.comparison,
            TeamFormComparison,
        ):
            raise TypeError(
                "comparison must be "
                "a TeamFormComparison."
            )

        if not isinstance(
            self.outcome_probabilities,
            StatisticalOutcomeProbabilities,
        ):
            raise TypeError(
                "outcome_probabilities must be a "
                "StatisticalOutcomeProbabilities."
            )

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

        if not isinstance(
            self.included_probability_mass,
            Decimal,
        ):
            raise TypeError(
                "included_probability_mass "
                "must be a Decimal."
            )

        if not (
            self.included_probability_mass.is_finite()
        ):
            raise ValueError(
                "included_probability_mass "
                "must be finite."
            )

        if not (
            Decimal("0")
            < self.included_probability_mass
            <= Decimal("100")
        ):
            raise ValueError(
                "included_probability_mass must be "
                "greater than 0 and at most 100."
            )

        if not isinstance(
            self.scorelines,
            tuple,
        ):
            raise TypeError(
                "scorelines must be a tuple."
            )

        expected_count = (
            self.maximum_goals
            + 1
        ) ** 2

        if len(self.scorelines) != expected_count:
            raise ValueError(
                "Scoreline matrix does not match "
                "maximum_goals."
            )

        score_pairs: set[
            tuple[int, int]
        ] = set()

        for scoreline in self.scorelines:
            if not isinstance(
                scoreline,
                ScorelineProbability,
            ):
                raise TypeError(
                    "scorelines may only contain "
                    "ScorelineProbability objects."
                )

            if (
                scoreline.home_goals
                > self.maximum_goals
                or scoreline.away_goals
                > self.maximum_goals
            ):
                raise ValueError(
                    "Scoreline exceeds maximum_goals."
                )

            pair = (
                scoreline.home_goals,
                scoreline.away_goals,
            )

            if pair in score_pairs:
                raise ValueError(
                    "Scoreline matrix must not "
                    "contain duplicates."
                )

            score_pairs.add(
                pair
            )

        expected_order = tuple(
            sorted(
                self.scorelines,
                key=lambda scoreline: (
                    -scoreline.probability,
                    scoreline.home_goals,
                    scoreline.away_goals,
                ),
            )
        )

        if self.scorelines != expected_order:
            raise ValueError(
                "Scorelines must be ordered by "
                "probability and score."
            )

    @property
    def home_team_name(self) -> str:
        """Return the home-team name."""

        return self.comparison.home_team_name

    @property
    def away_team_name(self) -> str:
        """Return the away-team name."""

        return self.comparison.away_team_name

    @property
    def favorite_outcome(self) -> Outcome:
        """Return the statistically most probable outcome."""

        return (
            self.outcome_probabilities
            .favorite_outcome
        )

    @property
    def confidence_margin(self) -> Decimal:
        """Return the probability gap to the second outcome."""

        return (
            self.outcome_probabilities
            .confidence_margin
        )

    @property
    def most_likely_scoreline(
        self,
    ) -> ScorelineProbability:
        """Return the most probable exact scoreline."""

        return self.scorelines[0]

    @property
    def truncated_probability_mass(
        self,
    ) -> Decimal:
        """Return probability outside the score matrix."""

        return (
            Decimal("100")
            - self.included_probability_mass
        ).quantize(
            Decimal("0.000001")
        )

    def probability_for(
        self,
        outcome: Outcome,
    ) -> Decimal:
        """Return the statistical probability of one outcome."""

        return (
            self.outcome_probabilities
            .for_outcome(
                outcome
            )
        )

    def top_scorelines(
        self,
        limit: int = 5,
    ) -> tuple[ScorelineProbability, ...]:
        """Return the most probable exact scores."""

        if isinstance(
            limit,
            bool,
        ) or not isinstance(
            limit,
            int,
        ):
            raise TypeError(
                "limit must be an integer."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        return self.scorelines[
            :limit
        ]