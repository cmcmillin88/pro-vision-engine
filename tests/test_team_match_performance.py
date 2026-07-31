"""Tests for individual team match performances."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
    TeamMatchResult,
)


def create_performance(
    **overrides: object,
) -> TeamMatchPerformance:
    """Create one valid test performance."""

    values: dict[str, object] = {
        "team_name": "Arsenal",
        "opponent_name": "Chelsea",
        "played_at": datetime(
            2026,
            8,
            1,
            15,
            0,
            tzinfo=timezone.utc,
        ),
        "venue": MatchVenue.HOME,
        "goals_for": 2,
        "goals_against": 1,
        "expected_goals_for": Decimal("1.70"),
        "expected_goals_against": Decimal("0.90"),
        "shots_for": 14,
        "shots_against": 8,
        "shots_on_target_for": 6,
        "shots_on_target_against": 3,
        "possession_percentage": Decimal("57.5"),
        "competition": "Premier League",
    }
    values.update(
        overrides
    )

    return TeamMatchPerformance(
        **values  # type: ignore[arg-type]
    )


def test_performance_normalizes_input_values() -> None:
    performance = create_performance(
        team_name="  Arsenal  ",
        opponent_name="  Chelsea FC  ",
        expected_goals_for="1.70",
        expected_goals_against=0.9,
        possession_percentage="57.5",
        competition="  Premier   League  ",
    )

    assert performance.team_name == "Arsenal"
    assert performance.opponent_name == "Chelsea FC"
    assert (
        performance.expected_goals_for
        == Decimal("1.70")
    )
    assert (
        performance.expected_goals_against
        == Decimal("0.9")
    )
    assert (
        performance.possession_percentage
        == Decimal("57.5")
    )
    assert performance.competition == "Premier League"


@pytest.mark.parametrize(
    (
        "goals_for",
        "goals_against",
        "expected_result",
        "expected_points",
    ),
    [
        (
            2,
            1,
            TeamMatchResult.WIN,
            3,
        ),
        (
            1,
            1,
            TeamMatchResult.DRAW,
            1,
        ),
        (
            0,
            2,
            TeamMatchResult.LOSS,
            0,
        ),
    ],
)
def test_result_and_points_are_calculated(
    goals_for: int,
    goals_against: int,
    expected_result: TeamMatchResult,
    expected_points: int,
) -> None:
    performance = create_performance(
        goals_for=goals_for,
        goals_against=goals_against,
    )

    assert performance.result is expected_result
    assert performance.points == expected_points


def test_performance_calculates_differences() -> None:
    performance = create_performance()

    assert performance.goal_difference == 1
    assert (
        performance.expected_goal_difference
        == Decimal("0.80")
    )
    assert (
        performance.finishing_delta
        == Decimal("0.30")
    )
    assert (
        performance.goal_prevention_delta
        == Decimal("-0.10")
    )
    assert performance.kept_clean_sheet is False
    assert performance.failed_to_score is False


def test_possession_can_be_omitted() -> None:
    performance = create_performance(
        possession_percentage=None
    )

    assert performance.possession_percentage is None


@pytest.mark.parametrize(
    "field_name",
    [
        "goals_for",
        "goals_against",
        "shots_for",
        "shots_against",
        "shots_on_target_for",
        "shots_on_target_against",
    ],
)
def test_performance_rejects_negative_integer_statistics(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        create_performance(
            **{
                field_name: -1,
            }
        )


def test_shots_on_target_for_cannot_exceed_shots() -> None:
    with pytest.raises(
        ValueError,
        match="cannot exceed shots_for",
    ):
        create_performance(
            shots_for=4,
            shots_on_target_for=5,
        )


def test_shots_on_target_against_cannot_exceed_shots() -> None:
    with pytest.raises(
        ValueError,
        match="cannot exceed shots_against",
    ):
        create_performance(
            shots_against=4,
            shots_on_target_against=5,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "expected_goals_for",
        "expected_goals_against",
    ],
)
def test_performance_rejects_negative_xg(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        create_performance(
            **{
                field_name: Decimal("-0.01"),
            }
        )


@pytest.mark.parametrize(
    "possession",
    [
        Decimal("-0.01"),
        Decimal("100.01"),
    ],
)
def test_performance_rejects_invalid_possession(
    possession: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 100",
    ):
        create_performance(
            possession_percentage=possession
        )


def test_performance_rejects_naive_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="timezone information",
    ):
        create_performance(
            played_at=datetime(
                2026,
                8,
                1,
                15,
                0,
            )
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "team_name",
        "opponent_name",
    ],
)
def test_performance_rejects_empty_team_names(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        create_performance(
            **{
                field_name: "   ",
            }
        )


def test_performance_rejects_same_team_and_opponent() -> None:
    with pytest.raises(
        ValueError,
        match="must be different",
    ):
        create_performance(
            team_name="Arsenal",
            opponent_name="arsenal",
        )


def test_performance_rejects_invalid_venue() -> None:
    with pytest.raises(
        TypeError,
        match="must be a MatchVenue",
    ):
        create_performance(
            venue="home"
        )


def test_performance_is_immutable() -> None:
    performance = create_performance()

    with pytest.raises(
        FrozenInstanceError
    ):
        performance.goals_for = 3  # type: ignore[misc]