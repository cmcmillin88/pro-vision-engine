"""Tests for common reduction-condition results."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.models.color_reduction_rule import (
    ColorReductionRule,
    ColoredOutcomeCell,
    ReductionColor,
)
from src.models.color_reduction_rule_set import (
    ColorReductionRuleSet,
)
from src.models.game_type import GameType
from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
    OutcomeCountCondition,
)
from src.models.outcome import Outcome
from src.models.point_reduction_rule import (
    PointAssignment,
    PointReductionRule,
)
from src.models.reduction_condition_result import (
    ReductionConditionEvaluation,
    ReductionConditionRowEvaluation,
    ReductionMetricEvaluation,
)
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.models.reduction_frame import ReductionFrame
from src.models.reduction_row import ReductionRow
from src.services.reduction_condition_engine import (
    ReductionConditionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_base_system():
    """Create the standard 27-row base system."""

    frame = ReductionFrame(
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
    )

    return ReductionRowGenerator().generate(
        frame
    )


def create_color_rule_set() -> ColorReductionRuleSet:
    """Create the standard color conditions."""

    return ColorReductionRuleSet(
        rules=(
            ColorReductionRule(
                color=ReductionColor.RED,
                cells=(
                    ColoredOutcomeCell(
                        1,
                        Outcome.HOME,
                    ),
                    ColoredOutcomeCell(
                        2,
                        Outcome.DRAW,
                    ),
                    ColoredOutcomeCell(
                        3,
                        Outcome.AWAY,
                    ),
                ),
                min_hits=1,
                max_hits=1,
            ),
            ColorReductionRule(
                color=ReductionColor.YELLOW,
                cells=(
                    ColoredOutcomeCell(
                        1,
                        Outcome.DRAW,
                    ),
                    ColoredOutcomeCell(
                        2,
                        Outcome.HOME,
                    ),
                    ColoredOutcomeCell(
                        3,
                        Outcome.DRAW,
                    ),
                ),
                min_hits=1,
                max_hits=2,
            ),
        )
    )


def create_one_x_two_rule() -> OneXTwoReductionRule:
    """Create the standard 1X2 conditions."""

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


def create_condition_set() -> ReductionConditionSet:
    """Create the complete condition set."""

    return ReductionConditionSet(
        color_rule_set=create_color_rule_set(),
        one_x_two_rule=create_one_x_two_rule(),
        point_rule=create_point_rule(),
    )


def create_result():
    """Create the standard combined result."""

    return ReductionConditionEngine().apply(
        create_base_system(),
        create_condition_set(),
    )


def test_metric_normalizes_label() -> None:
    metric = ReductionMetricEvaluation(
        label="  Röd  ",
        observed_value=1,
        minimum_value=1,
        maximum_value=2,
    )

    assert metric.label == "Röd"
    assert metric.is_approved is True
    assert metric.summary_text == (
        "Röd 1 [1/2]"
    )


def test_metric_can_be_rejected() -> None:
    metric = ReductionMetricEvaluation(
        label="X",
        observed_value=3,
        minimum_value=1,
        maximum_value=2,
    )

    assert metric.is_approved is False


def test_metric_rejects_empty_label() -> None:
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        ReductionMetricEvaluation(
            label="   ",
            observed_value=1,
            minimum_value=0,
            maximum_value=1,
        )


def test_metric_rejects_invalid_interval() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        ReductionMetricEvaluation(
            label="X",
            observed_value=1,
            minimum_value=2,
            maximum_value=1,
        )


def test_condition_evaluation_summary() -> None:
    evaluation = ReductionConditionEvaluation(
        condition_type=(
            ReductionConditionType.POINT
        ),
        metrics=(
            ReductionMetricEvaluation(
                label="Poäng",
                observed_value=11,
                minimum_value=10,
                maximum_value=12,
            ),
        ),
    )

    assert evaluation.is_approved is True
    assert evaluation.summary_text == (
        "Poäng: Poäng 11 [10/12]"
    )


def test_condition_rejects_duplicate_labels() -> None:
    metric = ReductionMetricEvaluation(
        label="X",
        observed_value=1,
        minimum_value=0,
        maximum_value=2,
    )

    with pytest.raises(
        ValueError,
        match="unique",
    ):
        ReductionConditionEvaluation(
            condition_type=(
                ReductionConditionType.ONE_X_TWO
            ),
            metrics=(
                metric,
                metric,
            ),
        )


def test_row_requires_official_condition_order() -> None:
    point_evaluation = ReductionConditionEvaluation(
        condition_type=(
            ReductionConditionType.POINT
        ),
        metrics=(
            ReductionMetricEvaluation(
                "Poäng",
                1,
                0,
                2,
            ),
        ),
    )

    color_evaluation = ReductionConditionEvaluation(
        condition_type=(
            ReductionConditionType.COLOR
        ),
        metrics=(
            ReductionMetricEvaluation(
                "Röd",
                1,
                0,
                1,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="official",
    ):
        ReductionConditionRowEvaluation(
            row=ReductionRow.from_symbols(
                "11111111"
            ),
            condition_evaluations=(
                point_evaluation,
                color_evaluation,
            ),
        )


def test_result_exposes_surviving_rows() -> None:
    result = create_result()

    assert result.original_row_count == 27
    assert result.approved_count == 2
    assert result.rejected_count == 25

    assert tuple(
        row.symbols
        for row in result.approved_rows
    ) == (
        "12X11111",
        "XX111111",
    )


def test_result_exposes_percentages() -> None:
    result = create_result()

    assert result.retained_percentage == Decimal(
        "7.41"
    )
    assert result.reduction_percentage == Decimal(
        "92.59"
    )
    assert result.is_empty is False


def test_result_counts_individual_approvals() -> None:
    result = create_result()

    assert result.approved_count_for_condition(
        ReductionConditionType.COLOR
    ) == 9

    assert result.approved_count_for_condition(
        ReductionConditionType.ONE_X_TWO
    ) == 12

    assert result.approved_count_for_condition(
        ReductionConditionType.POINT
    ) == 8


def test_result_exposes_summary_line() -> None:
    assert create_result().summary_line == (
        "Villkor 3 | Ursprung 27 | "
        "Kvar 2 | Bort 25 | "
        "Reducering 92.59%"
    )


def test_result_returns_one_based_evaluation() -> None:
    result = create_result()

    assert result.evaluation_at(
        1
    ).row == result.base_system.rows[0]


def test_result_rejects_inactive_lookup() -> None:
    point_only_result = (
        ReductionConditionEngine().apply(
            create_base_system(),
            ReductionConditionSet(
                point_rule=create_point_rule()
            ),
        )
    )

    with pytest.raises(
        KeyError,
        match="not active",
    ):
        point_only_result.approved_count_for_condition(
            ReductionConditionType.COLOR
        )


def test_result_rejects_wrong_evaluation_count() -> None:
    result = create_result()

    with pytest.raises(
        ValueError,
        match="one entry",
    ):
        replace(
            result,
            evaluations=result.evaluations[:-1],
        )


def test_result_rejects_changed_row_order() -> None:
    result = create_result()

    with pytest.raises(
        ValueError,
        match="row order",
    ):
        replace(
            result,
            evaluations=tuple(
                reversed(
                    result.evaluations
                )
            ),
        )


def test_result_rejects_changed_condition_types() -> None:
    result = create_result()
    first = result.evaluations[0]

    changed_first = ReductionConditionRowEvaluation(
        row=first.row,
        condition_evaluations=(
            first.condition_evaluations[1:]
        ),
    )

    with pytest.raises(
        ValueError,
        match="active condition types",
    ):
        replace(
            result,
            evaluations=(
                changed_first,
                *result.evaluations[1:],
            ),
        )