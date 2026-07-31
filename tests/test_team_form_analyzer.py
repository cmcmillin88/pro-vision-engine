"""Tests for team form and xG aggregation."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.services.team_form_analyzer import (
    TeamFormAnalyzer,
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
    goals_for: int,
    goals_against: int,
    expected_goals_for: str,
    expected_goals_against: str,
    shots_for: int,
    shots_on_target_for: int,
) -> TeamMatchPerformance:
    """Create one configurable form performance."""

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
        expected_goals_for=Decimal(
            expected_goals_for
        ),
        expected_goals_against=Decimal(
            expected_goals_against
        ),
        shots_for=shots_for,
        shots_against=10,
        shots_on_target_for=shots_on_target_for,
        shots_on_target_against=4,
    )


def create_performances() -> tuple[
    TeamMatchPerformance,
    ...,
]:
    """Create three deliberately unordered performances."""

    win = create_performance(
        days_ago=1,
        goals_for=2,
        goals_against=0,
        expected_goals_for="1.80",
        expected_goals_against="0.70",
        shots_for=14,
        shots_on_target_for=6,
    )
    draw = create_performance(
        days_ago=2,
        goals_for=1,
        goals_against=1,
        expected_goals_for="1.20",
        expected_goals_against="1.00",
        shots_for=10,
        shots_on_target_for=4,
    )
    loss = create_performance(
        days_ago=3,
        goals_for=0,
        goals_against=2,
        expected_goals_for="0.90",
        expected_goals_against="1.70",
        shots_for=8,
        shots_on_target_for=2,
    )

    return (
        draw,
        loss,
        win,
    )


def test_analyzer_orders_matches_newest_first() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances()
    )

    assert summary.form_string == "WDL"
    assert (
        summary.matches[0].played_at
        > summary.matches[1].played_at
        > summary.matches[2].played_at
    )


def test_analyzer_applies_recent_match_limit() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances(),
        limit=2,
    )

    assert summary.match_count == 2
    assert summary.form_string == "WD"


def test_analyzer_calculates_result_counts() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances()
    )

    assert summary.wins == 1
    assert summary.draws == 1
    assert summary.losses == 1
    assert summary.total_points == 4


def test_analyzer_calculates_goal_and_xg_averages() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances()
    )

    assert (
        summary.goals_for_average
        == Decimal("1.00")
    )
    assert (
        summary.goals_against_average
        == Decimal("1.00")
    )
    assert (
        summary.expected_goals_for_average
        == Decimal("1.30")
    )
    assert (
        summary.expected_goals_against_average
        == Decimal("1.13")
    )


def test_analyzer_calculates_shot_averages() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances()
    )

    assert (
        summary.shots_for_average
        == Decimal("10.67")
    )
    assert (
        summary.shots_on_target_for_average
        == Decimal("4.00")
    )


def test_analyzer_calculates_result_rates() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances()
    )

    assert summary.win_rate == Decimal("33.33")
    assert summary.draw_rate == Decimal("33.33")
    assert summary.loss_rate == Decimal("33.33")


def test_analyzer_calculates_clean_sheet_and_scoring_rates() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances()
    )

    assert (
        summary.clean_sheet_rate
        == Decimal("33.33")
    )
    assert (
        summary.failed_to_score_rate
        == Decimal("33.33")
    )


def test_analyzer_calculates_points_per_game() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances()
    )

    assert (
        summary.points_per_game
        == Decimal("1.33")
    )


def test_analyzer_without_limit_uses_all_matches() -> None:
    summary = TeamFormAnalyzer().analyze(
        create_performances(),
        limit=None,
    )

    assert summary.match_count == 3


def test_analyzer_rejects_empty_collection() -> None:
    with pytest.raises(
        ValueError,
        match="at least one performance",
    ):
        TeamFormAnalyzer().analyze(
            ()
        )


def test_analyzer_rejects_mixed_teams() -> None:
    performances = list(
        create_performances()
    )
    performances.append(
        create_performance(
            days_ago=4,
            team_name="Chelsea",
            goals_for=1,
            goals_against=0,
            expected_goals_for="1.00",
            expected_goals_against="0.50",
            shots_for=9,
            shots_on_target_for=3,
        )
    )

    with pytest.raises(
        ValueError,
        match="same team",
    ):
        TeamFormAnalyzer().analyze(
            performances
        )


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
    ],
)
def test_analyzer_rejects_non_positive_limit(
    limit: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        TeamFormAnalyzer().analyze(
            create_performances(),
            limit=limit,
        )


@pytest.mark.parametrize(
    "limit",
    [
        True,
        1.5,
    ],
)
def test_analyzer_rejects_invalid_limit_type(
    limit: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="integer or None",
    ):
        TeamFormAnalyzer().analyze(
            create_performances(),
            limit=limit,  # type: ignore[arg-type]
        )


def test_analyzer_rejects_invalid_performance_type() -> None:
    with pytest.raises(
        TypeError,
        match="TeamMatchPerformance objects",
    ):
        TeamFormAnalyzer().analyze(
            [
                object(),
            ]  # type: ignore[list-item]
        )