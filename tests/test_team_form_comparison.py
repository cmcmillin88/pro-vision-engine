"""Tests for statistical team-form comparison models."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.team_form import TeamFormSummary
from src.models.team_form_comparison import (
    FormEdgeStrength,
    MatchupLean,
    TeamFormComparison,
)
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)


def create_summary(
    *,
    team_name: str,
    opponent_name: str,
    expected_goals_for: str,
    expected_goals_against: str,
    points_per_game: str,
    shots_on_target: str,
) -> TeamFormSummary:
    """Create one compact form summary."""

    match = TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=datetime(
            2026,
            8,
            20,
            15,
            0,
            tzinfo=timezone.utc,
        ),
        venue=MatchVenue.HOME,
        goals_for=1,
        goals_against=0,
        expected_goals_for=Decimal(
            expected_goals_for
        ),
        expected_goals_against=Decimal(
            expected_goals_against
        ),
        shots_for=12,
        shots_against=8,
        shots_on_target_for=int(
            Decimal(shots_on_target)
        ),
        shots_on_target_against=3,
    )

    return TeamFormSummary(
        team_name=team_name,
        matches=(match,),
        goals_for_average=Decimal("1.00"),
        goals_against_average=Decimal("0.00"),
        expected_goals_for_average=Decimal(
            expected_goals_for
        ),
        expected_goals_against_average=Decimal(
            expected_goals_against
        ),
        shots_for_average=Decimal("12.00"),
        shots_on_target_for_average=Decimal(
            shots_on_target
        ),
        points_per_game=Decimal(
            points_per_game
        ),
        win_rate=Decimal("100.00"),
        draw_rate=Decimal("0.00"),
        loss_rate=Decimal("0.00"),
        clean_sheet_rate=Decimal("100.00"),
        failed_to_score_rate=Decimal("0.00"),
    )


def create_report() -> TeamFormComparison:
    """Create one valid comparison report."""

    home_form = create_summary(
        team_name="Arsenal",
        opponent_name="Tottenham",
        expected_goals_for="1.80",
        expected_goals_against="0.80",
        points_per_game="2.33",
        shots_on_target="6.00",
    )
    away_form = create_summary(
        team_name="Chelsea",
        opponent_name="Liverpool",
        expected_goals_for="1.20",
        expected_goals_against="1.50",
        points_per_game="1.00",
        shots_on_target="4.00",
    )

    return TeamFormComparison(
        home_form=home_form,
        away_form=away_form,
        projected_home_xg=Decimal("1.65"),
        projected_away_xg=Decimal("1.00"),
        projected_total_xg=Decimal("2.65"),
        projected_xg_difference=Decimal("0.65"),
        form_xg_difference=Decimal("1.30"),
        points_per_game_difference=Decimal("1.33"),
        shots_on_target_difference=Decimal("2.00"),
        lean=MatchupLean.HOME,
        strength=FormEdgeStrength.CLEAR,
    )


def test_comparison_exposes_matchup_helpers() -> None:
    report = create_report()

    assert report.home_team_name == "Arsenal"
    assert report.away_team_name == "Chelsea"
    assert report.projected_scoreline == "1.65-1.00"
    assert report.lean_team_name == "Arsenal"
    assert report.home_has_edge is True
    assert report.away_has_edge is False
    assert report.is_balanced is False


def test_comparison_rejects_same_team() -> None:
    report = create_report()
    same_team_form = create_summary(
        team_name="Arsenal",
        opponent_name="Liverpool",
        expected_goals_for="1.20",
        expected_goals_against="1.50",
        points_per_game="1.00",
        shots_on_target="4.00",
    )

    with pytest.raises(
        ValueError,
        match="must be different",
    ):
        replace(
            report,
            away_form=same_team_form,
        )


def test_comparison_rejects_total_xg_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="projected_total_xg",
    ):
        replace(
            create_report(),
            projected_total_xg=Decimal("2.50"),
        )


def test_comparison_rejects_xg_difference_mismatch() -> None:
    with pytest.raises(
        ValueError,
        match="projected_xg_difference",
    ):
        replace(
            create_report(),
            projected_xg_difference=Decimal("0.50"),
        )


def test_balanced_lean_requires_balanced_strength() -> None:
    with pytest.raises(
        ValueError,
        match="balanced edge strength",
    ):
        replace(
            create_report(),
            lean=MatchupLean.BALANCED,
            strength=FormEdgeStrength.CLEAR,
        )


def test_away_lean_requires_negative_xg_difference() -> None:
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        replace(
            create_report(),
            lean=MatchupLean.AWAY,
        )