"""Statistical performance for one team in one football match."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum


class MatchVenue(str, Enum):
    """Describes where a team played a match."""

    HOME = "home"
    AWAY = "away"
    NEUTRAL = "neutral"

    @property
    def display_name(self) -> str:
        """Return a human-readable venue name."""

        names = {
            MatchVenue.HOME: "Home",
            MatchVenue.AWAY: "Away",
            MatchVenue.NEUTRAL: "Neutral",
        }

        return names[self]


class TeamMatchResult(str, Enum):
    """Describes the result from one team's perspective."""

    WIN = "win"
    DRAW = "draw"
    LOSS = "loss"

    @property
    def points(self) -> int:
        """Return the league points for the result."""

        points_by_result = {
            TeamMatchResult.WIN: 3,
            TeamMatchResult.DRAW: 1,
            TeamMatchResult.LOSS: 0,
        }

        return points_by_result[self]

    @property
    def form_symbol(self) -> str:
        """Return a compact form symbol."""

        symbols = {
            TeamMatchResult.WIN: "W",
            TeamMatchResult.DRAW: "D",
            TeamMatchResult.LOSS: "L",
        }

        return symbols[self]


@dataclass(frozen=True, slots=True)
class TeamMatchPerformance:
    """Contains one team's result and underlying match statistics."""

    team_name: str
    opponent_name: str
    played_at: datetime
    venue: MatchVenue
    goals_for: int
    goals_against: int
    expected_goals_for: Decimal
    expected_goals_against: Decimal
    shots_for: int
    shots_against: int
    shots_on_target_for: int
    shots_on_target_against: int
    possession_percentage: Decimal | None = None
    competition: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the complete performance."""

        normalized_team_name = self._normalize_required_text(
            self.team_name,
            field_name="team_name",
        )
        normalized_opponent_name = (
            self._normalize_required_text(
                self.opponent_name,
                field_name="opponent_name",
            )
        )

        if (
            normalized_team_name.casefold()
            == normalized_opponent_name.casefold()
        ):
            raise ValueError(
                "Team and opponent must be different."
            )

        object.__setattr__(
            self,
            "team_name",
            normalized_team_name,
        )
        object.__setattr__(
            self,
            "opponent_name",
            normalized_opponent_name,
        )

        if not isinstance(
            self.played_at,
            datetime,
        ):
            raise TypeError(
                "played_at must be a datetime."
            )

        if (
            self.played_at.tzinfo is None
            or self.played_at.utcoffset() is None
        ):
            raise ValueError(
                "played_at must include timezone information."
            )

        if not isinstance(
            self.venue,
            MatchVenue,
        ):
            raise TypeError(
                "venue must be a MatchVenue."
            )

        for field_name in (
            "goals_for",
            "goals_against",
            "shots_for",
            "shots_against",
            "shots_on_target_for",
            "shots_on_target_against",
        ):
            self._validate_non_negative_integer(
                getattr(
                    self,
                    field_name,
                ),
                field_name=field_name,
            )

        if (
            self.shots_on_target_for
            > self.shots_for
        ):
            raise ValueError(
                "shots_on_target_for cannot exceed shots_for."
            )

        if (
            self.shots_on_target_against
            > self.shots_against
        ):
            raise ValueError(
                "shots_on_target_against cannot exceed "
                "shots_against."
            )

        for field_name in (
            "expected_goals_for",
            "expected_goals_against",
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

        if self.possession_percentage is not None:
            possession = self._to_decimal(
                self.possession_percentage,
                field_name="possession_percentage",
            )

            if not (
                Decimal("0")
                <= possession
                <= Decimal("100")
            ):
                raise ValueError(
                    "possession_percentage must be "
                    "between 0 and 100."
                )

            object.__setattr__(
                self,
                "possession_percentage",
                possession,
            )

        if self.competition is not None:
            normalized_competition = (
                self._normalize_required_text(
                    self.competition,
                    field_name="competition",
                )
            )

            object.__setattr__(
                self,
                "competition",
                normalized_competition,
            )

    @property
    def result(self) -> TeamMatchResult:
        """Return the result from the team's perspective."""

        if self.goals_for > self.goals_against:
            return TeamMatchResult.WIN

        if self.goals_for < self.goals_against:
            return TeamMatchResult.LOSS

        return TeamMatchResult.DRAW

    @property
    def points(self) -> int:
        """Return points earned in the match."""

        return self.result.points

    @property
    def goal_difference(self) -> int:
        """Return actual goal difference."""

        return (
            self.goals_for
            - self.goals_against
        )

    @property
    def expected_goal_difference(self) -> Decimal:
        """Return expected-goal difference."""

        return (
            self.expected_goals_for
            - self.expected_goals_against
        )

    @property
    def finishing_delta(self) -> Decimal:
        """Return goals scored minus expected goals."""

        return (
            Decimal(self.goals_for)
            - self.expected_goals_for
        )

    @property
    def goal_prevention_delta(self) -> Decimal:
        """Return expected goals conceded minus actual goals conceded."""

        return (
            self.expected_goals_against
            - Decimal(self.goals_against)
        )

    @property
    def kept_clean_sheet(self) -> bool:
        """Return whether the team conceded no goals."""

        return self.goals_against == 0

    @property
    def failed_to_score(self) -> bool:
        """Return whether the team scored no goals."""

        return self.goals_for == 0

    @staticmethod
    def _normalize_required_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """Normalize one required text value."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized_value = " ".join(
            value.split()
        )

        if not normalized_value:
            raise ValueError(
                f"{field_name} must not be empty."
            )

        return normalized_value

    @staticmethod
    def _validate_non_negative_integer(
        value: object,
        *,
        field_name: str,
    ) -> None:
        """Validate one count statistic."""

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

    @staticmethod
    def _to_decimal(
        value: object,
        *,
        field_name: str,
    ) -> Decimal:
        """Convert one numeric value to a finite Decimal."""

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