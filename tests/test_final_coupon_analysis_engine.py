"""Tests for the final Project 13 coupon-analysis engine."""

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
    FinalDecisionType,
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
    """Create one configurable performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=datetime(
            2026,
            11,
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


def create_snapshot(
    *,
    hour: int,
    strong: bool,
) -> MarketSnapshot:
    """Create one standard or strong-favorite snapshot."""

    if strong:
        odds = (
            ("1.40", "5.20", "9.00")
            if hour == 12
            else ("1.35", "5.50", "10.00")
        )
        percentages = (
            ("67", "19", "14")
            if hour == 12
            else ("68", "18", "14")
        )
    else:
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
            20,
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
    *,
    strong: bool = False,
) -> MatchAnalysisInput:
    """Create one standard or strong match input."""

    home_team = f"Home {index}"
    away_team = f"Away {index}"

    home_xg_for = (
        "2.10"
        if strong
        else "1.80"
    )
    home_xg_against = (
        "0.60"
        if strong
        else "0.80"
    )
    away_xg_for = (
        "0.60"
        if strong
        else "1.20"
    )
    away_xg_against = (
        "2.10"
        if strong
        else "1.50"
    )

    return MatchAnalysisInput(
        home_team_name=home_team,
        away_team_name=away_team,
        home_performances=(
            create_performance(
                team_name=home_team,
                opponent_name=f"Home opponent {index}",
                venue=MatchVenue.HOME,
                xg_for=home_xg_for,
                xg_against=home_xg_against,
            ),
        ),
        away_performances=(
            create_performance(
                team_name=away_team,
                opponent_name=f"Away opponent {index}",
                venue=MatchVenue.AWAY,
                xg_for=away_xg_for,
                xg_against=away_xg_against,
            ),
        ),
        earlier_market_snapshot=create_snapshot(
            hour=12,
            strong=strong,
        ),
        later_market_snapshot=create_snapshot(
            hour=14,
            strong=strong,
        ),
        match_reference=f"Match {index}",
    )


def create_coupon_input(
    game_type: GameType = GameType.TOPPTIPSET,
    *,
    strong_indexes: tuple[int, ...] = (),
) -> CouponAnalysisInput:
    """Create one configurable coupon input."""

    expected_count = game_type.expected_match_count

    if expected_count is None:
        raise ValueError(
            "Test helper requires a supported game type."
        )

    return CouponAnalysisInput(
        game_type=game_type,
        matches=tuple(
            create_match_input(
                index,
                strong=(
                    index in strong_indexes
                ),
            )
            for index in range(
                1,
                expected_count + 1,
            )
        ),
        coupon_id=f"{game_type.display_name} test",
    )


def test_engine_builds_complete_coupon_report() -> None:
    report = FinalCouponAnalysisEngine().analyze(
        create_coupon_input()
    )

    assert isinstance(
        report,
        FinalCouponAnalysisReport,
    )
    assert report.match_count == 8


def test_engine_analyzes_every_topptipset_match() -> None:
    report = FinalCouponAnalysisEngine().analyze(
        create_coupon_input()
    )

    assert len(
        report.match_reports
    ) == 8
    assert all(
        match_report.recommendation_symbols == "12"
        for match_report in report.match_reports
    )


def test_engine_supports_mixed_spike_and_double_coupon() -> None:
    report = FinalCouponAnalysisEngine().analyze(
        create_coupon_input(
            strong_indexes=(1,),
        )
    )

    assert report.spike_count == 1
    assert report.double_count == 7
    assert report.triple_count == 0
    assert report.base_row_count == 128
    assert report.review_count == 7
    assert (
        report.average_risk_score
        == Decimal("5.25")
    )
    assert (
        report.match_reports[0]
        .final_decision_type
        is FinalDecisionType.SPIKE
    )


def test_engine_supports_thirteen_match_coupon() -> None:
    report = FinalCouponAnalysisEngine().analyze(
        create_coupon_input(
            GameType.STRYKTIPSET
        )
    )

    assert report.match_count == 13
    assert report.double_count == 13
    assert report.base_row_count == 8192


def test_engine_rejects_invalid_input() -> None:
    with pytest.raises(
        TypeError,
        match="requires a CouponAnalysisInput",
    ):
        FinalCouponAnalysisEngine().analyze(
            object()  # type: ignore[arg-type]
        )


def test_engine_rejects_invalid_dependency() -> None:
    with pytest.raises(
        TypeError,
        match="FinalMatchAnalysisEngine",
    ):
        FinalCouponAnalysisEngine(
            match_analysis_engine=object(),  # type: ignore[arg-type]
        )


def test_engine_is_deterministic() -> None:
    analysis_input = create_coupon_input()
    engine = FinalCouponAnalysisEngine()

    first_report = engine.analyze(
        analysis_input
    )
    second_report = engine.analyze(
        analysis_input
    )

    assert first_report == second_report