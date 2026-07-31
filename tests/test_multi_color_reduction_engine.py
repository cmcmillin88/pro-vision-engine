"""Tests for multiple simultaneous color reductions."""

import pytest

from src.models.color_reduction_rule import (
    ColoredOutcomeCell,
    ColorReductionRule,
    ReductionColor,
)
from src.models.color_reduction_rule_set import (
    ColorReductionRuleSet,
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
from src.services.multi_color_reduction_engine import (
    MultiColorReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_frame() -> ReductionFrame:
    """Create a 27-row frame with three open matches."""

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
    """Generate the complete standard frame."""

    return ReductionRowGenerator().generate(
        create_frame()
    )


def create_rule(
    color: ReductionColor,
    outcome: Outcome,
    *,
    min_hits: int,
    max_hits: int,
) -> ColorReductionRule:
    """Create one three-match color rule."""

    return ColorReductionRule(
        color=color,
        cells=tuple(
            ColoredOutcomeCell(
                match_number=match_number,
                outcome=outcome,
            )
            for match_number in range(
                1,
                4,
            )
        ),
        min_hits=min_hits,
        max_hits=max_hits,
    )


def create_rule_set() -> ColorReductionRuleSet:
    """Create the standard red-yellow-blue rules."""

    return ColorReductionRuleSet(
        rules=(
            create_rule(
                ReductionColor.RED,
                Outcome.AWAY,
                min_hits=0,
                max_hits=1,
            ),
            create_rule(
                ReductionColor.YELLOW,
                Outcome.DRAW,
                min_hits=1,
                max_hits=2,
            ),
            create_rule(
                ReductionColor.BLUE,
                Outcome.HOME,
                min_hits=2,
                max_hits=3,
            ),
        )
    )


def test_engine_applies_all_rules_with_and_logic() -> None:
    result = MultiColorReductionEngine().apply(
        create_base_system(),
        create_rule_set(),
    )

    assert result.approved_count == 3
    assert tuple(
        row.symbols
        for row in result.approved_rows
    ) == (
        "11X11111",
        "1X111111",
        "X1111111",
    )


def test_one_failed_color_does_not_change_other_states() -> None:
    result = MultiColorReductionEngine().apply(
        create_base_system(),
        create_rule_set(),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "11111111"
    )

    assert evaluation.is_color_approved(
        ReductionColor.RED
    ) is True
    assert evaluation.is_color_approved(
        ReductionColor.YELLOW
    ) is False
    assert evaluation.is_color_approved(
        ReductionColor.BLUE
    ) is True
    assert evaluation.is_approved is False


def test_each_match_only_affects_the_matching_color_cell() -> None:
    result = MultiColorReductionEngine().apply(
        create_base_system(),
        create_rule_set(),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "1X211111"
    )

    assert evaluation.hit_count_for(
        ReductionColor.RED
    ) == 1
    assert evaluation.hit_count_for(
        ReductionColor.YELLOW
    ) == 1
    assert evaluation.hit_count_for(
        ReductionColor.BLUE
    ) == 1


def test_overlapping_cell_counts_for_each_color() -> None:
    red = ColorReductionRule(
        color=ReductionColor.RED,
        cells=(
            ColoredOutcomeCell(
                match_number=1,
                outcome=Outcome.HOME,
            ),
        ),
        min_hits=1,
        max_hits=1,
    )
    blue = ColorReductionRule(
        color=ReductionColor.BLUE,
        cells=(
            ColoredOutcomeCell(
                match_number=1,
                outcome=Outcome.HOME,
            ),
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.DRAW,
            ),
        ),
        min_hits=2,
        max_hits=2,
    )
    frame = ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            (Outcome.HOME,),
            (Outcome.DRAW,),
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

    result = MultiColorReductionEngine().apply_rules(
        base_system,
        (
            blue,
            red,
        ),
    )

    evaluation = result.evaluations[0]

    assert evaluation.hit_count_for(
        ReductionColor.RED
    ) == 1
    assert evaluation.hit_count_for(
        ReductionColor.BLUE
    ) == 2
    assert evaluation.is_approved is True


def test_multiple_cells_in_one_match_still_give_one_hit() -> None:
    red = ColorReductionRule(
        color=ReductionColor.RED,
        cells=(
            ColoredOutcomeCell(
                match_number=1,
                outcome=Outcome.HOME,
            ),
            ColoredOutcomeCell(
                match_number=1,
                outcome=Outcome.AWAY,
            ),
        ),
        min_hits=1,
        max_hits=1,
    )
    yellow = ColorReductionRule(
        color=ReductionColor.YELLOW,
        cells=(
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.DRAW,
            ),
        ),
        min_hits=0,
        max_hits=1,
    )

    result = MultiColorReductionEngine().apply_rules(
        create_base_system(),
        (
            red,
            yellow,
        ),
    )

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "12111111"
    )

    assert evaluation.hit_count_for(
        ReductionColor.RED
    ) == 1


