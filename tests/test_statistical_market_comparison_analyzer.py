"""Tests for statistical-market-public comparison analysis."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_snapshot import MarketSnapshot
from src.models.outcome import Outcome
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
    ModelValueLevel,
    ProbabilityEvidenceDirection,
)
from src.models.statistical_market_comparison_thresholds import (
    StatisticalMarketComparisonThresholds,
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


def create_prediction(
    *,
    home_xg_for: str = "1.80",
    home_xg_against: str = "0.80",
    away_xg_for: str = "1.20",
    away_xg_against: str = "1.50",
):
    """Create one statistical match prediction."""

    home_form = create_form(
        team_name="Arsenal",
        opponent_name="Tottenham",
        xg_for=home_xg_for,
        xg_against=home_xg_against,
    )
    away_form = create_form(
        team_name="Chelsea",
        opponent_name="Liverpool",
        xg_for=away_xg_for,
        xg_against=away_xg_against,
    )
    comparison = TeamFormComparisonAnalyzer().analyze(
        home_form,
        away_form,
    )

    return PoissonMatchPredictor().predict(
        comparison
    )


def create_market_analysis():
    """Create the standard market analysis."""

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

    return MarketAnalysisEngine().analyze(
        earlier,
        later,
    )


def test_analyzer_calculates_expected_probability_gaps() -> None:
    report = StatisticalMarketComparisonAnalyzer().analyze(
        create_prediction(),
        create_market_analysis(),
    )

    assert (
        report.for_outcome(
            Outcome.HOME
        ).statistical_market_gap
        == Decimal("-0.79")
    )
    assert (
        report.for_outcome(
            Outcome.DRAW
        ).statistical_market_gap
        == Decimal("-0.77")
    )
    assert (
        report.for_outcome(
            Outcome.AWAY
        ).statistical_market_gap
        == Decimal("1.56")
    )


def test_analyzer_calculates_expected_public_edges() -> None:
    report = StatisticalMarketComparisonAnalyzer().analyze(
        create_prediction(),
        create_market_analysis(),
    )

    assert (
        report.for_outcome(
            Outcome.HOME
        ).statistical_public_edge
        == Decimal("-7.42")
    )
    assert (
        report.for_outcome(
            Outcome.DRAW
        ).statistical_public_edge
        == Decimal("1.51")
    )
    assert (
        report.for_outcome(
            Outcome.AWAY
        ).statistical_public_edge
        == Decimal("5.91")
    )


def test_standard_example_has_model_market_agreement() -> None:
    report = StatisticalMarketComparisonAnalyzer().analyze(
        create_prediction(),
        create_market_analysis(),
    )

    assert all(
        comparison.evidence_direction
        is ProbabilityEvidenceDirection.AGREEMENT
        for comparison in report.outcome_comparisons
    )


def test_standard_example_identifies_away_model_value() -> None:
    report = StatisticalMarketComparisonAnalyzer().analyze(
        create_prediction(),
        create_market_analysis(),
    )
    away = report.for_outcome(
        Outcome.AWAY
    )

    assert (
        away.model_value_level
        is ModelValueLevel.VALUE
    )
    assert report.model_value_outcomes == (
        away,
    )


def test_standard_example_has_low_conflict() -> None:
    report = StatisticalMarketComparisonAnalyzer().analyze(
        create_prediction(),
        create_market_analysis(),
    )

    assert (
        report.conflict_level
        is ModelMarketConflictLevel.LOW
    )
    assert report.full_consensus is True
    assert report.has_high_conflict is False


def test_custom_agreement_margin_exposes_directions() -> None:
    thresholds = StatisticalMarketComparisonThresholds(
        agreement_margin=Decimal("0.50"),
        disagreement_warning=Decimal("5.00"),
        disagreement_strong=Decimal("10.00"),
    )
    report = StatisticalMarketComparisonAnalyzer(
        thresholds
    ).analyze(
        create_prediction(),
        create_market_analysis(),
    )

    assert (
        report.for_outcome(
            Outcome.HOME
        ).evidence_direction
        is ProbabilityEvidenceDirection.MARKET_HIGHER
    )
    assert (
        report.for_outcome(
            Outcome.DRAW
        ).evidence_direction
        is ProbabilityEvidenceDirection.MARKET_HIGHER
    )
    assert (
        report.for_outcome(
            Outcome.AWAY
        ).evidence_direction
        is (
            ProbabilityEvidenceDirection
            .STATISTICAL_HIGHER
        )
    )


def test_custom_warning_threshold_creates_medium_conflict() -> None:
    thresholds = StatisticalMarketComparisonThresholds(
        agreement_margin=Decimal("0.50"),
        disagreement_warning=Decimal("1.00"),
        disagreement_strong=Decimal("2.00"),
    )
    report = StatisticalMarketComparisonAnalyzer(
        thresholds
    ).analyze(
        create_prediction(),
        create_market_analysis(),
    )

    assert (
        report.conflict_level
        is ModelMarketConflictLevel.MEDIUM
    )


def test_opposing_statistical_favorite_creates_high_conflict() -> None:
    prediction = create_prediction(
        home_xg_for="0.80",
        home_xg_against="1.80",
        away_xg_for="2.10",
        away_xg_against="0.70",
    )
    report = StatisticalMarketComparisonAnalyzer().analyze(
        prediction,
        create_market_analysis(),
    )

    assert report.statistical_favorite is Outcome.AWAY
    assert report.market_favorite is Outcome.HOME
    assert (
        report.conflict_level
        is ModelMarketConflictLevel.HIGH
    )
    assert report.has_high_conflict is True


def test_opposing_prediction_contains_strong_model_value() -> None:
    prediction = create_prediction(
        home_xg_for="0.80",
        home_xg_against="1.80",
        away_xg_for="2.10",
        away_xg_against="0.70",
    )
    report = StatisticalMarketComparisonAnalyzer().analyze(
        prediction,
        create_market_analysis(),
    )

    assert report.strong_model_value_outcomes
    assert (
        report.strongest_model_value.outcome
        is Outcome.AWAY
    )


def test_analyzer_rejects_invalid_prediction() -> None:
    with pytest.raises(
        TypeError,
        match="StatisticalMatchPrediction",
    ):
        StatisticalMarketComparisonAnalyzer().analyze(
            object(),  # type: ignore[arg-type]
            create_market_analysis(),
        )


def test_analyzer_rejects_invalid_market_analysis() -> None:
    with pytest.raises(
        TypeError,
        match="MarketAnalysisReport",
    ):
        StatisticalMarketComparisonAnalyzer().analyze(
            create_prediction(),
            object(),  # type: ignore[arg-type]
        )


def test_analyzer_is_deterministic() -> None:
    prediction = create_prediction()
    market_analysis = create_market_analysis()
    analyzer = StatisticalMarketComparisonAnalyzer()

    first_report = analyzer.analyze(
        prediction,
        market_analysis,
    )
    second_report = analyzer.analyze(
        prediction,
        market_analysis,
    )

    assert first_report == second_report