"""Tests for the complete match-analysis report."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_recommendation import (
    RecommendationRiskLevel,
)
from src.models.market_snapshot import MarketSnapshot
from src.models.match_analysis import (
    MatchAnalysisReport,
)
from src.models.match_analysis_input import (
    MatchAnalysisInput,
)
from src.models.outcome import Outcome
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
)
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.match_analysis_engine import (
    MatchAnalysisEngine,
)


def create_performance(
    *,
    team_name: str,
    opponent_name: str,
    venue: MatchVenue,
    xg_for: str,
    xg_against: str,
) -> TeamMatchPerformance:
    """Create one compact team performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=datetime(
            2026,
            9,
            1,
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


def create_snapshot(
    *,
    hour: int,
    odds: tuple[str, str, str],
    percentages: tuple[str, str, str],
    source_name: str = "combined-market",
) -> MarketSnapshot:
    """Create one configurable market snapshot."""

    return MarketSnapshot(
        captured_at=datetime(
            2026,
            9,
            1,
            hour,
            0,
            tzinfo=timezone.utc,
        ),
        odds=ThreeWayOdds(
            Decimal(odds[0]),
            Decimal(odds[1]),
            Decimal(odds[2]),
        ),
        public_percentages=ThreeWayPercentages(
            Decimal(percentages[0]),
            Decimal(percentages[1]),
            Decimal(percentages[2]),
        ),
        source_name=source_name,
    )


def create_input(
    *,
    home_team_name: str = "Arsenal",
    home_xg_for: str = "1.80",
    home_xg_against: str = "0.80",
    earlier_snapshot: MarketSnapshot | None = None,
    later_snapshot: MarketSnapshot | None = None,
) -> MatchAnalysisInput:
    """Create one valid complete match input."""

    return MatchAnalysisInput(
        home_team_name=home_team_name,
        away_team_name="Chelsea",
        home_performances=(
            create_performance(
                team_name=home_team_name,
                opponent_name="Tottenham",
                venue=MatchVenue.HOME,
                xg_for=home_xg_for,
                xg_against=home_xg_against,
            ),
        ),
        away_performances=(
            create_performance(
                team_name="Chelsea",
                opponent_name="Liverpool",
                venue=MatchVenue.AWAY,
                xg_for="1.20",
                xg_against="1.50",
            ),
        ),
        earlier_market_snapshot=(
            earlier_snapshot
            or create_snapshot(
                hour=12,
                odds=(
                    "2.00",
                    "3.50",
                    "4.00",
                ),
                percentages=(
                    "55",
                    "25",
                    "20",
                ),
            )
        ),
        later_market_snapshot=(
            later_snapshot
            or create_snapshot(
                hour=14,
                odds=(
                    "1.80",
                    "3.80",
                    "4.50",
                ),
                percentages=(
                    "60",
                    "23",
                    "17",
                ),
            )
        ),
        match_reference="Match 1",
    )


def create_report() -> MatchAnalysisReport:
    """Create the standard complete match report."""

    return MatchAnalysisEngine().analyze(
        create_input()
    )


def test_report_exposes_complete_component_chain() -> None:
    report = create_report()

    assert (
        report.evidence_comparison
        .statistical_prediction
        == report.statistical_analysis.prediction
    )
    assert (
        report.evidence_comparison.market_analysis
        == report.market_analysis
    )


def test_report_exposes_match_and_prediction_summary() -> None:
    report = create_report()

    assert report.match_reference == "Match 1"
    assert report.home_team_name == "Arsenal"
    assert report.away_team_name == "Chelsea"
    assert report.projected_scoreline == "1.65-1.00"
    assert (
        report.most_likely_scoreline.scoreline
        == "1-0"
    )


def test_report_exposes_evidence_summary() -> None:
    report = create_report()

    assert report.statistical_favorite is Outcome.HOME
    assert report.market_favorite is Outcome.HOME
    assert report.public_favorite is Outcome.HOME
    assert report.full_consensus is True
    assert report.statistical_market_agree is True
    assert (
        report.conflict_level
        is ModelMarketConflictLevel.LOW
    )


def test_report_exposes_model_value_summary() -> None:
    report = create_report()

    assert report.has_model_value is True
    assert report.has_strong_model_value is False
    assert (
        report.strongest_model_value.outcome
        is Outcome.AWAY
    )
    assert (
        report.strongest_model_value
        .statistical_public_edge
        == Decimal("5.91")
    )


def test_report_exposes_market_recommendation() -> None:
    report = create_report()

    assert report.primary_outcome is Outcome.HOME
    assert report.recommended_outcomes == (
        Outcome.HOME,
        Outcome.AWAY,
    )
    assert report.recommendation_symbols == "12"
    assert (
        report.risk_level
        is RecommendationRiskLevel.HIGH
    )
    assert report.risk_score == 8
    assert report.market_spike_candidate is False
    assert report.is_joint_spike_candidate is False
    assert report.requires_extended_review is False


def test_report_rejects_invalid_analysis_input() -> None:
    report = create_report()

    with pytest.raises(
        TypeError,
        match="MatchAnalysisInput",
    ):
        MatchAnalysisReport(
            analysis_input=object(),  # type: ignore[arg-type]
            statistical_analysis=report.statistical_analysis,
            market_analysis=report.market_analysis,
            evidence_comparison=report.evidence_comparison,
        )


def test_report_rejects_mismatched_statistical_analysis() -> None:
    report = create_report()
    other_report = MatchAnalysisEngine().analyze(
        create_input(
            home_team_name="Liverpool",
            home_xg_for="2.00",
            home_xg_against="0.60",
        )
    )

    with pytest.raises(
        ValueError,
        match="team names",
    ):
        replace(
            report,
            statistical_analysis=(
                other_report.statistical_analysis
            ),
        )


def test_report_rejects_mismatched_market_analysis() -> None:
    report = create_report()
    other_earlier = create_snapshot(
        hour=12,
        odds=(
            "2.20",
            "3.40",
            "3.60",
        ),
        percentages=(
            "48",
            "27",
            "25",
        ),
        source_name="other-market",
    )
    other_later = create_snapshot(
        hour=14,
        odds=(
            "2.10",
            "3.50",
            "3.80",
        ),
        percentages=(
            "50",
            "26",
            "24",
        ),
        source_name="other-market",
    )
    other_report = MatchAnalysisEngine().analyze(
        create_input(
            earlier_snapshot=other_earlier,
            later_snapshot=other_later,
        )
    )

    with pytest.raises(
        ValueError,
        match="snapshots must match",
    ):
        replace(
            report,
            market_analysis=other_report.market_analysis,
        )