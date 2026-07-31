"""Tests for Poisson-based football predictions."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.outcome import Outcome
from src.models.poisson_prediction_settings import (
    PoissonPredictionSettings,
)
from src.models.team_form import TeamFormSummary
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.services.poisson_match_predictor import (
    PoissonMatchPredictor,
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
    points_per_game: str = "1.50",
    shots_on_target: int = 5,
) -> TeamFormSummary:
    """Create one configurable team-form summary."""

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
        goals_against=1,
        expected_goals_for=Decimal(
            expected_goals_for
        ),
        expected_goals_against=Decimal(
            expected_goals_against
        ),
        shots_for=12,
        shots_against=10,
        shots_on_target_for=shots_on_target,
        shots_on_target_against=4,
    )

    return TeamFormSummary(
        team_name=team_name,
        matches=(match,),
        goals_for_average=Decimal("1.00"),
        goals_against_average=Decimal("1.00"),
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
        win_rate=Decimal("33.33"),
        draw_rate=Decimal("33.34"),
        loss_rate=Decimal("33.33"),
        clean_sheet_rate=Decimal("0.00"),
        failed_to_score_rate=Decimal("0.00"),
    )


def create_sample_comparison():
    """Create the standard 1.65 against 1.00 projection."""

    home_form = create_summary(
        team_name="Arsenal",
        opponent_name="Tottenham",
        expected_goals_for="1.80",
        expected_goals_against="0.80",
        points_per_game="2.33",
        shots_on_target=6,
    )
    away_form = create_summary(
        team_name="Chelsea",
        opponent_name="Liverpool",
        expected_goals_for="1.20",
        expected_goals_against="1.50",
        points_per_game="1.00",
        shots_on_target=4,
    )

    return TeamFormComparisonAnalyzer().analyze(
        home_form,
        away_form,
    )


def test_predictor_calculates_expected_outcome_probabilities() -> None:
    prediction = PoissonMatchPredictor().predict(
        create_sample_comparison()
    )

    assert (
        prediction.probability_for(
            Outcome.HOME
        )
        == Decimal("52.58")
    )
    assert (
        prediction.probability_for(
            Outcome.DRAW
        )
        == Decimal("24.51")
    )
    assert (
        prediction.probability_for(
            Outcome.AWAY
        )
        == Decimal("22.91")
    )


def test_predictor_identifies_favorite_and_margin() -> None:
    prediction = PoissonMatchPredictor().predict(
        create_sample_comparison()
    )

    assert prediction.favorite_outcome is Outcome.HOME
    assert prediction.confidence_margin == Decimal("28.07")


def test_predictor_reports_included_probability_mass() -> None:
    prediction = PoissonMatchPredictor().predict(
        create_sample_comparison()
    )

    assert (
        prediction.included_probability_mass
        == Decimal("99.999862")
    )
    assert (
        prediction.truncated_probability_mass
        == Decimal("0.000138")
    )


def test_predictor_identifies_most_likely_scoreline() -> None:
    prediction = PoissonMatchPredictor().predict(
        create_sample_comparison()
    )
    scoreline = prediction.most_likely_scoreline

    assert scoreline.scoreline == "1-0"
    assert scoreline.probability == Decimal("11.66")


def test_predictor_returns_expected_top_five_scorelines() -> None:
    prediction = PoissonMatchPredictor().predict(
        create_sample_comparison()
    )

    assert tuple(
        scoreline.scoreline
        for scoreline in prediction.top_scorelines()
    ) == (
        "1-0",
        "1-1",
        "2-0",
        "2-1",
        "0-0",
    )


def test_predictor_creates_complete_score_matrix() -> None:
    prediction = PoissonMatchPredictor().predict(
        create_sample_comparison()
    )

    assert len(
        prediction.scorelines
    ) == 121


def test_outcome_probabilities_total_exactly_100() -> None:
    prediction = PoissonMatchPredictor().predict(
        create_sample_comparison()
    )

    assert (
        prediction.outcome_probabilities.total
        == Decimal("100.00")
    )


def test_stronger_away_projection_creates_away_favorite() -> None:
    home_form = create_summary(
        team_name="Arsenal",
        opponent_name="Tottenham",
        expected_goals_for="0.80",
        expected_goals_against="1.80",
    )
    away_form = create_summary(
        team_name="Chelsea",
        opponent_name="Liverpool",
        expected_goals_for="2.10",
        expected_goals_against="0.70",
    )
    comparison = TeamFormComparisonAnalyzer().analyze(
        home_form,
        away_form,
    )

    prediction = PoissonMatchPredictor().predict(
        comparison
    )

    assert prediction.favorite_outcome is Outcome.AWAY
    assert (
        prediction.probability_for(
            Outcome.AWAY
        )
        > prediction.probability_for(
            Outcome.HOME
        )
    )


def test_zero_xg_projection_creates_certain_nil_nil_draw() -> None:
    home_form = create_summary(
        team_name="Arsenal",
        opponent_name="Tottenham",
        expected_goals_for="0",
        expected_goals_against="0",
    )
    away_form = create_summary(
        team_name="Chelsea",
        opponent_name="Liverpool",
        expected_goals_for="0",
        expected_goals_against="0",
    )
    comparison = TeamFormComparisonAnalyzer().analyze(
        home_form,
        away_form,
    )

    prediction = PoissonMatchPredictor().predict(
        comparison
    )

    assert prediction.favorite_outcome is Outcome.DRAW
    assert (
        prediction.probability_for(
            Outcome.DRAW
        )
        == Decimal("100.00")
    )
    assert prediction.most_likely_scoreline.scoreline == "0-0"
    assert (
        prediction.most_likely_scoreline.probability
        == Decimal("100.00")
    )


def test_custom_maximum_goals_controls_matrix_size() -> None:
    settings = PoissonPredictionSettings(
        maximum_goals=5
    )

    prediction = PoissonMatchPredictor(
        settings
    ).predict(
        create_sample_comparison()
    )

    assert prediction.maximum_goals == 5
    assert len(prediction.scorelines) == 36
    assert (
        prediction.included_probability_mass
        == Decimal("99.243977")
    )


def test_predictor_rejects_insufficient_probability_mass() -> None:
    settings = PoissonPredictionSettings(
        maximum_goals=3
    )

    with pytest.raises(
        ValueError,
        match="below the configured minimum",
    ):
        PoissonMatchPredictor(
            settings
        ).predict(
            create_sample_comparison()
        )


def test_lower_minimum_mass_allows_smaller_matrix() -> None:
    settings = PoissonPredictionSettings(
        maximum_goals=3,
        minimum_included_mass=Decimal("80.00"),
    )

    prediction = PoissonMatchPredictor(
        settings
    ).predict(
        create_sample_comparison()
    )

    assert len(prediction.scorelines) == 16
    assert (
        prediction.included_probability_mass
        == Decimal("89.678762")
    )


def test_predictor_rejects_invalid_comparison() -> None:
    with pytest.raises(
        TypeError,
        match="requires a TeamFormComparison",
    ):
        PoissonMatchPredictor().predict(
            object()  # type: ignore[arg-type]
        )


def test_predictor_is_deterministic() -> None:
    comparison = create_sample_comparison()
    predictor = PoissonMatchPredictor()

    first_prediction = predictor.predict(
        comparison
    )
    second_prediction = predictor.predict(
        comparison
    )

    assert first_prediction == second_prediction