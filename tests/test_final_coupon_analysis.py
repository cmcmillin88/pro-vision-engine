"""Tests for complete final coupon-analysis reports."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.coupon_analysis_input import (
    CouponAnalysisInput,
)
from src.models.final_coupon_analysis import (
    FinalCouponAnalysisReport,
)
from src.models.final_match_summary import (
    FinalMatchSummary,
)
from src.models.game_type import GameType
from src.models.market_snapshot import MarketSnapshot
from src.models.match_analysis_input import MatchAnalysisInput
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.final_coupon_analysis_engine import (
    FinalCouponAnalysisEngine,
)


def create_performance(
    *,
    team_name: str,
    opponent_name: str,
    venue: MatchVenue,
    xg_for: str,
    xg_against: str,
) -> TeamMatchPerformance:
    """Create one compact performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=datetime(
            2026,
            11,
            10,
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
) -> MarketSnapshot:
    """Create the standard market snapshot."""

    odds = (
        ("2.00", "3.50", "4.00")
        if hour == 12
        else ("1.80", "3.80", "4.50")
    )
    percentages = (
        ("55", "25", "20")
        if hour == 12
        else ("60", "23", "17")
    )

    return MarketSnapshot(
        captured_at=datetime(
            2026,
            11,
            10,
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
        source_name="combined-market",
    )


def create_match_input(
    index: int,
) -> MatchAnalysisInput:
    """Create one standard analyzed-match input."""

    home_team = f"Home {index}"
    away_team = f"Away {index}"

    return MatchAnalysisInput(
        home_team_name=home_team,
        away_team_name=away_team,
        home_performances=(
            create_performance(
                team_name=home_team,
                opponent_name=f"Home opponent {index}",
                venue=MatchVenue.HOME,
                xg_for="1.80",
                xg_against="0.80",
            ),
        ),
        away_performances=(
            create_performance(
                team_name=away_team,
                opponent_name=f"Away opponent {index}",
                venue=MatchVenue.AWAY,
                xg_for="1.20",
                xg_against="1.50",
            ),
        ),
        earlier_market_snapshot=create_snapshot(
            hour=12
        ),
        later_market_snapshot=create_snapshot(
            hour=14
        ),
        match_reference=f"Match {index}",
    )


def create_report() -> FinalCouponAnalysisReport:
    """Create one standard Topptipset report."""

    analysis_input = CouponAnalysisInput(
        game_type=GameType.TOPPTIPSET,
        matches=tuple(
            create_match_input(
                index
            )
            for index in range(
                1,
                9,
            )
        ),
        coupon_id="Topptipset test",
    )

    return FinalCouponAnalysisEngine().analyze(
        analysis_input
    )


def test_report_exposes_complete_component_chain() -> None:
    report = create_report()

    assert all(
        match_report.analysis_input
        == report.analysis_input.matches[index]
        for index, match_report in enumerate(
            report.match_reports
        )
    )


def test_report_exposes_coupon_metadata() -> None:
    report = create_report()

    assert report.game_type is GameType.TOPPTIPSET
    assert report.coupon_id == "Topptipset test"
    assert report.match_count == 8


def test_report_classifies_all_standard_matches() -> None:
    report = create_report()

    assert report.spike_count == 0
    assert report.single_count == 0
    assert report.double_count == 8
    assert report.triple_count == 0
    assert report.review_count == 8


def test_report_calculates_base_row_count() -> None:
    report = create_report()

    assert report.base_row_count == 256
    assert (
        report.recommendation_pattern
        == "12|12|12|12|12|12|12|12"
    )
    assert report.has_full_cover is False


def test_report_calculates_coupon_risk() -> None:
    report = create_report()

    assert report.total_risk_score == 48
    assert (
        report.average_risk_score
        == Decimal("6.00")
    )


def test_report_creates_flat_match_summaries() -> None:
    report = create_report()

    assert len(
        report.match_summaries
    ) == 8
    assert all(
        isinstance(
            summary,
            FinalMatchSummary,
        )
        for summary in report.match_summaries
    )


def test_report_exposes_expected_summary_line() -> None:
    report = create_report()

    assert report.summary_line == (
        "Topptipset | Matcher 8 | "
        "Spikar 0 | Singlar 0 | "
        "Halvgarderingar 8 | "
        "Helgarderingar 0 | "
        "Rader 256 | Granskning 8 | "
        "Snittrisk 6.00"
    )


def test_report_rejects_reversed_match_order() -> None:
    report = create_report()

    with pytest.raises(
        ValueError,
        match="coupon order",
    ):
        replace(
            report,
            match_reports=tuple(
                reversed(
                    report.match_reports
                )
            ),
        )


def test_report_rejects_invalid_match_report_item() -> None:
    report = create_report()
    reports = list(
        report.match_reports
    )
    reports[0] = object()  # type: ignore[assignment]

    with pytest.raises(
        TypeError,
        match="FinalMatchAnalysisReport objects",
    ):
        FinalCouponAnalysisReport(
            analysis_input=report.analysis_input,
            match_reports=tuple(reports),
        )