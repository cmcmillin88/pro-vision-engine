"""Shared deterministic fixtures for odds-reduction tests."""

from datetime import datetime, timezone
from decimal import Decimal

from src.models.game_type import GameType
from src.models.odds_reduction_rule import (
    OddsReductionRule,
    OddsReductionSnapshot,
)
from src.models.outcome import Outcome
from src.models.reduction_frame import ReductionFrame
from src.models.three_way_odds import ThreeWayOdds
from src.services.odds_reduction_engine import (
    OddsReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_snapshot() -> OddsReductionSnapshot:
    """Create the standard frozen eight-match odds snapshot."""

    return OddsReductionSnapshot(
        captured_at=datetime(
            2026,
            7,
            31,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        match_odds=(
            ThreeWayOdds("2.00", "3.00", "4.00"),
            ThreeWayOdds("1.50", "3.00", "6.00"),
            ThreeWayOdds("2.00", "4.00", "5.00"),
            ThreeWayOdds("2.00", "2.00", "2.00"),
            ThreeWayOdds("2.00", "2.00", "2.00"),
            ThreeWayOdds("2.00", "2.00", "2.00"),
            ThreeWayOdds("2.00", "2.00", "2.00"),
            ThreeWayOdds("2.00", "2.00", "2.00"),
        ),
        source="  Testmarknad  ",
    )


def create_frame() -> ReductionFrame:
    """Create the standard 27-row Topptipset frame."""

    return ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            Outcome.ordered(),
            Outcome.ordered(),
            Outcome.ordered(),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
        ),
        coupon_id="Oddsreducering",
    )


def create_base_system():
    """Generate the standard deterministic base system."""

    return ReductionRowGenerator().generate(
        create_frame()
    )


def create_rule(
    *,
    minimum: Decimal | str = "700",
    maximum: Decimal | str = "1600",
) -> OddsReductionRule:
    """Create the standard half-open odds interval."""

    return OddsReductionRule(
        snapshot=create_snapshot(),
        min_total_odds=minimum,
        max_total_odds=maximum,
    )


def create_result():
    """Apply the standard odds-reduction fixture."""

    return OddsReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )