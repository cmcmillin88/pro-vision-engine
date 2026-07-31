"""Aggregation service for football team form and xG."""

from collections.abc import Iterable
from decimal import Decimal, ROUND_HALF_UP

from src.models.team_form import TeamFormSummary
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
    TeamMatchResult,
)


class TeamFormAnalyzer:
    """Calculates recent form from individual team performances."""

    _quantum = Decimal("0.01")
    _hundred = Decimal("100")

    def analyze(
        self,
        performances: Iterable[TeamMatchPerformance],
        *,
        limit: int | None = None,
        venue: MatchVenue | None = None,
        competition: str | None = None,
    ) -> TeamFormSummary:
        """Aggregate filtered recent performances for one team."""

        self._validate_limit(
            limit
        )
        normalized_competition = (
            self._validate_filters(
                venue=venue,
                competition=competition,
            )
        )

        try:
            resolved_performances = tuple(
                performances
            )
        except TypeError as error:
            raise TypeError(
                "performances must be iterable."
            ) from error

        if not resolved_performances:
            raise ValueError(
                "TeamFormAnalyzer requires "
                "at least one performance."
            )

        for performance in resolved_performances:
            if not isinstance(
                performance,
                TeamMatchPerformance,
            ):
                raise TypeError(
                    "performances may only contain "
                    "TeamMatchPerformance objects."
                )

        reference_name = (
            resolved_performances[0]
            .team_name
        )

        if any(
            performance.team_name.casefold()
            != reference_name.casefold()
            for performance in resolved_performances
        ):
            raise ValueError(
                "All performances must belong "
                "to the same team."
            )

        ordered_performances = tuple(
            sorted(
                resolved_performances,
                key=lambda performance: (
                    performance.played_at
                ),
                reverse=True,
            )
        )

        filtered_performances = tuple(
            performance
            for performance in ordered_performances
            if self._matches_filters(
                performance,
                venue=venue,
                competition=normalized_competition,
            )
        )

        if not filtered_performances:
            raise ValueError(
                "No performances match "
                "the requested filters."
            )

        if limit is None:
            selected_performances = (
                filtered_performances
            )
        else:
            selected_performances = (
                filtered_performances[:limit]
            )

        match_count = len(
            selected_performances
        )
        team_name = (
            selected_performances[0]
            .team_name
        )

        wins = self._count_results(
            selected_performances,
            TeamMatchResult.WIN,
        )
        draws = self._count_results(
            selected_performances,
            TeamMatchResult.DRAW,
        )
        losses = self._count_results(
            selected_performances,
            TeamMatchResult.LOSS,
        )
        clean_sheets = sum(
            performance.kept_clean_sheet
            for performance in selected_performances
        )
        failed_to_score = sum(
            performance.failed_to_score
            for performance in selected_performances
        )

        return TeamFormSummary(
            team_name=team_name,
            matches=selected_performances,
            goals_for_average=self._average(
                (
                    Decimal(
                        performance.goals_for
                    )
                    for performance
                    in selected_performances
                ),
                match_count,
            ),
            goals_against_average=self._average(
                (
                    Decimal(
                        performance.goals_against
                    )
                    for performance
                    in selected_performances
                ),
                match_count,
            ),
            expected_goals_for_average=self._average(
                (
                    performance.expected_goals_for
                    for performance
                    in selected_performances
                ),
                match_count,
            ),
            expected_goals_against_average=self._average(
                (
                    performance.expected_goals_against
                    for performance
                    in selected_performances
                ),
                match_count,
            ),
            shots_for_average=self._average(
                (
                    Decimal(
                        performance.shots_for
                    )
                    for performance
                    in selected_performances
                ),
                match_count,
            ),
            shots_on_target_for_average=self._average(
                (
                    Decimal(
                        performance.shots_on_target_for
                    )
                    for performance
                    in selected_performances
                ),
                match_count,
            ),
            points_per_game=self._average(
                (
                    Decimal(
                        performance.points
                    )
                    for performance
                    in selected_performances
                ),
                match_count,
            ),
            win_rate=self._rate(
                wins,
                match_count,
            ),
            draw_rate=self._rate(
                draws,
                match_count,
            ),
            loss_rate=self._rate(
                losses,
                match_count,
            ),
            clean_sheet_rate=self._rate(
                clean_sheets,
                match_count,
            ),
            failed_to_score_rate=self._rate(
                failed_to_score,
                match_count,
            ),
        )

    @staticmethod
    def _validate_limit(
        limit: int | None,
    ) -> None:
        """Validate an optional recent-match limit."""

        if limit is None:
            return

        if isinstance(
            limit,
            bool,
        ) or not isinstance(
            limit,
            int,
        ):
            raise TypeError(
                "limit must be an integer or None."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

    @staticmethod
    def _validate_filters(
        *,
        venue: MatchVenue | None,
        competition: str | None,
    ) -> str | None:
        """Validate and normalize optional form filters."""

        if (
            venue is not None
            and not isinstance(
                venue,
                MatchVenue,
            )
        ):
            raise TypeError(
                "venue filter must be "
                "a MatchVenue or None."
            )

        if competition is None:
            return None

        if not isinstance(
            competition,
            str,
        ):
            raise TypeError(
                "competition filter must be "
                "a string or None."
            )

        normalized_competition = " ".join(
            competition.split()
        )

        if not normalized_competition:
            raise ValueError(
                "competition filter "
                "must not be empty."
            )

        return normalized_competition

    @staticmethod
    def _matches_filters(
        performance: TeamMatchPerformance,
        *,
        venue: MatchVenue | None,
        competition: str | None,
    ) -> bool:
        """Return whether a performance matches all filters."""

        if (
            venue is not None
            and performance.venue is not venue
        ):
            return False

        if competition is not None:
            performance_competition = (
                performance.competition
                or ""
            )

            if (
                performance_competition.casefold()
                != competition.casefold()
            ):
                return False

        return True

    @staticmethod
    def _count_results(
        performances: tuple[
            TeamMatchPerformance,
            ...,
        ],
        result: TeamMatchResult,
    ) -> int:
        """Count one result type."""

        return sum(
            performance.result is result
            for performance in performances
        )

    def _average(
        self,
        values: Iterable[Decimal],
        count: int,
    ) -> Decimal:
        """Calculate a rounded Decimal average."""

        total = sum(
            values,
            Decimal("0"),
        )

        return self._round(
            total
            / Decimal(count)
        )

    def _rate(
        self,
        occurrence_count: int,
        match_count: int,
    ) -> Decimal:
        """Calculate a rounded percentage rate."""

        return self._round(
            Decimal(occurrence_count)
            / Decimal(match_count)
            * self._hundred
        )

    def _round(
        self,
        value: Decimal,
    ) -> Decimal:
        """Round one statistic to two decimal places."""

        return value.quantize(
            self._quantum,
            rounding=ROUND_HALF_UP,
        )