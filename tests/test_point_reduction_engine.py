"""Tests for deterministic point reduction."""

import pytest

from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.point_reduction_rule import (
    PointAssignment,
    PointReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
    ReductionFrame,
)
from src.services.point_reduction_engine import (
    PointReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_frame() -> ReductionFrame:
    """Create a 27-row frame."""

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
    )


def create_base_system() -> BaseReductionSystem:
    """Generate the standard base system."""

    return ReductionRowGenerator().generate(
        create_frame()
    )


def create_rule(
    *,
    min_points: int = 10,
    max_points: int = 12,
) -> PointReductionRule:
    """Create the standard point rule."""

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


def test_engine_applies_point_interval() -> None:
    result = PointReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    assert result.approved_count == 8
    assert result.rejected_count == 19


def test_engine_treats_unmarked_cells_as_zero() -> None:
    result = PointReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "21111111"
    )

    assert evaluation.total_points == 9


def test_engine_counts_pointed_spiked_matches() -> None:
    result = PointReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "22211111"
    )

    assert evaluation.total_points == 4


def test_engine_uses_inclusive_boundaries() -> None:
    result = PointReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    lower = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "12X11111"
    )
    upper = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "11211111"
    )

    assert lower.total_points == 10
    assert lower.is_approved is True
    assert upper.total_points == 12
    assert upper.is_approved is True


def test_engine_preserves_base_row_order() -> None:
    base_system = create_base_system()

    result = PointReductionEngine().apply(
        base_system,
        create_rule(),
    )

    assert tuple(
        evaluation.row
        for evaluation in result.evaluations
    ) == base_system.rows


def test_engine_is_deterministic() -> None:
    base_system = create_base_system()
    rule = create_rule()
    engine = PointReductionEngine()

    first = engine.apply(
        base_system,
        rule,
    )
    second = engine.apply(
        base_system,
        rule,
    )

    assert first == second


def test_engine_rejects_invalid_base_system() -> None:
    with pytest.raises(
        TypeError,
        match="BaseReductionSystem",
    ):
        PointReductionEngine().apply(
            object(),  # type: ignore[arg-type]
            create_rule(),
        )


def test_engine_rejects_invalid_rule() -> None:
    with pytest.raises(
        TypeError,
        match="PointReductionRule",
    ):
        PointReductionEngine().apply(
            create_base_system(),
            object(),  # type: ignore[arg-type]
        )


def test_engine_rejects_match_outside_frame() -> None:
    rule = PointReductionRule(
        assignments=(
            PointAssignment(
                match_number=9,
                outcome=Outcome.HOME,
                points=1,
            ),
        ),
        min_points=0,
        max_points=1,
    )

    with pytest.raises(
        ValueError,
        match="outside the reduction frame",
    ):
        PointReductionEngine().apply(
            create_base_system(),
            rule,
        )


def test_engine_rejects_outcome_outside_frame() -> None:
    frame = ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
        ),
    )
    base_system = ReductionRowGenerator().generate(
        frame
    )
    rule = PointReductionRule(
        assignments=(
            PointAssignment(
                match_number=1,
                outcome=Outcome.DRAW,
                points=1,
            ),
        ),
        min_points=0,
        max_points=1,
    )

    with pytest.raises(
        ValueError,
        match="turquoise reduction frame",
    ):
        PointReductionEngine().apply(
            base_system,
            rule,
        )


def test_engine_can_keep_every_row() -> None:
    result = PointReductionEngine().apply(
        create_base_system(),
        create_rule(
            min_points=0,
            max_points=14,
        ),
    )

    assert result.approved_count == 27
    assert result.rejected_count == 0


def test_engine_can_remove_every_row() -> None:
    result = PointReductionEngine().apply(
        create_base_system(),
        create_rule(
            min_points=0,
            max_points=0,
        ),
    )

    assert result.approved_count == 0
    assert result.is_empty is True