"""Tests for complete coupon-analysis input."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.coupon_analysis_input import (
    CouponAnalysisInput,
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


def create_performance(
    *,
    team_name: str,
    opponent_name: str,
    venue: MatchVenue,
) -> TeamMatchPerformance:
    """Create one compact team performance."""

    return TeamMatchPerformance(
        team_name=team_name,
        opponent_name=opponent_name,
        played_at=datetime(
            2026,
            11,
            1,
            15,
            0,
            tzinfo=timezone.utc,
        ),
        venue=venue,
        goals_for=1,
        goals_against=1,
        expected_goals_for=Decimal("1.20"),
        expected_goals_against=Decimal("1.00"),
        shots_for=10,
        shots_against=9,
        shots_on_target_for=4,
        shots_on_target_against=3,
    )


def create_snapshot(
    *,
    hour: int,
) -> MarketSnapshot:
    """Create one compact market snapshot."""

    return MarketSnapshot(
        captured_at=datetime(
            2026,
            11,
            1,
            hour,
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


def create_match_input(
    index: int,
) -> MatchAnalysisInput:
    """Create one valid coupon match input."""

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
            ),
        ),
        away_performances=(
            create_performance(
                team_name=away_team,
                opponent_name=f"Away opponent {index}",
                venue=MatchVenue.AWAY,
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


def create_input() -> CouponAnalysisInput:
    """Create one valid Topptipset input."""

    return CouponAnalysisInput(
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
        coupon_id="Topptipset 1",
    )


def test_input_exposes_expected_match_count() -> None:
    analysis_input = create_input()

    assert analysis_input.match_count == 8
    assert analysis_input.expected_match_count == 8
    assert (
        analysis_input.game_type
        is GameType.TOPPTIPSET
    )


def test_input_normalizes_coupon_id() -> None:
    analysis_input = CouponAnalysisInput(
        game_type=GameType.TOPPTIPSET,
        matches=create_input().matches,
        coupon_id="  Topptipset   vecka  1  ",
    )

    assert (
        analysis_input.coupon_id
        == "Topptipset vecka 1"
    )


def test_input_rejects_unknown_game_type() -> None:
    with pytest.raises(
        ValueError,
        match="supported game type",
    ):
        CouponAnalysisInput(
            game_type=GameType.UNKNOWN,
            matches=create_input().matches,
        )


def test_input_rejects_wrong_match_count() -> None:
    with pytest.raises(
        ValueError,
        match="exactly 8 matches",
    ):
        CouponAnalysisInput(
            game_type=GameType.TOPPTIPSET,
            matches=create_input().matches[:-1],
        )


def test_input_rejects_non_tuple_matches() -> None:
    with pytest.raises(
        TypeError,
        match="matches must be a tuple",
    ):
        CouponAnalysisInput(
            game_type=GameType.TOPPTIPSET,
            matches=list(  # type: ignore[arg-type]
                create_input().matches
            ),
        )


def test_input_rejects_invalid_match_item() -> None:
    matches = list(
        create_input().matches
    )
    matches[0] = object()  # type: ignore[assignment]

    with pytest.raises(
        TypeError,
        match="MatchAnalysisInput objects",
    ):
        CouponAnalysisInput(
            game_type=GameType.TOPPTIPSET,
            matches=tuple(matches),
        )


def test_input_rejects_duplicate_match_references() -> None:
    analysis_input = create_input()
    matches = list(
        analysis_input.matches
    )
    matches[1] = replace(
        matches[1],
        match_reference="match 1",
    )

    with pytest.raises(
        ValueError,
        match="must be unique",
    ):
        CouponAnalysisInput(
            game_type=GameType.TOPPTIPSET,
            matches=tuple(matches),
        )


def test_input_is_immutable() -> None:
    analysis_input = create_input()

    with pytest.raises(
        FrozenInstanceError
    ):
        analysis_input.coupon_id = "Changed"  # type: ignore[misc]