"""Tests for the first color-reduction engine."""

import pytest

from src.models.color_reduction_rule import (
    ColoredOutcomeCell,
    ColorReductionRule,
    ReductionColor,
)
from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.reduction_frame import (
    BaseReductionSystem,
    ReductionFrame,
)
from src.services.color_reduction_engine import (
    ColorReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_frame() -> ReductionFrame:
    """Create a deterministic four-row frame."""

    return ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            (
                Outcome.HOME,
                Outcome.DRAW,
            ),
            (
                Outcome.HOME,
                Outcome.AWAY,
            ),
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
            ),
        ),
    )


def create_base_system() -> BaseReductionSystem:
    """Create the complete four-row base system."""

    return ReductionRowGenerator().generate(
        create_frame()
    )


def create_exact_two_rule() -> ColorReductionRule:
    """Create the standard exact-two-hits rule."""

    return ColorReductionRule(
        color=ReductionColor.RED,
        cells=(
            ColoredOutcomeCell(
                match_number=1,
                outcome=Outcome.DRAW,
            ),
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.HOME,
            ),
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.AWAY,
            ),
        ),
        min_hits=2,
        max_hits=2,
    )


def test_engine_applies_exact_two_hit_rule() -> None:
    result = ColorReductionEngine().apply(
        create_base_system(),
        create_exact_two_rule(),
    )

    assert result.approved_count == 2
    assert result.rejected_count == 2
    assert tuple(
        row.symbols
        for row in result.approved_rows
    ) == (
        "X1111111",
        "X2111111",
    )


def test_multiple_cells_in_same_match_count_as_one_hit() -> None:
    result = ColorReductionEngine().apply(
        create_base_system(),
        create_exact_two_rule(),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "X2111111"
    )

    assert evaluation.hit_count == 2
    assert evaluation.is_approved is True


def test_engine_uses_inclusive_minimum_and_maximum() -> None:
    rule = ColorReductionRule(
        color=ReductionColor.YELLOW,
        cells=create_exact_two_rule().cells,
        min_hits=1,
        max_hits=2,
    )

    result = ColorReductionEngine().apply(
        create_base_system(),
        rule,
    )

    assert result.approved_count == 4
    assert result.rejected_count == 0


def test_engine_preserves_original_row_order() -> None:
    base_system = create_base_system()

    result = ColorReductionEngine().apply(
        base_system,
        create_exact_two_rule(),
    )

    assert tuple(
        evaluation.row
        for evaluation in result.evaluations
    ) == base_system.rows


def test_engine_can_remove_every_row() -> None:
    rule = ColorReductionRule(
        color=ReductionColor.BLUE,
        cells=(
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.HOME,
            ),
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.AWAY,
            ),
        ),
        min_hits=0,
        max_hits=0,
    )

    result = ColorReductionEngine().apply(
        create_base_system(),
        rule,
    )

    assert result.approved_count == 0
    assert result.rejected_count == 4
    assert result.is_empty is True


def test_engine_can_keep_every_row() -> None:
    rule = ColorReductionRule(
        color=ReductionColor.PINK,
        cells=(
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.HOME,
            ),
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.AWAY,
            ),
        ),
        min_hits=1,
        max_hits=1,
    )

    result = ColorReductionEngine().apply(
        create_base_system(),
        rule,
    )

    assert result.approved_count == 4
    assert result.rejected_count == 0


def test_engine_rejects_match_outside_frame() -> None:
    rule = ColorReductionRule(
        color=ReductionColor.PURPLE,
        cells=(
            ColoredOutcomeCell(
                match_number=9,
                outcome=Outcome.HOME,
            ),
        ),
        min_hits=0,
        max_hits=0,
    )

    with pytest.raises(
        ValueError,
        match="outside the reduction frame",
    ):
        ColorReductionEngine().apply(
            create_base_system(),
            rule,
        )


def test_engine_rejects_colored_outcome_outside_frame() -> None:
    rule = ColorReductionRule(
        color=ReductionColor.GREEN,
        cells=(
            ColoredOutcomeCell(
                match_number=3,
                outcome=Outcome.DRAW,
            ),
        ),
        min_hits=0,
        max_hits=0,
    )

    with pytest.raises(
        ValueError,
        match="turquoise reduction frame",
    ):
        ColorReductionEngine().apply(
            create_base_system(),
            rule,
        )


def test_engine_rejects_invalid_base_system() -> None:
    with pytest.raises(
        TypeError,
        match="BaseReductionSystem",
    ):
        ColorReductionEngine().apply(
            object(),  # type: ignore[arg-type]
            create_exact_two_rule(),
        )


def test_engine_rejects_invalid_rule() -> None:
    with pytest.raises(
        TypeError,
        match="ColorReductionRule",
    ):
        ColorReductionEngine().apply(
            create_base_system(),
            object(),  # type: ignore[arg-type]
        )


def test_engine_is_deterministic() -> None:
    base_system = create_base_system()
    rule = create_exact_two_rule()
    engine = ColorReductionEngine()

    first_result = engine.apply(
        base_system,
        rule,
    )
    second_result = engine.apply(
        base_system,
        rule,
    )

    assert first_result == second_result