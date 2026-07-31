"""Tests for odds integration in the common condition engine."""

from decimal import Decimal

import pytest

from src.models.odds_reduction_rule import (
    OddsReductionRule,
)
from src.models.point_reduction_rule import (
    PointAssignment,
    PointReductionRule,
)
from src.models.outcome import Outcome
from src.models.reduction_condition_result import (
    ReductionMetricEvaluation,
)
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.services.reduction_condition_engine import (
    ReductionConditionEngine,
)
from tests.odds_reduction_helpers import (
    create_base_system,
    create_rule,
    create_snapshot,
)


def create_point_rule() -> PointReductionRule:
    """Create the Sprint 7.4 standard point rule."""

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


def test_condition_type_order_keeps_odds_before_payout() -> None:
    assert ReductionConditionType.ordered() == (
        ReductionConditionType.COLOR,
        ReductionConditionType.ONE_X_TWO,
        ReductionConditionType.POINT,
        ReductionConditionType.ODDS,
        ReductionConditionType.PAYOUT,
    )


def test_condition_set_supports_odds_only() -> None:
    condition_set = ReductionConditionSet(
        odds_rule=create_rule()
    )

    assert condition_set.condition_types == (
        ReductionConditionType.ODDS,
    )
    assert condition_set.atomic_condition_count == 1


def test_condition_set_combines_point_and_odds() -> None:
    condition_set = ReductionConditionSet(
        point_rule=create_point_rule(),
        odds_rule=create_rule(),
    )

    result = ReductionConditionEngine().apply(
        create_base_system(),
        condition_set,
    )

    assert result.approved_count == 4
    assert condition_set.condition_count == 2


def test_common_metric_supports_exclusive_decimal_maximum() -> None:
    metric = ReductionMetricEvaluation(
        label="Totalodds",
        observed_value=Decimal("1600"),
        minimum_value=Decimal("700"),
        maximum_value=Decimal("1600"),
        maximum_inclusive=False,
    )

    assert metric.is_approved is False
    assert metric.summary_text == (
        "Totalodds 1600.00 [700.00/1600.00)"
    )


def test_common_result_counts_odds_approvals() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        ReductionConditionSet(
            odds_rule=create_rule()
        ),
    )

    assert result.approved_count_for_condition(
        ReductionConditionType.ODDS
    ) == 13


def test_common_engine_exposes_exact_odds_metric() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        ReductionConditionSet(
            odds_rule=create_rule()
        ),
    )

    evaluation = result.evaluations[0].evaluation_for(
        ReductionConditionType.ODDS
    )

    assert evaluation.metrics[0].observed_value == Decimal(
        "192.0000000"
    )
    assert evaluation.metrics[0].maximum_inclusive is False


def test_common_engine_rejects_odds_snapshot_count_mismatch() -> None:
    short_snapshot = create_snapshot()
    short_snapshot = type(short_snapshot)(
        captured_at=short_snapshot.captured_at,
        match_odds=short_snapshot.match_odds[:-1],
        source=short_snapshot.source,
    )
    rule = OddsReductionRule(
        snapshot=short_snapshot,
        min_total_odds="1",
        max_total_odds="10000",
    )

    with pytest.raises(
        ValueError,
        match="exactly one complete",
    ):
        ReductionConditionEngine().apply(
            create_base_system(),
            ReductionConditionSet(
                odds_rule=rule
            ),
        )


def test_condition_pattern_includes_frozen_odds_interval() -> None:
    condition_set = ReductionConditionSet(
        point_rule=create_point_rule(),
        odds_rule=create_rule(),
    )

    assert condition_set.condition_pattern == (
        "Poäng 10/12 | "
        "Odds 700.00 <= odds < 1600.00"
    )