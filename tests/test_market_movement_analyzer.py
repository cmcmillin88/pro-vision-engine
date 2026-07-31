"""Tests for time-based market movement analysis."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.models.market_snapshot import MarketSnapshot
from src.models.movement_direction import (
    MovementDirection,
)
from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.market_movement_analyzer import (
    MarketMovementAnalyzer,
)


def create_earlier_snapshot(
    *,
    source_name: str = "combined-market",
) -> MarketSnapshot:
    """Create the earlier representative market snapshot."""

    return MarketSnapshot(
        captured_at=datetime(
            2026,
            8,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        odds=ThreeWayOdds(
            home=Decimal("2.00"),
            draw=Decimal("3.50"),
            away=Decimal("4.00"),
        ),
        public_percentages=ThreeWayPercentages(
            home=Decimal("55"),
            draw=Decimal("25"),
            away=Decimal("20"),
        ),
        source_name=source_name,
    )


def create_later_snapshot(
    *,
    captured_at: datetime | None = None,
    source_name: str = "combined-market",
) -> MarketSnapshot:
    """Create the later representative market snapshot."""

    return MarketSnapshot(
        captured_at=(
            captured_at
            or datetime(
                2026,
                8,
                1,
                14,
                0,
                tzinfo=timezone.utc,
            )
        ),
        odds=ThreeWayOdds(
            home=Decimal("1.80"),
            draw=Decimal("3.80"),
            away=Decimal("4.50"),
        ),
        public_percentages=ThreeWayPercentages(
            home=Decimal("60"),
            draw=Decimal("23"),
            away=Decimal("17"),
        ),
        source_name=source_name,
    )


def create_analysis():
    """Create one complete movement analysis."""

    return MarketMovementAnalyzer().analyze(
        create_earlier_snapshot(),
        create_later_snapshot(),
    )


def test_analysis_preserves_snapshots_and_duration() -> None:
    earlier_snapshot = create_earlier_snapshot()
    later_snapshot = create_later_snapshot()

    analysis = MarketMovementAnalyzer().analyze(
        earlier_snapshot,
        later_snapshot,
    )

    assert analysis.earlier_snapshot is earlier_snapshot
    assert analysis.later_snapshot is later_snapshot
    assert analysis.elapsed_time == timedelta(
        hours=2
    )


def test_analysis_preserves_official_outcome_order() -> None:
    analysis = create_analysis()

    assert tuple(
        movement.outcome
        for movement in analysis.outcome_movements
    ) == Outcome.ordered()


def test_analysis_calculates_odds_movements() -> None:
    analysis = create_analysis()

    assert (
        analysis.for_outcome(
            Outcome.HOME
        ).odds_change
        == Decimal("-0.20")
    )
    assert (
        analysis.for_outcome(
            Outcome.DRAW
        ).odds_change
        == Decimal("0.30")
    )
    assert (
        analysis.for_outcome(
            Outcome.AWAY
        ).odds_change
        == Decimal("0.50")
    )


def test_analysis_calculates_market_probability_movements() -> None:
    analysis = create_analysis()

    assert (
        analysis.for_outcome(
            Outcome.HOME
        ).market_probability_change
        == Decimal("5.09")
    )
    assert (
        analysis.for_outcome(
            Outcome.DRAW
        ).market_probability_change
        == Decimal("-2.31")
    )
    assert (
        analysis.for_outcome(
            Outcome.AWAY
        ).market_probability_change
        == Decimal("-2.79")
    )


def test_analysis_calculates_public_percentage_movements() -> None:
    analysis = create_analysis()

    assert (
        analysis.for_outcome(
            Outcome.HOME
        ).public_percentage_change
        == Decimal("5.00")
    )
    assert (
        analysis.for_outcome(
            Outcome.DRAW
        ).public_percentage_change
        == Decimal("-2.00")
    )
    assert (
        analysis.for_outcome(
            Outcome.AWAY
        ).public_percentage_change
        == Decimal("-3.00")
    )


def test_analysis_calculates_edge_movements() -> None:
    analysis = create_analysis()

    assert (
        analysis.for_outcome(
            Outcome.HOME
        ).edge_change
        == Decimal("0.09")
    )
    assert (
        analysis.for_outcome(
            Outcome.DRAW
        ).edge_change
        == Decimal("-0.31")
    )
    assert (
        analysis.for_outcome(
            Outcome.AWAY
        ).edge_change
        == Decimal("0.21")
    )


def test_analysis_exposes_movement_directions() -> None:
    analysis = create_analysis()
    home_movement = analysis.for_outcome(
        Outcome.HOME
    )

    assert (
        home_movement.odds_direction
        is MovementDirection.DECREASED
    )
    assert (
        home_movement.market_probability_direction
        is MovementDirection.INCREASED
    )
    assert (
        home_movement.public_percentage_direction
        is MovementDirection.INCREASED
    )
    assert home_movement.odds_shortened is True
    assert home_movement.odds_drifted is False


def test_analysis_identifies_strongest_market_move() -> None:
    analysis = create_analysis()

    assert (
        analysis.strongest_market_probability_move.outcome
        is Outcome.HOME
    )


def test_analysis_identifies_strongest_public_move() -> None:
    analysis = create_analysis()

    assert (
        analysis.strongest_public_percentage_move.outcome
        is Outcome.HOME
    )


def test_analyzer_rejects_invalid_earlier_snapshot() -> None:
    with pytest.raises(
        TypeError,
        match="Earlier snapshot",
    ):
        MarketMovementAnalyzer().analyze(
            object(),  # type: ignore[arg-type]
            create_later_snapshot(),
        )


def test_analyzer_rejects_invalid_later_snapshot() -> None:
    with pytest.raises(
        TypeError,
        match="Later snapshot",
    ):
        MarketMovementAnalyzer().analyze(
            create_earlier_snapshot(),
            object(),  # type: ignore[arg-type]
        )


def test_analyzer_rejects_non_chronological_snapshots() -> None:
    earlier_snapshot = create_earlier_snapshot()

    later_snapshot = create_later_snapshot(
        captured_at=(
            earlier_snapshot.captured_at
        )
    )

    with pytest.raises(
        ValueError,
        match="captured after",
    ):
        MarketMovementAnalyzer().analyze(
            earlier_snapshot,
            later_snapshot,
        )


def test_analyzer_rejects_different_sources() -> None:
    with pytest.raises(
        ValueError,
        match="same source name",
    ):
        MarketMovementAnalyzer().analyze(
            create_earlier_snapshot(
                source_name="source-a"
            ),
            create_later_snapshot(
                source_name="source-b"
            ),
        )