"""Integration tests for payout reduction in the common engine."""

from decimal import Decimal

import pytest

from src.models.point_reduction_rule import (
    PointAssignment,
    PointReductionRule,
)
from src.models.outcome import Outcome
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.services.reduction_condition_engine import (
    ReductionConditionEngine,
)
from tests.payout_reduction_helpers import (
    create_base_system,
    create_rule,
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


def test_common_engine_supports_payout_only() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        ReductionConditionSet(
            payout_rule=create_rule()
        ),
    )

    assert result.approved_count == 11
    assert result.condition_set.condition_types == (
        ReductionConditionType.PAYOUT,
    )


def test_common_engine_combines_points_and_payout() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        ReductionConditionSet(
            point_rule=create_point_rule(),
            payout_rule=create_rule(),
        ),
    )

    assert result.approved_count == 4
    assert tuple(
        row.symbols
        for row in result.approved_rows
    ) == (
        "1X211111",
        "12111111",
        "12X11111",
        "XX111111",
    )


def test_common_engine_preserves_independent_counts() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        ReductionConditionSet(
            point_rule=create_point_rule(),
            payout_rule=create_rule(),
        ),
    )

    assert result.approved_count_for_condition(
        ReductionConditionType.POINT
    ) == 8
    assert result.approved_count_for_condition(
        ReductionConditionType.PAYOUT
    ) == 11


def test_common_engine_exposes_payout_metric() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        ReductionConditionSet(
            payout_rule=create_rule()
        ),
    )

    evaluation = result.evaluations[0].evaluation_for(
        ReductionConditionType.PAYOUT
    )
    metric = evaluation.metrics[0]

    assert metric.label == "Utdelning"
    assert metric.observed_value == Decimal("106.67")
    assert metric.minimum_value == Decimal("400.00")
    assert metric.maximum_value == Decimal("800.00")
    assert metric.maximum_inclusive is True
    assert metric.is_approved is False


def test_common_engine_exposes_condition_pattern() -> None:
    condition_set = ReductionConditionSet(
        point_rule=create_point_rule(),
        payout_rule=create_rule(),
    )

    assert condition_set.condition_pattern == (
        "Poäng 10/12 | Utdelning "
        "400.00 <= utdelning <= 800.00"
    )


def test_common_engine_rejects_payout_match_count_mismatch() -> None:
    snapshot = create_rule().snapshot
    short_rule = type(create_rule())(
        snapshot=type(snapshot)(
            captured_at=snapshot.captured_at,
            match_percentages=(
                snapshot.match_percentages[:-1]
            ),
            turnover=snapshot.turnover,
            top_prize_pool=snapshot.top_prize_pool,
            base_unit_stake=snapshot.base_unit_stake,
            source=snapshot.source,
        ),
        min_estimated_payout="400",
        max_estimated_payout="800",
    )

    with pytest.raises(
        ValueError,
        match="payout snapshot.*exactly",
    ):
        ReductionConditionEngine().apply(
            create_base_system(),
            ReductionConditionSet(
                payout_rule=short_rule
            ),
        )