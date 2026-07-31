"""Tests for combined multi-color reduction results."""

from dataclasses import replace
from decimal import Decimal

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
from src.models.multi_color_reduction_result import (
    ColorRuleRowEvaluation,
    MultiColorReductionResult,
    MultiColorReductionRowEvaluation,
)
from src.models.outcome import Outcome
from src.models.reduction_frame import ReductionFrame
from src.services.multi_color_reduction_engine import (
    MultiColorReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_frame() -> ReductionFrame:
    """Create a 27-row Topptipset frame."""

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


def create_rule(
    color: ReductionColor,
    outcome: Outcome,
    *,
    min_hits: int,
    max_hits: int,
) -> ColorReductionRule:
    """Create one standard three-match rule."""

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
    """Create the standard combined rules."""

    return ColorReductionRuleSet(
        rules=(
            create_rule(
                ReductionColor.BLUE,
                Outcome.HOME,
                min_hits=2,
                max_hits=3,
            ),
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
        )
    )


def create_result() -> MultiColorReductionResult:
    """Create the standard 27-row result."""

    base_system = ReductionRowGenerator().generate(
        create_frame()
    )

    return MultiColorReductionEngine().apply(
        base_system,
        create_rule_set(),
    )


def test_result_exposes_jointly_approved_rows() -> None:
    result = create_result()

    assert result.original_row_count == 27
    assert result.approved_count == 3
    assert result.rejected_count == 24

    assert tuple(
        row.symbols
        for row in result.approved_rows
    ) == (
        "11X11111",
        "1X111111",
        "X1111111",
    )


def test_result_exposes_percentages() -> None:
    result = create_result()

    assert (
        result.retained_percentage
        == Decimal("11.11")
    )
    assert (
        result.reduction_percentage
        == Decimal("88.89")
    )
    assert result.is_empty is False


def test_result_counts_each_color_independently() -> None:
    result = create_result()

    assert result.approved_count_for_color(
        ReductionColor.RED
    ) == 20
    assert result.approved_count_for_color(
        ReductionColor.YELLOW
    ) == 18
    assert result.approved_count_for_color(
        ReductionColor.BLUE
    ) == 7

    assert result.rejected_count_for_color(
        ReductionColor.BLUE
    ) == 20


def test_result_exposes_summary_line() -> None:
    result = create_result()

    assert result.summary_line == (
        "Färger Röd 0/1 | Gul 1/2 | Blå 2/3 | "
        "Ursprung 27 | Kvar 3 | Bort 24 | "
        "Reducering 88.89%"
    )


def test_row_evaluation_keeps_colors_independent() -> None:
    result = create_result()

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "11111111"
    )

    assert evaluation.approved_colors == (
        ReductionColor.RED,
        ReductionColor.BLUE,
    )
    assert evaluation.rejected_colors == (
        ReductionColor.YELLOW,
    )
    assert evaluation.is_approved is False


def test_row_evaluation_returns_color_details() -> None:
    result = create_result()
    evaluation = result.approved_evaluations[0]

    assert evaluation.hit_count_for(
        ReductionColor.RED
    ) == 0
    assert evaluation.hit_count_for(
        ReductionColor.YELLOW
    ) == 1
    assert evaluation.hit_count_for(
        ReductionColor.BLUE
    ) == 2
    assert evaluation.is_approved is True


def test_result_returns_evaluation_by_row_number() -> None:
    result = create_result()

    assert (
        result.evaluation_at(
            1
        ).row
        == result.base_system.rows[0]
    )


def test_result_rejects_invalid_base_system() -> None:
    result = create_result()

    with pytest.raises(
        TypeError,
        match="BaseReductionSystem",
    ):
        replace(
            result,
            base_system=object(),  # type: ignore[arg-type]
        )


def test_result_rejects_invalid_rule_set() -> None:
    result = create_result()

    with pytest.raises(
        TypeError,
        match="ColorReductionRuleSet",
    ):
        replace(
            result,
            rule_set=object(),  # type: ignore[arg-type]
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


def test_result_rejects_changed_color_order() -> None:
    result = create_result()
    first = result.evaluations[0]

    changed_first = MultiColorReductionRowEvaluation(
        row=first.row,
        rule_evaluations=tuple(
            reversed(
                first.rule_evaluations
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match="color order",
    ):
        replace(
            result,
            evaluations=(
                changed_first,
                *result.evaluations[1:],
            ),
        )


def test_row_evaluation_rejects_wrong_hit_count() -> None:
    result = create_result()
    first = result.evaluations[0]
    red = first.rule_evaluations[0]

    wrong_red = ColorRuleRowEvaluation(
        rule=red.rule,
        hit_count=1,
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        MultiColorReductionRowEvaluation(
            row=first.row,
            rule_evaluations=(
                wrong_red,
                *first.rule_evaluations[1:],
            ),
        )


def test_evaluation_at_rejects_invalid_number() -> None:
    result = create_result()

    with pytest.raises(
        IndexError,
        match="outside",
    ):
        result.evaluation_at(
            0
        )