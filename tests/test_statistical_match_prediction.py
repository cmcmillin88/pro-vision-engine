"""Tests for statistical match prediction models."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.outcome import Outcome
from src.models.statistical_match_prediction import (
    ScorelineProbability,
    StatisticalMatchPrediction,
    StatisticalOutcomeProbabilities,
)
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


def create_form(
    *,
    team_name: str,
    opponent_name: str,
) -> TeamFormSummary:
    """Create one compact team-form summary."""

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
        expected_goals_for=Decimal("1.50"),
        expected_goals_against=Decimal("1.00"),
        shots_for=12,
        shots_against=8,
        shots_on_target_for=5,
        shots_on_target_against=3,
    )

    return TeamFormSummary(
        team_name=team_name,
        matches=(match,),
        goals_for_average=Decimal("1.00"),
        goals_against_average=Decimal("0.00"),
        expected_goals_for_average=Decimal("1.50"),
        expected_goals_against_average=Decimal("1.00"),
        shots_for_average=Decimal("12.00"),
        shots_on_target_for_average=Decimal("5.00"),
        points_per_game=Decimal("3.00"),
        win_rate=Decimal("100.00"),
        draw_rate=Decimal("0.00"),
        loss_rate=Decimal("0.00"),
        clean_sheet_rate=Decimal("100.00"),
        failed_to_score_rate=Decimal("0.00"),
    )


def create_comparison() -> TeamFormComparison:
    """Create one valid form comparison."""

    return TeamFormComparison(
        home_form=create_form(
            team_name="Arsenal",
            opponent_name="Tottenham",
        ),
        away_form=create_form(
            team_name="Chelsea",
            opponent_name="Liverpool",
        ),
        projected_home_xg=Decimal("1.65"),
        projected_away_xg=Decimal("1.00"),
        projected_total_xg=Decimal("2.65"),
        projected_xg_difference=Decimal("0.65"),
        form_xg_difference=Decimal("1.30"),
        points_per_game_difference=Decimal("1.00"),
        shots_on_target_difference=Decimal("2.00"),
        lean=MatchupLean.HOME,
        strength=FormEdgeStrength.CLEAR,
    )


def create_prediction() -> StatisticalMatchPrediction:
    """Create one small valid score matrix."""

    scorelines = (
        ScorelineProbability(
            home_goals=0,
            away_goals=0,
            probability=Decimal("40.00"),
        ),
        ScorelineProbability(
            home_goals=1,
            away_goals=0,
            probability=Decimal("30.00"),
        ),
        ScorelineProbability(
            home_goals=0,
            away_goals=1,
            probability=Decimal("20.00"),
        ),
        ScorelineProbability(
            home_goals=1,
            away_goals=1,
            probability=Decimal("10.00"),
        ),
    )

    return StatisticalMatchPrediction(
        comparison=create_comparison(),
        outcome_probabilities=(
            StatisticalOutcomeProbabilities(
                home=Decimal("30.00"),
                draw=Decimal("50.00"),
                away=Decimal("20.00"),
            )
        ),
        scorelines=scorelines,
        included_probability_mass=Decimal("99.500000"),
        maximum_goals=1,
    )


def test_outcome_probabilities_expose_values_and_favorite() -> None:
    probabilities = StatisticalOutcomeProbabilities(
        home=Decimal("52.58"),
        draw=Decimal("24.51"),
        away=Decimal("22.91"),
    )

    assert probabilities.total == Decimal("100.00")
    assert probabilities.favorite_outcome is Outcome.HOME
    assert probabilities.confidence_margin == Decimal("28.07")
    assert (
        probabilities.for_outcome(
            Outcome.DRAW
        )
        == Decimal("24.51")
    )


def test_outcome_probabilities_reject_invalid_total() -> None:
    with pytest.raises(
        ValueError,
        match="exactly 100.00",
    ):
        StatisticalOutcomeProbabilities(
            home=Decimal("50.00"),
            draw=Decimal("25.00"),
            away=Decimal("24.00"),
        )


def test_scoreline_exposes_result_helpers() -> None:
    scoreline = ScorelineProbability(
        home_goals=2,
        away_goals=1,
        probability=Decimal("12.50"),
    )

    assert scoreline.scoreline == "2-1"
    assert scoreline.total_goals == 3
    assert scoreline.result is Outcome.HOME
    assert scoreline.both_teams_to_score is True


def test_scoreline_rejects_negative_goals() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        ScorelineProbability(
            home_goals=-1,
            away_goals=0,
            probability=Decimal("10.00"),
        )


def test_prediction_exposes_summary_helpers() -> None:
    prediction = create_prediction()

    assert prediction.home_team_name == "Arsenal"
    assert prediction.away_team_name == "Chelsea"
    assert prediction.favorite_outcome is Outcome.DRAW
    assert prediction.confidence_margin == Decimal("20.00")
    assert prediction.most_likely_scoreline.scoreline == "0-0"
    assert (
        prediction.truncated_probability_mass
        == Decimal("0.500000")
    )


def test_top_scorelines_validates_limit() -> None:
    prediction = create_prediction()

    assert len(
        prediction.top_scorelines(
            2
        )
    ) == 2

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        prediction.top_scorelines(
            0
        )


def test_prediction_rejects_duplicate_scorelines() -> None:
    prediction = create_prediction()
    duplicated = (
        prediction.scorelines[0],
        prediction.scorelines[1],
        prediction.scorelines[2],
        prediction.scorelines[0],
    )

    with pytest.raises(
        ValueError,
        match="duplicates",
    ):
        StatisticalMatchPrediction(
            comparison=prediction.comparison,
            outcome_probabilities=(
                prediction.outcome_probabilities
            ),
            scorelines=duplicated,
            included_probability_mass=(
                prediction.included_probability_mass
            ),
            maximum_goals=1,
        )


def test_prediction_rejects_unordered_scorelines() -> None:
    prediction = create_prediction()
    unordered = (
        prediction.scorelines[1],
        prediction.scorelines[0],
        prediction.scorelines[2],
        prediction.scorelines[3],
    )

    with pytest.raises(
        ValueError,
        match="ordered by probability",
    ):
        StatisticalMatchPrediction(
            comparison=prediction.comparison,
            outcome_probabilities=(
                prediction.outcome_probabilities
            ),
            scorelines=unordered,
            included_probability_mass=(
                prediction.included_probability_mass
            ),
            maximum_goals=1,
        )


def test_prediction_rejects_scoreline_outside_maximum() -> None:
    prediction = create_prediction()
    invalid_scorelines = (
        prediction.scorelines[0],
        prediction.scorelines[1],
        prediction.scorelines[2],
        ScorelineProbability(
            home_goals=2,
            away_goals=1,
            probability=Decimal("10.00"),
        ),
    )

    with pytest.raises(
        ValueError,
        match="exceeds maximum_goals",
    ):
        StatisticalMatchPrediction(
            comparison=prediction.comparison,
            outcome_probabilities=(
                prediction.outcome_probabilities
            ),
            scorelines=invalid_scorelines,
            included_probability_mass=(
                prediction.included_probability_mass
            ),
            maximum_goals=1,
        )