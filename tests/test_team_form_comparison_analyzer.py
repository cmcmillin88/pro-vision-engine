"""Tests for statistical team-form comparison analysis."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.team_form import TeamFormSummary
from src.models.team_form_comparison import (
    FormEdgeStrength,
    MatchupLean,
)
from src.models.team_form_comparison_thresholds import (
    TeamFormComparisonThresholds,
)
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.services.team_form_comparison_analyzer import (
    TeamFormComparisonAnalyzer,
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
    """Create one configurable form summary."""

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


def create_sample_forms() -> tuple[
    TeamFormSummary,
    TeamFormSummary,
]:
    """Create the standard home and away summaries."""

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

    return home_form, away_form


def test_analyzer_calculates_projected_xg() -> None:
    home_form, away_form = create_sample_forms()

    comparison = TeamFormComparisonAnalyzer().analyze(
        home_form,
        away_form,
    )

    assert (
        comparison.projected_home_xg
        == Decimal("1.65")
    )
    assert (
        comparison.projected_away_xg
        == Decimal("1.00")
    )
    assert (
        comparison.projected_total_xg
        == Decimal("2.65")
    )


def test_analyzer_calculates_statistical_differences() -> None:
    home_form, away_form = create_sample_forms()

    comparison = TeamFormComparisonAnalyzer().analyze(
        home_form,
        away_form,
    )

    assert (
        comparison.projected_xg_difference
        == Decimal("0.65")
    )
    assert (
        comparison.form_xg_difference
        == Decimal("1.30")
    )
    assert (
        comparison.points_per_game_difference
        == Decimal("1.33")
    )
    assert (
        comparison.shots_on_target_difference
        == Decimal("2.00")
    )


def test_sample_matchup_has_clear_home_lean() -> None:
    home_form, away_form = create_sample_forms()

    comparison = TeamFormComparisonAnalyzer().analyze(
        home_form,
        away_form,
    )

    assert comparison.lean is MatchupLean.HOME
    assert (
        comparison.strength
        is FormEdgeStrength.CLEAR
    )
    assert comparison.lean_team_name == "Arsenal"


def test_large_negative_edge_creates_strong_away_lean() -> None:
    home_form = create_summary(
        team_name="Arsenal",
        opponent_name="Tottenham",
        expected_goals_for="0.80",
        expected_goals_against="1.80",
        points_per_game="0.70",
        shots_on_target="3.00",
    )
    away_form = create_summary(
        team_name="Chelsea",
        opponent_name="Liverpool",
        expected_goals_for="2.10",
        expected_goals_against="0.70",
        points_per_game="2.40",
        shots_on_target="7.00",
    )

    comparison = TeamFormComparisonAnalyzer().analyze(
        home_form,
        away_form,
    )

    assert (
        comparison.projected_xg_difference
        == Decimal("-1.20")
    )
    assert comparison.lean is MatchupLean.AWAY
    assert (
        comparison.strength
        is FormEdgeStrength.STRONG
    )


def test_equal_projection_creates_balanced_matchup() -> None:
    home_form = create_summary(
        team_name="Arsenal",
        opponent_name="Tottenham",
        expected_goals_for="1.40",
        expected_goals_against="1.20",
        points_per_game="1.50",
        shots_on_target="5.00",
    )
    away_form = create_summary(
        team_name="Chelsea",
        opponent_name="Liverpool",
        expected_goals_for="1.40",
        expected_goals_against="1.20",
        points_per_game="1.50",
        shots_on_target="5.00",
    )

    comparison = TeamFormComparisonAnalyzer().analyze(
        home_form,
        away_form,
    )

    assert comparison.lean is MatchupLean.BALANCED
    assert (
        comparison.strength
        is FormEdgeStrength.BALANCED
    )
    assert comparison.is_balanced is True


def test_custom_thresholds_change_matchup_lean() -> None:
    home_form, away_form = create_sample_forms()
    thresholds = TeamFormComparisonThresholds(
        balanced_xg_margin=Decimal("0.70"),
        clear_xg_margin=Decimal("0.80"),
        strong_xg_margin=Decimal("1.20"),
    )

    comparison = TeamFormComparisonAnalyzer(
        thresholds
    ).analyze(
        home_form,
        away_form,
    )

    assert comparison.lean is MatchupLean.BALANCED
    assert (
        comparison.strength
        is FormEdgeStrength.BALANCED
    )


def test_analyzer_rejects_invalid_home_form() -> None:
    _, away_form = create_sample_forms()

    with pytest.raises(
        TypeError,
        match="home_form",
    ):
        TeamFormComparisonAnalyzer().analyze(
            object(),  # type: ignore[arg-type]
            away_form,
        )


def test_analyzer_rejects_invalid_away_form() -> None:
    home_form, _ = create_sample_forms()

    with pytest.raises(
        TypeError,
        match="away_form",
    ):
        TeamFormComparisonAnalyzer().analyze(
            home_form,
            object(),  # type: ignore[arg-type]
        )


def test_analyzer_rejects_same_team() -> None:
    home_form, _ = create_sample_forms()
    away_form = create_summary(
        team_name="arsenal",
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
        TeamFormComparisonAnalyzer().analyze(
            home_form,
            away_form,
        )