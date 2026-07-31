"""Statistical comparison models for two football teams."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.models.team_form import TeamFormSummary


class MatchupLean(str, Enum):
    """Describes the statistical direction of a matchup."""

    HOME = "home"
    BALANCED = "balanced"
    AWAY = "away"

    @property
    def display_name(self) -> str:
        """Return a human-readable matchup direction."""

        names = {
            MatchupLean.HOME: "Home",
            MatchupLean.BALANCED: "Balanced",
            MatchupLean.AWAY: "Away",
        }

        return names[self]


class FormEdgeStrength(str, Enum):
    """Describes the strength of a statistical form edge."""

    BALANCED = "balanced"
    SLIGHT = "slight"
    CLEAR = "clear"
    STRONG = "strong"

    @property
    def rank(self) -> int:
        """Return a sortable strength rank."""

        ranks = {
            FormEdgeStrength.BALANCED: 0,
            FormEdgeStrength.SLIGHT: 1,
            FormEdgeStrength.CLEAR: 2,
            FormEdgeStrength.STRONG: 3,
        }

        return ranks[self]


@dataclass(frozen=True, slots=True)
class TeamFormComparison:
    """Contains a statistical comparison of home and away form."""

    home_form: TeamFormSummary
    away_form: TeamFormSummary
    projected_home_xg: Decimal
    projected_away_xg: Decimal
    projected_total_xg: Decimal
    projected_xg_difference: Decimal
    form_xg_difference: Decimal
    points_per_game_difference: Decimal
    shots_on_target_difference: Decimal
    lean: MatchupLean
    strength: FormEdgeStrength

    def __post_init__(self) -> None:
        """Validate the complete team-form comparison."""

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

        for field_name in (
            "projected_home_xg",
            "projected_away_xg",
            "projected_total_xg",
            "projected_xg_difference",
            "form_xg_difference",
            "points_per_game_difference",
            "shots_on_target_difference",
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

        for field_name in (
            "projected_home_xg",
            "projected_away_xg",
            "projected_total_xg",
        ):
            if getattr(
                self,
                field_name,
            ) < Decimal("0"):
                raise ValueError(
                    f"{field_name} must not be negative."
                )

        if (
            self.projected_total_xg
            != (
                self.projected_home_xg
                + self.projected_away_xg
            )
        ):
            raise ValueError(
                "projected_total_xg must equal "
                "projected home plus away xG."
            )

        if (
            self.projected_xg_difference
            != (
                self.projected_home_xg
                - self.projected_away_xg
            )
        ):
            raise ValueError(
                "projected_xg_difference must equal "
                "home xG minus away xG."
            )

        if not isinstance(
            self.lean,
            MatchupLean,
        ):
            raise TypeError(
                "lean must be a MatchupLean."
            )

        if not isinstance(
            self.strength,
            FormEdgeStrength,
        ):
            raise TypeError(
                "strength must be a FormEdgeStrength."
            )

        if (
            self.lean is MatchupLean.BALANCED
            and self.strength
            is not FormEdgeStrength.BALANCED
        ):
            raise ValueError(
                "A balanced lean requires "
                "balanced edge strength."
            )

        if (
            self.lean is not MatchupLean.BALANCED
            and self.strength
            is FormEdgeStrength.BALANCED
        ):
            raise ValueError(
                "A directional lean cannot use "
                "balanced edge strength."
            )

        if (
            self.lean is MatchupLean.HOME
            and self.projected_xg_difference
            <= Decimal("0")
        ):
            raise ValueError(
                "A home lean requires a positive "
                "projected xG difference."
            )

        if (
            self.lean is MatchupLean.AWAY
            and self.projected_xg_difference
            >= Decimal("0")
        ):
            raise ValueError(
                "An away lean requires a negative "
                "projected xG difference."
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
        """Return the projected xG score as compact text."""

        return (
            f"{self.projected_home_xg:.2f}-"
            f"{self.projected_away_xg:.2f}"
        )

    @property
    def lean_team_name(self) -> str | None:
        """Return the team supported by the statistical lean."""

        if self.lean is MatchupLean.HOME:
            return self.home_team_name

        if self.lean is MatchupLean.AWAY:
            return self.away_team_name

        return None

    @property
    def home_has_edge(self) -> bool:
        """Return whether the model leans toward the home team."""

        return self.lean is MatchupLean.HOME

    @property
    def away_has_edge(self) -> bool:
        """Return whether the model leans toward the away team."""

        return self.lean is MatchupLean.AWAY

    @property
    def is_balanced(self) -> bool:
        """Return whether the matchup is statistically balanced."""

        return self.lean is MatchupLean.BALANCED