"""Tests for venue and competition form filters."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.services.team_form_analyzer import TeamFormAnalyzer


BASE_TIME = datetime(
    2026,
    8,
    20,
    15,
    0,
    tzinfo=timezone.utc,
)


def create_performance(
    *,
    days_ago: int,
    venue: MatchVenue,
    competition: str,
) -> TeamMatchPerformance:
    """Create one filterable team performance."""

    return TeamMatchPerformance(
        team_name="Arsenal",
        opponent_name=f"Opponent {days_ago}",
        played_at=(
            BASE_TIME
            - timedelta(
                days=days_ago
            )
        ),
        venue=venue,
        goals_for=2,
        goals_against=1,
        expected_goals_for=Decimal("1.60"),
        expected_goals_against=Decimal("1.00"),
        shots_for=12,
        shots_against=9,
        shots_on_target_for=5,
        shots_on_target_against=3,
        competition=competition,
    )


def create_performances() -> tuple[
    TeamMatchPerformance,
    ...,
]:
    """Create mixed venue and competition performances."""

    return (
        create_performance(
            days_ago=1,
            venue=MatchVenue.AWAY,
            competition="Premier League",
        ),
        create_performance(
            days_ago=2,
            venue=MatchVenue.HOME,
            competition="Premier League",
        ),
        create_performance(
            days_ago=3,
            venue=MatchVenue.HOME,
            competition="Champions League",
        ),
    )


def test_analyzer_filters_by_venue() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances(),
        venue=MatchVenue.HOME,
    )

    assert summary.match_count == 2
    assert all(
        match.venue is MatchVenue.HOME
        for match in summary.matches
    )


def test_analyzer_filters_by_competition() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances(),
        competition="  premier   league  ",
    )

    assert summary.match_count == 2
    assert all(
        match.competition == "Premier League"
        for match in summary.matches
    )


def test_analyzer_filters_before_applying_limit() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances(),
        venue=MatchVenue.HOME,
        limit=1,
    )

    assert summary.match_count == 1
    assert (
        summary.matches[0].played_at
        == BASE_TIME - timedelta(days=2)
    )


def test_analyzer_rejects_empty_filtered_result() -> None:
    with pytest.raises(
        ValueError,
        match="requested filters",
    ):
        TeamFormAnalyzer().analyze(
            create_performances(),
            venue=MatchVenue.NEUTRAL,
        )


def test_analyzer_rejects_invalid_venue_filter() -> None:
    with pytest.raises(
        TypeError,
        match="MatchVenue or None",
    ):
        TeamFormAnalyzer().analyze(
            create_performances(),
            venue="home",  # type: ignore[arg-type]
        )


def test_analyzer_rejects_invalid_competition_type() -> None:
    with pytest.raises(
        TypeError,
        match="string or None",
    ):
        TeamFormAnalyzer().analyze(
            create_performances(),
            competition=123,  # type: ignore[arg-type]
        )


def test_analyzer_rejects_empty_competition_filter() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        TeamFormAnalyzer().analyze(
            create_performances(),
            competition="   ",
        )