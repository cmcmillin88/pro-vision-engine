"""Complete statistical analysis result for one football match."""

from dataclasses import dataclass
from decimal import Decimal

from src.models.outcome import Outcome
from src.models.statistical_match_prediction import (
    ScorelineProbability,
    StatisticalMatchPrediction,
    StatisticalOutcomeProbabilities,
)
from src.models.team_form import TeamFormSummary
from src.models.team_form_comparison import (
    FormEdgeStrength,
    MatchupLean,
    TeamFormComparison,
)
from src.models.team_match_performance import (
    MatchVenue,
)


@dataclass(frozen=True, slots=True)
class StatisticalAnalysisReport:
    """Contains the complete statistical analysis pipeline."""

    home_form: TeamFormSummary
    away_form: TeamFormSummary
    form_comparison: TeamFormComparison
    prediction: StatisticalMatchPrediction

    def __post_init__(self) -> None:
        """Validate all relationships in the analysis chain."""

        if not isinstance(
            self.home_form,
            TeamFormSummary,
        ):
            raise TypeError(
                "home_form must be a TeamFormSummary."
            )

        if not isinstance(
            self.away_form,
            TeamFormSummary,
        ):
            raise TypeError(
                "away_form must be a TeamFormSummary."
            )

        if (
            self.home_form.team_name.casefold()
            == self.away_form.team_name.casefold()
        ):
            raise ValueError(
                "Home and away teams must be different."
            )

        if any(
            match.venue is not MatchVenue.HOME
            for match in self.home_form.matches
        ):
            raise ValueError(
                "home_form must contain only "
                "home performances."
            )

        if any(
            match.venue is not MatchVenue.AWAY
            for match in self.away_form.matches
        ):
            raise ValueError(
                "away_form must contain only "
                "away performances."
            )

        if not isinstance(
            self.form_comparison,
            TeamFormComparison,
        ):
            raise TypeError(
                "form_comparison must be "
                "a TeamFormComparison."
            )

        if (
            self.form_comparison.home_form
            != self.home_form
            or self.form_comparison.away_form
            != self.away_form
        ):
            raise ValueError(
                "form_comparison must use the supplied "
                "home and away forms."
            )

        if not isinstance(
            self.prediction,
            StatisticalMatchPrediction,
        ):
            raise TypeError(
                "prediction must be a "
                "StatisticalMatchPrediction."
            )

        if (
            self.prediction.comparison
            != self.form_comparison
        ):
            raise ValueError(
                "prediction must use the supplied "
                "form comparison."
            )

    @property
    def home_team_name(self) -> str:
        """Return the home-team name."""

        return self.home_form.team_name

    @property
    def away_team_name(self) -> str:
        """Return the away-team name."""

        return self.away_form.team_name

    @property
    def projected_scoreline(self) -> str:
        """Return the projected xG score."""

        return self.form_comparison.projected_scoreline

    @property
    def projected_home_xg(self) -> Decimal:
        """Return projected home expected goals."""

        return self.form_comparison.projected_home_xg

    @property
    def projected_away_xg(self) -> Decimal:
        """Return projected away expected goals."""

        return self.form_comparison.projected_away_xg

    @property
    def projected_total_xg(self) -> Decimal:
        """Return projected total expected goals."""

        return self.form_comparison.projected_total_xg

    @property
    def matchup_lean(self) -> MatchupLean:
        """Return the statistical matchup direction."""

        return self.form_comparison.lean

    @property
    def edge_strength(self) -> FormEdgeStrength:
        """Return the statistical edge strength."""

        return self.form_comparison.strength

    @property
    def outcome_probabilities(
        self,
    ) -> StatisticalOutcomeProbabilities:
        """Return the normalized 1-X-2 probabilities."""

        return self.prediction.outcome_probabilities

    @property
    def favorite_outcome(self) -> Outcome:
        """Return the statistically most probable outcome."""

        return self.prediction.favorite_outcome

    @property
    def confidence_margin(self) -> Decimal:
        """Return the gap between the top two outcomes."""

        return self.prediction.confidence_margin

    @property
    def most_likely_scoreline(
        self,
    ) -> ScorelineProbability:
        """Return the most probable exact result."""

        return self.prediction.most_likely_scoreline

    @property
    def home_match_count(self) -> int:
        """Return included home-match count."""

        return self.home_form.match_count

    @property
    def away_match_count(self) -> int:
        """Return included away-match count."""

        return self.away_form.match_count

    def probability_for(
        self,
        outcome: Outcome,
    ) -> Decimal:
        """Return the statistical probability of one outcome."""

        return self.prediction.probability_for(
            outcome
        )

    def top_scorelines(
        self,
        limit: int = 5,
    ) -> tuple[ScorelineProbability, ...]:
        """Return the most probable exact scorelines."""

        return self.prediction.top_scorelines(
            limit
        )