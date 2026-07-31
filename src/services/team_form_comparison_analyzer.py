"""Statistical comparison service for two football teams."""

from decimal import Decimal, ROUND_HALF_UP

from src.models.team_form import TeamFormSummary
from src.models.team_form_comparison import (
    FormEdgeStrength,
    MatchupLean,
    TeamFormComparison,
)
from src.models.team_form_comparison_thresholds import (
    TeamFormComparisonThresholds,
)


class TeamFormComparisonAnalyzer:
    """Compares home and away form through xG and results."""

    _quantum = Decimal("0.01")
    _two = Decimal("2")

    def __init__(
        self,
        thresholds: (
            TeamFormComparisonThresholds
            | None
        ) = None,
    ) -> None:
        """Create the comparison analyzer."""

        self._thresholds = (
            thresholds
            or TeamFormComparisonThresholds()
        )

    def analyze(
        self,
        home_form: TeamFormSummary,
        away_form: TeamFormSummary,
    ) -> TeamFormComparison:
        """Compare two form summaries in home-away context."""

        self._validate_forms(
            home_form,
            away_form,
        )

        projected_home_xg = self._average(
            home_form.expected_goals_for_average,
            away_form.expected_goals_against_average,
        )
        projected_away_xg = self._average(
            away_form.expected_goals_for_average,
            home_form.expected_goals_against_average,
        )
        projected_total_xg = self._round(
            projected_home_xg
            + projected_away_xg
        )
        projected_xg_difference = self._round(
            projected_home_xg
            - projected_away_xg
        )

        home_form_xg_difference = (
            home_form.expected_goals_for_average
            - home_form.expected_goals_against_average
        )
        away_form_xg_difference = (
            away_form.expected_goals_for_average
            - away_form.expected_goals_against_average
        )
        form_xg_difference = self._round(
            home_form_xg_difference
            - away_form_xg_difference
        )
        points_per_game_difference = self._round(
            home_form.points_per_game
            - away_form.points_per_game
        )
        shots_on_target_difference = self._round(
            home_form.shots_on_target_for_average
            - away_form.shots_on_target_for_average
        )

        lean = self._resolve_lean(
            projected_xg_difference
        )
        strength = self._resolve_strength(
            projected_xg_difference,
            lean,
        )

        return TeamFormComparison(
            home_form=home_form,
            away_form=away_form,
            projected_home_xg=projected_home_xg,
            projected_away_xg=projected_away_xg,
            projected_total_xg=projected_total_xg,
            projected_xg_difference=(
                projected_xg_difference
            ),
            form_xg_difference=form_xg_difference,
            points_per_game_difference=(
                points_per_game_difference
            ),
            shots_on_target_difference=(
                shots_on_target_difference
            ),
            lean=lean,
            strength=strength,
        )

    @staticmethod
    def _validate_forms(
        home_form: TeamFormSummary,
        away_form: TeamFormSummary,
    ) -> None:
        """Validate the two supplied form summaries."""

        if not isinstance(
            home_form,
            TeamFormSummary,
        ):
            raise TypeError(
                "home_form must be a TeamFormSummary."
            )

        if not isinstance(
            away_form,
            TeamFormSummary,
        ):
            raise TypeError(
                "away_form must be a TeamFormSummary."
            )

        if (
            home_form.team_name.casefold()
            == away_form.team_name.casefold()
        ):
            raise ValueError(
                "Home and away teams must be different."
            )

    def _resolve_lean(
        self,
        projected_xg_difference: Decimal,
    ) -> MatchupLean:
        """Resolve the statistical matchup direction."""

        if (
            abs(projected_xg_difference)
            < self._thresholds.balanced_xg_margin
        ):
            return MatchupLean.BALANCED

        if projected_xg_difference > Decimal("0"):
            return MatchupLean.HOME

        return MatchupLean.AWAY

    def _resolve_strength(
        self,
        projected_xg_difference: Decimal,
        lean: MatchupLean,
    ) -> FormEdgeStrength:
        """Resolve the strength of the statistical edge."""

        if lean is MatchupLean.BALANCED:
            return FormEdgeStrength.BALANCED

        absolute_difference = abs(
            projected_xg_difference
        )

        if (
            absolute_difference
            < self._thresholds.clear_xg_margin
        ):
            return FormEdgeStrength.SLIGHT

        if (
            absolute_difference
            < self._thresholds.strong_xg_margin
        ):
            return FormEdgeStrength.CLEAR

        return FormEdgeStrength.STRONG

    def _average(
        self,
        first_value: Decimal,
        second_value: Decimal,
    ) -> Decimal:
        """Calculate the rounded average of two values."""

        return self._round(
            (
                first_value
                + second_value
            )
            / self._two
        )

    def _round(
        self,
        value: Decimal,
    ) -> Decimal:
        """Round one comparison value to two decimals."""

        return value.quantize(
            self._quantum,
            rounding=ROUND_HALF_UP,
        )