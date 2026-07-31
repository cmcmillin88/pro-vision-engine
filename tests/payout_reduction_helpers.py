"""Shared deterministic fixtures for payout-reduction tests."""

from datetime import datetime, timezone
from decimal import Decimal

from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.payout_reduction_rule import (
    PayoutReductionRule,
    PayoutReductionSnapshot,
)
from src.models.reduction_frame import ReductionFrame
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.payout_reduction_engine import (
    PayoutReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_snapshot() -> PayoutReductionSnapshot:
    """Create the standard frozen eight-match payout snapshot."""

    return PayoutReductionSnapshot(
        captured_at=datetime(
            2026,
            7,
            31,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        match_percentages=(
            ThreeWayPercentages("50", "30", "20"),
            ThreeWayPercentages("60", "25", "15"),
            ThreeWayPercentages("40", "35", "25"),
            ThreeWayPercentages("50", "30", "20"),
            ThreeWayPercentages("50", "30", "20"),
            ThreeWayPercentages("50", "30", "20"),
            ThreeWayPercentages("50", "30", "20"),
            ThreeWayPercentages("50", "30", "20"),
        ),
        turnover="1000000",
        top_prize_pool="400000",
        base_unit_stake="1",
        source="  Testpool  ",
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
        coupon_id="Utdelningsreducering",
    )


def create_base_system():
    """Generate the standard deterministic base system."""

    return ReductionRowGenerator().generate(
        create_frame()
    )


def create_rule(
    *,
    minimum: Decimal | str = "400",
    maximum: Decimal | str = "800",
) -> PayoutReductionRule:
    """Create the standard inclusive payout interval."""

    return PayoutReductionRule(
        snapshot=create_snapshot(),
        min_estimated_payout=minimum,
        max_estimated_payout=maximum,
    )


def create_result():
    """Apply the standard payout-reduction fixture."""

    return PayoutReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )