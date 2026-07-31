"""Tests for the complete statistical-analysis report."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.outcome import Outcome
from src.models.statistical_analysis import (
    StatisticalAnalysisReport,
)
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.services.poisson_match_predictor import (
    PoissonMatchPredictor,
)
from src.services.statistical_analysis_engine import (
    StatisticalAnalysisEngine,
)
from src.services.team_form_analyzer import (
    TeamFormAnalyzer,
)
from src.services.team_form_comparison_analyzer import (
    TeamFormComparisonAnalyzer,
)


def create_performance(
    *,
    team_name: str,
    opponent_name: str,
    venue: MatchVenue,
    xg_for: str,
    xg_against: str,
) -> TeamMatchPerformance:
    """Create one compact statistical performance."""

    return TeamMatchPerformance(
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
        venue=venue,
        goals_for=1,
        goals_against=1,
        expected_goals_for=Decimal(xg_for),
        expected_goals_against=Decimal(xg_against),
        shots_for=12,
        shots_against=10,
        shots_on_target_for=5,
        shots_on_target_against=4,
    )


def create_report() -> StatisticalAnalysisReport:
    """Create one valid complete statistical report."""

    home_performances = (
        create_performance(
            team_name="Arsenal",
            opponent_name="Tottenham",
            venue=MatchVenue.HOME,
            xg_for="1.80",
            xg_against="0.80",
        ),
    )
    away_performances = (
        create_performance(
            team_name="Chelsea",
            opponent_name="Liverpool",
            venue=MatchVenue.AWAY,
            xg_for="1.20",
            xg_against="1.50",
        ),
    )

    return StatisticalAnalysisEngine().analyze(
        home_performances,
        away_performances,
    )


def test_report_exposes_complete_component_chain() -> None:
    report = create_report()

    assert (
        report.form_comparison.home_form
        == report.home_form
    )
    assert (
        report.form_comparison.away_form
        == report.away_form
    )
    assert (
        report.prediction.comparison
        == report.form_comparison
    )


def test_report_exposes_match_summary() -> None:
    report = create_report()

    assert report.home_team_name == "Arsenal"
    assert report.away_team_name == "Chelsea"
    assert report.projected_scoreline == "1.65-1.00"
    assert report.home_match_count == 1
    assert report.away_match_count == 1


def test_report_exposes_prediction_helpers() -> None:
    report = create_report()

    assert report.favorite_outcome is Outcome.HOME
    assert (
        report.probability_for(
            Outcome.HOME
        )
        == Decimal("52.58")
    )
    assert report.confidence_margin == Decimal("28.07")
    assert (
        report.most_likely_scoreline.scoreline
        == "1-0"
    )
    assert len(
        report.top_scorelines(
            3
        )
    ) == 3


def test_report_contains_correct_venue_contexts() -> None:
    report = create_report()

    assert all(
        match.venue is MatchVenue.HOME
        for match in report.home_form.matches
    )
    assert all(
        match.venue is MatchVenue.AWAY
        for match in report.away_form.matches
    )


def test_report_rejects_invalid_home_form() -> None:
    report = create_report()

    with pytest.raises(
        TypeError,
        match="home_form",
    ):
        StatisticalAnalysisReport(
            home_form=object(),  # type: ignore[arg-type]
            away_form=report.away_form,
            form_comparison=report.form_comparison,
            prediction=report.prediction,
        )


def test_report_rejects_wrong_home_venue_context() -> None:
    report = create_report()
    wrong_home_form = TeamFormAnalyzer().analyze(
        (
            create_performance(
                team_name="Arsenal",
                opponent_name="Tottenham",
                venue=MatchVenue.AWAY,
                xg_for="1.80",
                xg_against="0.80",
            ),
        ),
        venue=MatchVenue.AWAY,
    )
    comparison = TeamFormComparisonAnalyzer().analyze(
        wrong_home_form,
        report.away_form,
    )
    prediction = PoissonMatchPredictor().predict(
        comparison
    )

    with pytest.raises(
        ValueError,
        match="only home performances",
    ):
        StatisticalAnalysisReport(
            home_form=wrong_home_form,
            away_form=report.away_form,
            form_comparison=comparison,
            prediction=prediction,
        )


def test_report_rejects_mismatched_form_comparison() -> None:
    report = create_report()
    other_home_form = TeamFormAnalyzer().analyze(
        (
            create_performance(
                team_name="Liverpool",
                opponent_name="Everton",
                venue=MatchVenue.HOME,
                xg_for="2.00",
                xg_against="0.60",
            ),
        ),
        venue=MatchVenue.HOME,
    )
    other_comparison = (
        TeamFormComparisonAnalyzer().analyze(
            other_home_form,
            report.away_form,
        )
    )
    other_prediction = PoissonMatchPredictor().predict(
        other_comparison
    )

    with pytest.raises(
        ValueError,
        match="supplied home and away forms",
    ):
        StatisticalAnalysisReport(
            home_form=report.home_form,
            away_form=report.away_form,
            form_comparison=other_comparison,
            prediction=other_prediction,
        )


def test_report_rejects_mismatched_prediction() -> None:
    report = create_report()
    other_home_form = TeamFormAnalyzer().analyze(
        (
            create_performance(
                team_name="Liverpool",
                opponent_name="Everton",
                venue=MatchVenue.HOME,
                xg_for="2.00",
                xg_against="0.60",
            ),
        ),
        venue=MatchVenue.HOME,
    )
    other_comparison = (
        TeamFormComparisonAnalyzer().analyze(
            other_home_form,
            report.away_form,
        )
    )
    other_prediction = PoissonMatchPredictor().predict(
        other_comparison
    )

    with pytest.raises(
        ValueError,
        match="supplied form comparison",
    ):
        StatisticalAnalysisReport(
            home_form=report.home_form,
            away_form=report.away_form,
            form_comparison=report.form_comparison,
            prediction=other_prediction,
        )