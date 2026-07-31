"""Aggregated football team form models."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from src.models.team_match_performance import (
    TeamMatchPerformance,
    TeamMatchResult,
)


@dataclass(frozen=True, slots=True)
class TeamFormSummary:
    """Contains aggregated form and xG statistics for one team."""

    team_name: str
    matches: tuple[TeamMatchPerformance, ...]
    goals_for_average: Decimal
    goals_against_average: Decimal
    expected_goals_for_average: Decimal
    expected_goals_against_average: Decimal
    shots_for_average: Decimal
    shots_on_target_for_average: Decimal
    points_per_game: Decimal
    win_rate: Decimal
    draw_rate: Decimal
    loss_rate: Decimal
    clean_sheet_rate: Decimal
    failed_to_score_rate: Decimal

    _average_fields: ClassVar[tuple[str, ...]] = (
        "goals_for_average",
        "goals_against_average",
        "expected_goals_for_average",
        "expected_goals_against_average",
        "shots_for_average",
        "shots_on_target_for_average",
        "points_per_game",
    )

    _rate_fields: ClassVar[tuple[str, ...]] = (
        "win_rate",
        "draw_rate",
        "loss_rate",
        "clean_sheet_rate",
        "failed_to_score_rate",
    )

    def __post_init__(self) -> None:
        """Validate the complete form summary."""

        if not isinstance(
            self.team_name,
            str,
        ):
            raise TypeError(
                "TeamFormSummary team_name "
                "must be a string."
            )

        normalized_team_name = " ".join(
            self.team_name.split()
        )

        if not normalized_team_name:
            raise ValueError(
                "TeamFormSummary team_name "
                "must not be empty."
            )

        object.__setattr__(
            self,
            "team_name",
            normalized_team_name,
        )

        if not isinstance(
            self.matches,
            tuple,
        ):
            raise TypeError(
                "TeamFormSummary matches must be a tuple."
            )

        if not self.matches:
            raise ValueError(
                "TeamFormSummary requires at least one match."
            )

        for match in self.matches:
            if not isinstance(
                match,
                TeamMatchPerformance,
            ):
                raise TypeError(
                    "TeamFormSummary matches may only contain "
                    "TeamMatchPerformance objects."
                )

            if (
                match.team_name.casefold()
                != normalized_team_name.casefold()
            ):
                raise ValueError(
                    "All form matches must belong "
                    "to the same team."
                )

        expected_order = tuple(
            sorted(
                self.matches,
                key=lambda match: match.played_at,
                reverse=True,
            )
        )

        if self.matches != expected_order:
            raise ValueError(
                "TeamFormSummary matches must be ordered "
                "from newest to oldest."
            )

        for field_name in self._average_fields:
            self._validate_decimal(
                getattr(
                    self,
                    field_name,
                ),
                field_name=field_name,
            )

        if self.points_per_game > Decimal("3"):
            raise ValueError(
                "points_per_game must not exceed 3."
            )

        for field_name in self._rate_fields:
            value = getattr(
                self,
                field_name,
            )

            self._validate_decimal(
                value,
                field_name=field_name,
            )

            if value > Decimal("100"):
                raise ValueError(
                    f"{field_name} must not exceed 100."
                )

    @property
    def match_count(self) -> int:
        """Return the number of included matches."""

        return len(
            self.matches
        )

    @property
    def wins(self) -> int:
        """Return the number of wins."""

        return self._result_count(
            TeamMatchResult.WIN
        )

    @property
    def draws(self) -> int:
        """Return the number of draws."""

        return self._result_count(
            TeamMatchResult.DRAW
        )

    @property
    def losses(self) -> int:
        """Return the number of losses."""

        return self._result_count(
            TeamMatchResult.LOSS
        )

    @property
    def total_points(self) -> int:
        """Return total points from all included matches."""

        return sum(
            match.points
            for match in self.matches
        )

    @property
    def total_goal_difference(self) -> int:
        """Return total actual goal difference."""

        return sum(
            match.goal_difference
            for match in self.matches
        )

    @property
    def total_expected_goal_difference(
        self,
    ) -> Decimal:
        """Return total expected-goal difference."""

        return sum(
            (
                match.expected_goal_difference
                for match in self.matches
            ),
            Decimal("0"),
        )

    @property
    def form_string(self) -> str:
        """Return newest-first W-D-L form symbols."""

        return "".join(
            match.result.form_symbol
            for match in self.matches
        )

    @property
    def latest_match(
        self,
    ) -> TeamMatchPerformance:
        """Return the newest included match."""

        return self.matches[0]

    def _result_count(
        self,
        result: TeamMatchResult,
    ) -> int:
        """Count matches with one result."""

        return sum(
            match.result is result
            for match in self.matches
        )

    @staticmethod
    def _validate_decimal(
        value: object,
        *,
        field_name: str,
    ) -> None:
        """Validate a non-negative finite Decimal."""

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

        if value < Decimal("0"):
            raise ValueError(
                f"{field_name} must not be negative."
            )