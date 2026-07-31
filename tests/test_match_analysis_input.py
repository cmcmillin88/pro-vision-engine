"""Tests for complete match-analysis input data."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_snapshot import MarketSnapshot
from src.models.match_analysis_input import (
    MatchAnalysisInput,
)
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
) -> TeamMatchPerformance:
    """Create one valid performance."""

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
        venue=MatchVenue.HOME,
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
    """Create one valid market snapshot."""

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
            Decimal("2.00"),
            Decimal("3.50"),
            Decimal("4.00"),
        ),
        public_percentages=ThreeWayPercentages(
            Decimal("55"),
            Decimal("25"),
            Decimal("20"),
        ),
        source_name="test-market",
    )


def create_input(
    **overrides: object,
) -> MatchAnalysisInput:
    """Create one valid complete analysis input."""

    values: dict[str, object] = {
        "home_team_name": "Arsenal",
        "away_team_name": "Chelsea",
        "home_performances": (
            create_performance(
                team_name="Arsenal",
                opponent_name="Tottenham",
            ),
        ),
        "away_performances": (
            create_performance(
                team_name="Chelsea",
                opponent_name="Liverpool",
            ),
        ),
        "earlier_market_snapshot": create_snapshot(
            hour=12
        ),
        "later_market_snapshot": create_snapshot(
            hour=14
        ),
        "match_reference": "Match 1",
    }
    values.update(
        overrides
    )

    return MatchAnalysisInput(
        **values  # type: ignore[arg-type]
    )


def test_input_normalizes_names_and_reference() -> None:
    analysis_input = create_input(
        home_team_name="  Arsenal  ",
        away_team_name="  Chelsea  ",
        match_reference="  Match   1  ",
    )

    assert analysis_input.home_team_name == "Arsenal"
    assert analysis_input.away_team_name == "Chelsea"
    assert analysis_input.match_reference == "Match 1"
    assert analysis_input.home_performance_count == 1
    assert analysis_input.away_performance_count == 1


def test_input_rejects_same_home_and_away_team() -> None:
    with pytest.raises(
        ValueError,
        match="must be different",
    ):
        create_input(
            away_team_name="arsenal",
            away_performances=(
                create_performance(
                    team_name="Arsenal",
                    opponent_name="Liverpool",
                ),
            ),
        )


def test_input_rejects_non_tuple_performances() -> None:
    with pytest.raises(
        TypeError,
        match="home_performances must be a tuple",
    ):
        create_input(
            home_performances=[
                create_performance(
                    team_name="Arsenal",
                    opponent_name="Tottenham",
                )
            ]
        )


def test_input_rejects_empty_performances() -> None:
    with pytest.raises(
        ValueError,
        match="away_performances must not be empty",
    ):
        create_input(
            away_performances=()
        )


def test_input_rejects_invalid_performance_item() -> None:
    with pytest.raises(
        TypeError,
        match="TeamMatchPerformance objects",
    ):
        create_input(
            home_performances=(
                object(),
            )
        )


def test_input_rejects_performance_for_wrong_team() -> None:
    with pytest.raises(
        ValueError,
        match="must belong to Arsenal",
    ):
        create_input(
            home_performances=(
                create_performance(
                    team_name="Liverpool",
                    opponent_name="Tottenham",
                ),
            )
        )


def test_input_rejects_invalid_market_snapshot() -> None:
    with pytest.raises(
        TypeError,
        match="earlier_market_snapshot",
    ):
        create_input(
            earlier_market_snapshot=object()
        )


def test_input_is_immutable() -> None:
    analysis_input = create_input()

    with pytest.raises(
        FrozenInstanceError
    ):
        analysis_input.home_team_name = "Liverpool"  # type: ignore[misc]