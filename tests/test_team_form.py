"""Tests for aggregated team form models."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.models.team_form import TeamFormSummary
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)


BASE_TIME = datetime(
    2026,
    8,
    10,
    15,
    0,
    tzinfo=timezone.utc,
)


def create_performance(
    *,
    days_ago: int,
    team_name: str = "Arsenal",
    goals_for: int = 2,
    goals_against: int = 1,
) -> TeamMatchPerformance:
    """Create one form test performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=f"Opponent {days_ago}",
        played_at=(
            BASE_TIME
            - timedelta(
                days=days_ago
            )
        ),
        venue=MatchVenue.HOME,
        goals_for=goals_for,
        goals_against=goals_against,
        expected_goals_for=Decimal("1.50"),
        expected_goals_against=Decimal("1.00"),
        shots_for=12,
        shots_against=8,
        shots_on_target_for=5,
        shots_on_target_against=3,
    )


def create_summary() -> TeamFormSummary:
    """Create one valid form summary."""

    matches = (
        create_performance(
            days_ago=1,
            goals_for=2,
            goals_against=0,
        ),
        create_performance(
            days_ago=2,
            goals_for=1,
            goals_against=1,
        ),
        create_performance(
            days_ago=3,
            goals_for=0,
            goals_against=2,
        ),
    )

    return TeamFormSummary(
        team_name="Arsenal",
        matches=matches,
        goals_for_average=Decimal("1.00"),
        goals_against_average=Decimal("1.00"),
        expected_goals_for_average=Decimal("1.50"),
        expected_goals_against_average=Decimal("1.00"),
        shots_for_average=Decimal("12.00"),
        shots_on_target_for_average=Decimal("5.00"),
        points_per_game=Decimal("1.33"),
        win_rate=Decimal("33.33"),
        draw_rate=Decimal("33.33"),
        loss_rate=Decimal("33.33"),
        clean_sheet_rate=Decimal("33.33"),
        failed_to_score_rate=Decimal("33.33"),
    )


def test_summary_exposes_form_counts() -> None:
    summary = create_summary()

    assert summary.match_count == 3
    assert summary.wins == 1
    assert summary.draws == 1
    assert summary.losses == 1
    assert summary.form_string == "WDL"
    assert summary.latest_match is summary.matches[0]


def test_summary_exposes_aggregate_totals() -> None:
    summary = create_summary()

    assert summary.total_points == 4
    assert summary.total_goal_difference == 0
    assert (
        summary.total_expected_goal_difference
        == Decimal("1.50")
    )


def test_summary_rejects_empty_matches() -> None:
    values = create_summary()

    with pytest.raises(
        ValueError,
        match="at least one match",
    ):
        TeamFormSummary(
            team_name=values.team_name,
            matches=(),
            goals_for_average=values.goals_for_average,
            goals_against_average=(
                values.goals_against_average
            ),
            expected_goals_for_average=(
                values.expected_goals_for_average
            ),
            expected_goals_against_average=(
                values.expected_goals_against_average
            ),
            shots_for_average=values.shots_for_average,
            shots_on_target_for_average=(
                values.shots_on_target_for_average
            ),
            points_per_game=values.points_per_game,
            win_rate=values.win_rate,
            draw_rate=values.draw_rate,
            loss_rate=values.loss_rate,
            clean_sheet_rate=values.clean_sheet_rate,
            failed_to_score_rate=(
                values.failed_to_score_rate
            ),
        )


def test_summary_rejects_mixed_teams() -> None:
    values = create_summary()
    mixed_matches = (
        values.matches[0],
        create_performance(
            days_ago=2,
            team_name="Chelsea",
        ),
    )

    with pytest.raises(
        ValueError,
        match="same team",
    ):
        TeamFormSummary(
            team_name="Arsenal",
            matches=mixed_matches,
            goals_for_average=Decimal("1"),
            goals_against_average=Decimal("1"),
            expected_goals_for_average=Decimal("1"),
            expected_goals_against_average=Decimal("1"),
            shots_for_average=Decimal("1"),
            shots_on_target_for_average=Decimal("1"),
            points_per_game=Decimal("1"),
            win_rate=Decimal("50"),
            draw_rate=Decimal("0"),
            loss_rate=Decimal("50"),
            clean_sheet_rate=Decimal("0"),
            failed_to_score_rate=Decimal("0"),
        )


def test_summary_rejects_non_tuple_matches() -> None:
    values = create_summary()

    with pytest.raises(
        TypeError,
        match="must be a tuple",
    ):
        TeamFormSummary(
            team_name=values.team_name,
            matches=list(values.matches),  # type: ignore[arg-type]
            goals_for_average=values.goals_for_average,
            goals_against_average=(
                values.goals_against_average
            ),
            expected_goals_for_average=(
                values.expected_goals_for_average
            ),
            expected_goals_against_average=(
                values.expected_goals_against_average
            ),
            shots_for_average=values.shots_for_average,
            shots_on_target_for_average=(
                values.shots_on_target_for_average
            ),
            points_per_game=values.points_per_game,
            win_rate=values.win_rate,
            draw_rate=values.draw_rate,
            loss_rate=values.loss_rate,
            clean_sheet_rate=values.clean_sheet_rate,
            failed_to_score_rate=(
                values.failed_to_score_rate
            ),
        )