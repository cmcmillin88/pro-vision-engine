"""Tests for total 1-X-2 outcome-count reduction."""

import pytest

from src.models.game_type import GameType
from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
    OutcomeCountCondition,
)
from src.models.outcome import Outcome
from src.models.reduction_frame import (
    BaseReductionSystem,
    ReductionFrame,
)
from src.services.one_x_two_reduction_engine import (
    OneXTwoReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_frame() -> ReductionFrame:
    """Create an 81-row frame."""

    return ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            Outcome.ordered(),
            Outcome.ordered(),
            Outcome.ordered(),
            Outcome.ordered(),
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


def create_rule() -> OneXTwoReductionRule:
    """Create the standard complete rule."""

    return OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                outcome=Outcome.HOME,
                min_count=5,
                max_count=6,
            ),
            OutcomeCountCondition(
                outcome=Outcome.DRAW,
                min_count=1,
                max_count=2,
            ),
            OutcomeCountCondition(
                outcome=Outcome.AWAY,
                min_count=1,
                max_count=2,
            ),
        )
    )


def test_engine_applies_all_active_conditions() -> None:
    result = OneXTwoReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    assert result.approved_count == 36
    assert result.rejected_count == 45


def test_engine_counts_spiked_matches() -> None:
    result = OneXTwoReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "11X21111"
    )

    assert evaluation.count_for(
        Outcome.HOME
    ) == 6


def test_engine_supports_one_active_condition() -> None:
    rule = OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                outcome=Outcome.HOME,
                min_count=5,
                max_count=6,
            ),
        )
    )

    result = OneXTwoReductionEngine().apply(
        create_base_system(),
        rule,
    )

    assert result.approved_count == 56


def test_engine_uses_inclusive_boundaries() -> None:
    result = OneXTwoReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    lower_boundary = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "1XX21111"
    )

    upper_boundary = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "11X21111"
    )

    assert lower_boundary.count_for(
        Outcome.HOME
    ) == 5
    assert lower_boundary.is_approved is True

    assert upper_boundary.count_for(
        Outcome.HOME
    ) == 6
    assert upper_boundary.is_approved is True


def test_engine_preserves_base_row_order() -> None:
    base_system = create_base_system()

    result = OneXTwoReductionEngine().apply(
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
    engine = OneXTwoReductionEngine()

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
        OneXTwoReductionEngine().apply(
            object(),  # type: ignore[arg-type]
            create_rule(),
        )


def test_engine_rejects_invalid_rule() -> None:
    with pytest.raises(
        TypeError,
        match="OneXTwoReductionRule",
    ):
        OneXTwoReductionEngine().apply(
            create_base_system(),
            object(),  # type: ignore[arg-type]
        )


def test_engine_rejects_bounds_above_match_count() -> None:
    rule = OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                outcome=Outcome.HOME,
                min_count=0,
                max_count=9,
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="match count",
    ):
        OneXTwoReductionEngine().apply(
            create_base_system(),
            rule,
        )


def test_engine_supports_exact_outcome_count() -> None:
    rule = OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                outcome=Outcome.DRAW,
                min_count=2,
                max_count=2,
            ),
        )
    )

    result = OneXTwoReductionEngine().apply(
        create_base_system(),
        rule,
    )

    assert result.approved_count == 24


def test_engine_can_remove_every_row() -> None:
    rule = OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                outcome=Outcome.HOME,
                min_count=0,
                max_count=0,
            ),
        )
    )

    result = OneXTwoReductionEngine().apply(
        create_base_system(),
        rule,
    )

    assert result.approved_count == 0
    assert result.is_empty is True


def test_engine_can_keep_every_row() -> None:
    rule = OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                outcome=Outcome.HOME,
                min_count=4,
                max_count=8,
            ),
        )
    )

    result = OneXTwoReductionEngine().apply(
        create_base_system(),
        rule,
    )

    assert result.approved_count == 81
    assert result.rejected_count == 0


def test_engine_keeps_condition_states_independent() -> None:
    result = OneXTwoReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "111X1111"
    )

    assert evaluation.is_outcome_approved(
        Outcome.HOME
    ) is False
    assert evaluation.is_outcome_approved(
        Outcome.DRAW
    ) is True
    assert evaluation.is_outcome_approved(
        Outcome.AWAY
    ) is False