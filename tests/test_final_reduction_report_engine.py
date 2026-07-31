"""Tests for the complete final reduction-report engine."""

from decimal import Decimal

import pytest

from src.models.payout_reduction_rule import (
    PayoutReductionRule,
)
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.services.final_reduction_report_engine import (
    FinalReductionReportEngine,
)
from src.services.reduction_condition_engine import (
    ReductionConditionEngine,
)
from tests.reduction_report_helpers import (
    create_base_system,
    create_condition_set,
    create_payout_rule,
    create_point_rule,
)


def test_engine_builds_complete_five_condition_report() -> None:
    report = FinalReductionReportEngine().analyze(
        create_base_system(),
        create_condition_set(),
        row_price="1.00",
    )

    assert report.condition_count == 5
    assert report.approved_symbols == (
        "12X11111",
    )


def test_engine_preserves_base_system_and_condition_set() -> None:
    base_system = create_base_system()
    condition_set = create_condition_set()

    report = FinalReductionReportEngine().analyze(
        base_system,
        condition_set,
    )

    assert report.base_system is base_system
    assert report.condition_set is condition_set


def test_engine_builds_independent_condition_impacts() -> None:
    report = FinalReductionReportEngine().analyze(
        create_base_system(),
        create_condition_set(),
    )

    assert report.condition_impact_for(
        ReductionConditionType.COLOR
    ).independently_rejected_count == 18

    assert report.condition_impact_for(
        ReductionConditionType.PAYOUT
    ).independently_rejected_count == 16


def test_engine_builds_exact_rejection_signatures() -> None:
    report = FinalReductionReportEngine().analyze(
        create_base_system(),
        create_condition_set(),
    )

    pattern_counts = {
        tuple(
            condition_type.value
            for condition_type in pattern.condition_types
        ): pattern.row_count
        for pattern in report.rejection_patterns
    }

    assert pattern_counts[
        (
            "color",
            "one_x_two",
            "point",
            "odds",
            "payout",
        )
    ] == 5
    assert pattern_counts[("color",)] == 1
    assert pattern_counts[("odds",)] == 1
    assert pattern_counts[("point",)] == 1


def test_engine_orders_patterns_by_count_then_official_order() -> None:
    report = FinalReductionReportEngine().analyze(
        create_base_system(),
        create_condition_set(),
    )

    assert tuple(
        pattern.row_count
        for pattern in report.rejection_patterns[:5]
    ) == (
        5,
        3,
        3,
        2,
        2,
    )

    assert report.rejection_patterns[1].condition_types == (
        ReductionConditionType.COLOR,
        ReductionConditionType.POINT,
    )


def test_engine_is_deterministic() -> None:
    engine = FinalReductionReportEngine()
    base_system = create_base_system()
    condition_set = create_condition_set()

    first = engine.analyze(
        base_system,
        condition_set,
        row_price="1.00",
    )
    second = engine.analyze(
        base_system,
        condition_set,
        row_price="1.00",
    )

    assert first == second


def test_engine_supports_one_condition_group() -> None:
    report = FinalReductionReportEngine().analyze(
        create_base_system(),
        ReductionConditionSet(
            point_rule=create_point_rule()
        ),
    )

    assert report.condition_count == 1
    assert report.approved_count == 8
    assert report.strictest_condition.condition_type is (
        ReductionConditionType.POINT
    )
    assert report.combination_removed_count == 0


def test_engine_supports_empty_final_system() -> None:
    payout_rule = create_payout_rule(
        minimum="1800",
        maximum="2000",
    )

    report = FinalReductionReportEngine().analyze(
        create_base_system(),
        ReductionConditionSet(
            payout_rule=payout_rule
        ),
        row_price="1.00",
    )

    assert report.is_empty is True
    assert report.approved_count == 0
    assert report.final_cost == Decimal("0.00")
    assert report.rejected_count == 27


def test_engine_accepts_numeric_row_price() -> None:
    report = FinalReductionReportEngine().analyze(
        create_base_system(),
        create_condition_set(),
        row_price=1,
    )

    assert report.row_price == Decimal("1.00")


def test_engine_rejects_invalid_base_system() -> None:
    with pytest.raises(
        TypeError,
        match="BaseReductionSystem",
    ):
        FinalReductionReportEngine().analyze(
            object(),  # type: ignore[arg-type]
            create_condition_set(),
        )


def test_engine_rejects_invalid_condition_set() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionConditionSet",
    ):
        FinalReductionReportEngine().analyze(
            create_base_system(),
            object(),  # type: ignore[arg-type]
        )


def test_engine_rejects_invalid_injected_engine() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionConditionEngine",
    ):
        FinalReductionReportEngine(
            object()  # type: ignore[arg-type]
        )


def test_engine_accepts_injected_condition_engine() -> None:
    condition_engine = ReductionConditionEngine()
    engine = FinalReductionReportEngine(
        condition_engine
    )

    report = engine.analyze(
        create_base_system(),
        create_condition_set(),
    )

    assert report.approved_count == 1


def test_engine_propagates_frame_validation() -> None:
    payout_rule: PayoutReductionRule = create_payout_rule()
    shorter_percentages = (
        payout_rule.snapshot.match_percentages[:-1]
    )

    broken_snapshot = type(
        payout_rule.snapshot
    )(
        captured_at=payout_rule.snapshot.captured_at,
        match_percentages=shorter_percentages,
        turnover=payout_rule.snapshot.turnover,
        top_prize_pool=payout_rule.snapshot.top_prize_pool,
        base_unit_stake=payout_rule.snapshot.base_unit_stake,
        source=payout_rule.snapshot.source,
    )
    broken_rule = PayoutReductionRule(
        snapshot=broken_snapshot,
        min_estimated_payout=(
            payout_rule.min_estimated_payout
        ),
        max_estimated_payout=(
            payout_rule.max_estimated_payout
        ),
    )

    with pytest.raises(
        ValueError,
        match="snapshot",
    ):
        FinalReductionReportEngine().analyze(
            create_base_system(),
            ReductionConditionSet(
                payout_rule=broken_rule
            ),
        )