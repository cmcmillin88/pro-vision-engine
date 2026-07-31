"""Tests for the common reduction-condition engine."""

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
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.models.reduction_frame import ReductionFrame
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


def create_point_rule(
    *,
    min_points: int = 10,
    max_points: int = 12,
) -> PointReductionRule:
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
        min_points=min_points,
        max_points=max_points,
    )


def create_condition_set() -> ReductionConditionSet:
    """Create the complete standard condition set."""

    return ReductionConditionSet(
        color_rule_set=create_color_rule_set(),
        one_x_two_rule=create_one_x_two_rule(),
        point_rule=create_point_rule(),
    )


def test_engine_applies_all_with_and_logic() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        create_condition_set(),
    )

    assert result.approved_count == 2
    assert result.rejected_count == 25


def test_engine_preserves_independent_results() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        create_condition_set(),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "11211111"
    )

    assert evaluation.evaluation_for(
        ReductionConditionType.POINT
    ).is_approved is True

    assert evaluation.is_approved is False


def test_engine_exposes_metric_values() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        create_condition_set(),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "12X11111"
    )

    color_evaluation = evaluation.evaluation_for(
        ReductionConditionType.COLOR
    )
    one_x_two_evaluation = evaluation.evaluation_for(
        ReductionConditionType.ONE_X_TWO
    )
    point_evaluation = evaluation.evaluation_for(
        ReductionConditionType.POINT
    )

    assert tuple(
        metric.observed_value
        for metric in color_evaluation.metrics
    ) == (
        1,
        1,
    )

    assert tuple(
        metric.observed_value
        for metric in one_x_two_evaluation.metrics
    ) == (
        6,
        1,
        1,
    )

    assert (
        point_evaluation.metrics[0].observed_value
        == 10
    )


def test_engine_supports_one_condition() -> None:
    result = ReductionConditionEngine().apply(
        create_base_system(),
        ReductionConditionSet(
            point_rule=create_point_rule()
        ),
    )

    assert result.approved_count == 8


def test_engine_supports_single_color_and_points() -> None:
    color_rule = ColorReductionRule(
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
    )

    result = ReductionConditionEngine().apply(
        create_base_system(),
        ReductionConditionSet(
            color_rule=color_rule,
            point_rule=create_point_rule(),
        ),
    )

    assert result.condition_set.condition_count == 2
    assert result.approved_count == 3


def test_engine_preserves_base_row_order() -> None:
    base_system = create_base_system()

    result = ReductionConditionEngine().apply(
        base_system,
        create_condition_set(),
    )

    assert tuple(
        evaluation.row
        for evaluation in result.evaluations
    ) == base_system.rows


def test_engine_is_deterministic() -> None:
    base_system = create_base_system()
    condition_set = create_condition_set()
    engine = ReductionConditionEngine()

    first = engine.apply(
        base_system,
        condition_set,
    )
    second = engine.apply(
        base_system,
        condition_set,
    )

    assert first == second


def test_engine_rejects_invalid_base_system() -> None:
    with pytest.raises(
        TypeError,
        match="BaseReductionSystem",
    ):
        ReductionConditionEngine().apply(
            object(),  # type: ignore[arg-type]
            create_condition_set(),
        )


def test_engine_rejects_invalid_condition_set() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionConditionSet",
    ):
        ReductionConditionEngine().apply(
            create_base_system(),
            object(),  # type: ignore[arg-type]
        )


def test_engine_rejects_color_match_outside_frame() -> None:
    color_rule = ColorReductionRule(
        color=ReductionColor.RED,
        cells=(
            ColoredOutcomeCell(
                9,
                Outcome.HOME,
            ),
        ),
        min_hits=0,
        max_hits=1,
    )

    with pytest.raises(
        ValueError,
        match="color cell.*outside",
    ):
        ReductionConditionEngine().apply(
            create_base_system(),
            ReductionConditionSet(
                color_rule=color_rule
            ),
        )


def test_engine_rejects_color_outcome_outside_frame() -> None:
    color_rule = ColorReductionRule(
        color=ReductionColor.RED,
        cells=(
            ColoredOutcomeCell(
                4,
                Outcome.DRAW,
            ),
        ),
        min_hits=0,
        max_hits=1,
    )

    with pytest.raises(
        ValueError,
        match="turquoise",
    ):
        ReductionConditionEngine().apply(
            create_base_system(),
            ReductionConditionSet(
                color_rule=color_rule
            ),
        )


def test_engine_rejects_1x2_maximum_above_frame() -> None:
    rule = OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                Outcome.HOME,
                0,
                9,
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="maximum exceeds",
    ):
        ReductionConditionEngine().apply(
            create_base_system(),
            ReductionConditionSet(
                one_x_two_rule=rule
            ),
        )


def test_engine_rejects_point_match_outside_frame() -> None:
    rule = PointReductionRule(
        assignments=(
            PointAssignment(
                9,
                Outcome.HOME,
                1,
            ),
        ),
        min_points=0,
        max_points=1,
    )

    with pytest.raises(
        ValueError,
        match="point assignment.*outside",
    ):
        ReductionConditionEngine().apply(
            create_base_system(),
            ReductionConditionSet(
                point_rule=rule
            ),
        )


def test_engine_rejects_point_outcome_outside_frame() -> None:
    rule = PointReductionRule(
        assignments=(
            PointAssignment(
                4,
                Outcome.DRAW,
                1,
            ),
        ),
        min_points=0,
        max_points=1,
    )

    with pytest.raises(
        ValueError,
        match="turquoise",
    ):
        ReductionConditionEngine().apply(
            create_base_system(),
            ReductionConditionSet(
                point_rule=rule
            ),
        )