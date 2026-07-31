"""Tests for time-stamped market snapshots."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_snapshot import MarketSnapshot
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)


def create_odds() -> ThreeWayOdds:
    """Create valid test odds."""

    return ThreeWayOdds(
        home=Decimal("2.00"),
        draw=Decimal("3.50"),
        away=Decimal("4.00"),
    )


def create_percentages() -> ThreeWayPercentages:
    """Create valid test percentages."""

    return ThreeWayPercentages(
        home=Decimal("55"),
        draw=Decimal("25"),
        away=Decimal("20"),
    )


def test_snapshot_normalizes_source_name() -> None:
    snapshot = MarketSnapshot(
        captured_at=datetime(
            2026,
            8,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        odds=create_odds(),
        public_percentages=create_percentages(),
        source_name="  combined-market  ",
    )

    assert snapshot.source_name == "combined-market"


def test_snapshot_rejects_naive_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="timezone information",
    ):
        MarketSnapshot(
            captured_at=datetime(
                2026,
                8,
                1,
                12,
                0,
            ),
            odds=create_odds(),
            public_percentages=create_percentages(),
        )


def test_snapshot_rejects_invalid_odds_type() -> None:
    with pytest.raises(
        TypeError,
        match="must be ThreeWayOdds",
    ):
        MarketSnapshot(
            captured_at=datetime(
                2026,
                8,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            odds=object(),  # type: ignore[arg-type]
            public_percentages=create_percentages(),
        )


def test_snapshot_rejects_invalid_percentage_type() -> None:
    with pytest.raises(
        TypeError,
        match="must be ThreeWayPercentages",
    ):
        MarketSnapshot(
            captured_at=datetime(
                2026,
                8,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            odds=create_odds(),
            public_percentages=object(),  # type: ignore[arg-type]
        )


def test_snapshot_rejects_empty_source_name() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        MarketSnapshot(
            captured_at=datetime(
                2026,
                8,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            odds=create_odds(),
            public_percentages=create_percentages(),
            source_name="   ",
        )


def test_snapshot_is_immutable() -> None:
    snapshot = MarketSnapshot(
        captured_at=datetime(
            2026,
            8,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        odds=create_odds(),
        public_percentages=create_percentages(),
    )

    with pytest.raises(FrozenInstanceError):
        snapshot.source_name = "changed"  # type: ignore[misc]