"""Tests for statistical-market comparison models."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_snapshot import MarketSnapshot
from src.models.outcome import Outcome
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
    ModelValueLevel,
    ProbabilityEvidenceDirection,
    StatisticalMarketComparisonReport,
)
from src.models.team_form import TeamFormSummary
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.market_analysis_engine import (
    MarketAnalysisEngine,
)
from src.services.poisson_match_predictor import (
    PoissonMatchPredictor,
)
from src.services.statistical_market_comparison_analyzer import (
    StatisticalMarketComparisonAnalyzer,
)
from src.services.team_form_comparison_analyzer import (
    TeamFormComparisonAnalyzer,
)


def create_form(
    *,
    team_name: str,
    opponent_name: str,
    xg_for: str,
    xg_against: str,
) -> TeamFormSummary:
    """Create one compact statistical form summary."""

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
        expected_goals_for=Decimal(xg_for),
        expected_goals_against=Decimal(xg_against),
        shots_for=12,
        shots_against=10,
        shots_on_target_for=5,
        shots_on_target_against=4,
    )

    return TeamFormSummary(
        team_name=team_name,
        matches=(match,),
        goals_for_average=Decimal("1.00"),
        goals_against_average=Decimal("1.00"),
        expected_goals_for_average=Decimal(xg_for),
        expected_goals_against_average=Decimal(xg_against),
        shots_for_average=Decimal("12.00"),
        shots_on_target_for_average=Decimal("5.00"),
        points_per_game=Decimal("1.50"),
        win_rate=Decimal("33.33"),
        draw_rate=Decimal("33.34"),
        loss_rate=Decimal("33.33"),
        clean_sheet_rate=Decimal("0.00"),
        failed_to_score_rate=Decimal("0.00"),
    )


def create_report() -> StatisticalMarketComparisonReport:
    """Create the standard complete comparison."""

    home_form = create_form(
        team_name="Arsenal",
        opponent_name="Tottenham",
        xg_for="1.80",
        xg_against="0.80",
    )
    away_form = create_form(
        team_name="Chelsea",
        opponent_name="Liverpool",
        xg_for="1.20",
        xg_against="1.50",
    )
    form_comparison = (
        TeamFormComparisonAnalyzer().analyze(
            home_form,
            away_form,
        )
    )
    prediction = PoissonMatchPredictor().predict(
        form_comparison
    )

    earlier = MarketSnapshot(
        captured_at=datetime(
            2026,
            8,
            20,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        odds=ThreeWayOdds(
            Decimal("2.00"),
            Decimal("3.50"),
            Decimal("4.00"),
        ),
        public_percentages=ThreeWayPercentages(
            Decimal("55"),
            Decimal("25"),
            Decimal("20"),
        ),
        source_name="combined-market",
    )
    later = MarketSnapshot(
        captured_at=datetime(
            2026,
            8,
            20,
            14,
            0,
            tzinfo=timezone.utc,
        ),
        odds=ThreeWayOdds(
            Decimal("1.80"),
            Decimal("3.80"),
            Decimal("4.50"),
        ),
        public_percentages=ThreeWayPercentages(
            Decimal("60"),
            Decimal("23"),
            Decimal("17"),
        ),
        source_name="combined-market",
    )
    market_analysis = MarketAnalysisEngine().analyze(
        earlier,
        later,
    )

    return (
        StatisticalMarketComparisonAnalyzer()
        .analyze(
            prediction,
            market_analysis,
        )
    )


def test_outcome_comparison_exposes_helpers() -> None:
    comparison = create_report().for_outcome(
        Outcome.AWAY
    )

    assert (
        comparison.absolute_statistical_market_gap
        == Decimal("1.56")
    )
    assert comparison.has_model_value is True
    assert comparison.has_strong_model_value is False
    assert comparison.model_and_market_agree is True


def test_report_exposes_favorite_summary() -> None:
    report = create_report()

    assert report.statistical_favorite is Outcome.HOME
    assert report.market_favorite is Outcome.HOME
    assert report.public_favorite is Outcome.HOME
    assert report.statistical_market_agree is True
    assert report.full_consensus is True


def test_report_filters_model_value_outcomes() -> None:
    report = create_report()

    assert tuple(
        comparison.outcome
        for comparison in report.model_value_outcomes
    ) == (
        Outcome.AWAY,
    )
    assert report.strong_model_value_outcomes == ()
    assert (
        report.strongest_model_value.outcome
        is Outcome.AWAY
    )


def test_report_identifies_strongest_market_disagreement() -> None:
    report = create_report()

    strongest = report.strongest_market_disagreement

    assert strongest.outcome is Outcome.AWAY
    assert (
        strongest.statistical_market_gap
        == Decimal("1.56")
    )


def test_report_rejects_unordered_outcomes() -> None:
    report = create_report()

    with pytest.raises(
        ValueError,
        match="official 1-X-2 order",
    ):
        StatisticalMarketComparisonReport(
            statistical_prediction=(
                report.statistical_prediction
            ),
            market_analysis=report.market_analysis,
            outcome_comparisons=(
                report.outcome_comparisons[2],
                report.outcome_comparisons[1],
                report.outcome_comparisons[0],
            ),
            conflict_level=report.conflict_level,
        )


def test_outcome_rejects_inconsistent_gap() -> None:
    comparison = create_report().for_outcome(
        Outcome.HOME
    )

    with pytest.raises(
        ValueError,
        match="statistical_market_gap",
    ):
        replace(
            comparison,
            statistical_market_gap=Decimal("0.00"),
        )


def test_outcome_rejects_invalid_direction_sign() -> None:
    comparison = create_report().for_outcome(
        Outcome.AWAY
    )

    with pytest.raises(
        ValueError,
        match="negative statistical-market gap",
    ):
        replace(
            comparison,
            evidence_direction=(
                ProbabilityEvidenceDirection
                .MARKET_HIGHER
            ),
        )


def test_report_rejects_mismatched_source_probability() -> None:
    report = create_report()
    home = report.for_outcome(
        Outcome.HOME
    )
    changed_home = replace(
        home,
        statistical_probability=Decimal("53.58"),
        statistical_market_gap=Decimal("0.21"),
        statistical_public_edge=Decimal("-6.42"),
        evidence_direction=(
            ProbabilityEvidenceDirection.AGREEMENT
        ),
        model_value_level=ModelValueLevel.NONE,
    )

    with pytest.raises(
        ValueError,
        match="does not match the prediction",
    ):
        StatisticalMarketComparisonReport(
            statistical_prediction=(
                report.statistical_prediction
            ),
            market_analysis=report.market_analysis,
            outcome_comparisons=(
                changed_home,
                report.outcome_comparisons[1],
                report.outcome_comparisons[2],
            ),
            conflict_level=(
                ModelMarketConflictLevel.LOW
            ),
        )