"""Shared deterministic fixtures for final reduction-report tests."""

from datetime import datetime, timezone

from src.models.color_reduction_rule import (
    ColorReductionRule,
    ColoredOutcomeCell,
    ReductionColor,
)
from src.models.color_reduction_rule_set import (
    ColorReductionRuleSet,
)
from src.models.game_type import GameType
from src.models.odds_reduction_rule import (
    OddsReductionRule,
    OddsReductionSnapshot,
)
from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
    OutcomeCountCondition,
)
from src.models.outcome import Outcome
from src.models.payout_reduction_rule import (
    PayoutReductionRule,
    PayoutReductionSnapshot,
)
from src.models.point_reduction_rule import (
    PointAssignment,
    PointReductionRule,
)
from src.models.reduction_condition_set import (
    ReductionConditionSet,
)
from src.models.reduction_frame import ReductionFrame
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.final_reduction_report_engine import (
    FinalReductionReportEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
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
        coupon_id="Komplett reduceringsrapport",
    )


def create_base_system():
    """Generate the standard complete base system."""

    return ReductionRowGenerator().generate(
        create_frame()
    )


def create_color_rule_set() -> ColorReductionRuleSet:
    """Create the standard two-color rule set."""

    return ColorReductionRuleSet(
        rules=(
            ColorReductionRule(
                color=ReductionColor.RED,
                cells=(
                    ColoredOutcomeCell(1, Outcome.HOME),
                    ColoredOutcomeCell(2, Outcome.DRAW),
                    ColoredOutcomeCell(3, Outcome.AWAY),
                ),
                min_hits=1,
                max_hits=1,
            ),
            ColorReductionRule(
                color=ReductionColor.YELLOW,
                cells=(
                    ColoredOutcomeCell(1, Outcome.DRAW),
                    ColoredOutcomeCell(2, Outcome.HOME),
                    ColoredOutcomeCell(3, Outcome.DRAW),
                ),
                min_hits=1,
                max_hits=2,
            ),
        )
    )


def create_one_x_two_rule() -> OneXTwoReductionRule:
    """Create the standard total 1-X-2 conditions."""

    return OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                Outcome.HOME,
                5,
                6,
            ),
            OutcomeCountCondition(
                Outcome.DRAW,
                1,
                2,
            ),
            OutcomeCountCondition(
                Outcome.AWAY,
                0,
                1,
            ),
        )
    )


def create_point_rule() -> PointReductionRule:
    """Create the standard point condition."""

    return PointReductionRule(
        assignments=(
            PointAssignment(1, Outcome.HOME, 5),
            PointAssignment(1, Outcome.DRAW, 2),
            PointAssignment(2, Outcome.HOME, 4),
            PointAssignment(2, Outcome.DRAW, 3),
            PointAssignment(2, Outcome.AWAY, 1),
            PointAssignment(3, Outcome.HOME, 3),
            PointAssignment(3, Outcome.DRAW, 2),
            PointAssignment(3, Outcome.AWAY, 1),
            PointAssignment(4, Outcome.HOME, 2),
        ),
        min_points=10,
        max_points=12,
    )


def create_odds_rule() -> OddsReductionRule:
    """Create the standard frozen total-odds condition."""

    return OddsReductionRule(
        snapshot=OddsReductionSnapshot(
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
            source="Testmarknad",
        ),
        min_total_odds="700",
        max_total_odds="1600",
    )


def create_payout_rule(
    *,
    minimum: str = "400",
    maximum: str = "800",
) -> PayoutReductionRule:
    """Create the standard transparent payout condition."""

    return PayoutReductionRule(
        snapshot=PayoutReductionSnapshot(
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
            source="Testpool",
        ),
        min_estimated_payout=minimum,
        max_estimated_payout=maximum,
    )


def create_condition_set() -> ReductionConditionSet:
    """Create all five supported reduction groups together."""

    return ReductionConditionSet(
        color_rule_set=create_color_rule_set(),
        one_x_two_rule=create_one_x_two_rule(),
        point_rule=create_point_rule(),
        odds_rule=create_odds_rule(),
        payout_rule=create_payout_rule(),
    )


def create_report(
    *,
    row_price="1.00",
):
    """Build the standard final reduction report."""

    return FinalReductionReportEngine().analyze(
        create_base_system(),
        create_condition_set(),
        row_price=row_price,
    )