def test_apply_rules_creates_rule_set() -> None:
    rule_set = create_rule_set()

    result = MultiColorReductionEngine().apply_rules(
        create_base_system(),
        rule_set.rules,
    )

    assert result.rule_set == rule_set
    assert result.approved_count == 3


def test_engine_preserves_base_row_order() -> None:
    base_system = create_base_system()

    result = MultiColorReductionEngine().apply(
        base_system,
        create_rule_set(),
    )

    assert tuple(
        evaluation.row
        for evaluation in result.evaluations
    ) == base_system.rows


def test_engine_is_deterministic() -> None:
    base_system = create_base_system()
    rule_set = create_rule_set()
    engine = MultiColorReductionEngine()

    first = engine.apply(
        base_system,
        rule_set,
    )
    second = engine.apply(
        base_system,
        rule_set,
    )

    assert first == second


def test_engine_rejects_invalid_base_system() -> None:
    with pytest.raises(
        TypeError,
        match="BaseReductionSystem",
    ):
        MultiColorReductionEngine().apply(
            object(),  # type: ignore[arg-type]
            create_rule_set(),
        )


def test_engine_rejects_invalid_rule_set() -> None:
    with pytest.raises(
        TypeError,
        match="ColorReductionRuleSet",
    ):
        MultiColorReductionEngine().apply(
            create_base_system(),
            object(),  # type: ignore[arg-type]
        )


def test_engine_rejects_invalid_single_color_engine() -> None:
    with pytest.raises(
        TypeError,
        match="ColorReductionEngine",
    ):
        MultiColorReductionEngine(
            single_color_engine=object(),  # type: ignore[arg-type]
        )


def test_engine_rejects_match_outside_frame() -> None:
    red = ColorReductionRule(
        color=ReductionColor.RED,
        cells=(
            ColoredOutcomeCell(
                match_number=9,
                outcome=Outcome.HOME,
            ),
        ),
        min_hits=0,
        max_hits=0,
    )
    blue = create_rule(
        ReductionColor.BLUE,
        Outcome.HOME,
        min_hits=0,
        max_hits=3,
    )

    with pytest.raises(
        ValueError,
        match="outside the reduction frame",
    ):
        MultiColorReductionEngine().apply_rules(
            create_base_system(),
            (
                red,
                blue,
            ),
        )


def test_engine_rejects_colored_outcome_outside_frame() -> None:
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
    red = ColorReductionRule(
        color=ReductionColor.RED,
        cells=(
            ColoredOutcomeCell(
                match_number=1,
                outcome=Outcome.DRAW,
            ),
        ),
        min_hits=0,
        max_hits=0,
    )
    blue = ColorReductionRule(
        color=ReductionColor.BLUE,
        cells=(
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.HOME,
            ),
        ),
        min_hits=1,
        max_hits=1,
    )

    with pytest.raises(
        ValueError,
        match="turquoise reduction frame",
    ):
        MultiColorReductionEngine().apply_rules(
            base_system,
            (
                red,
                blue,
            ),
        )