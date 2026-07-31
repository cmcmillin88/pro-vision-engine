"""Tests for completed single-color reduction results."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.models.color_reduction_result import (
    ColorReductionResult,
)
from src.models.color_reduction_rule import (
    ColoredOutcomeCell,
    ColorReductionRule,
    ReductionColor,
)
from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.reduction_frame import ReductionFrame
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


def create_rule() -> ColorReductionRule:
    """Create a red exact-two-hits rule."""

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


def create_result() -> ColorReductionResult:
    """Create the standard completed result."""

    base_system = ReductionRowGenerator().generate(
        create_frame()
    )

    return ColorReductionEngine().apply(
        base_system,
        create_rule(),
    )


def test_result_exposes_approved_and_rejected_rows() -> None:
    result = create_result()

    assert result.original_row_count == 4
    assert result.approved_count == 2
    assert result.rejected_count == 2

    assert tuple(
        row.symbols
        for row in result.approved_rows
    ) == (
        "X1111111",
        "X2111111",
    )

    assert tuple(
        row.symbols
        for row in result.rejected_rows
    ) == (
        "11111111",
        "12111111",
    )


def test_result_exposes_percentages() -> None:
    result = create_result()

    assert (
        result.retained_percentage
        == Decimal("50.00")
    )
    assert (
        result.reduction_percentage
        == Decimal("50.00")
    )
    assert result.is_empty is False


def test_result_exposes_summary_line() -> None:
    result = create_result()

    assert result.summary_line == (
        "Färg Röd | MIN 2 | MAX 2 | "
        "Ursprung 4 | Kvar 2 | Bort 2 | "
        "Reducering 50.00%"
    )


def test_result_rejects_invalid_base_system() -> None:
    result = create_result()

    with pytest.raises(
        TypeError,
        match="BaseReductionSystem",
    ):
        ColorReductionResult(
            base_system=object(),  # type: ignore[arg-type]
            rule=result.rule,
            evaluations=result.evaluations,
        )


def test_result_rejects_invalid_rule() -> None:
    result = create_result()

    with pytest.raises(
        TypeError,
        match="ColorReductionRule",
    ):
        replace(
            result,
            rule=object(),  # type: ignore[arg-type]
        )


def test_result_rejects_non_tuple_evaluations() -> None:
    result = create_result()

    with pytest.raises(
        TypeError,
        match="must be a tuple",
    ):
        replace(
            result,
            evaluations=list(  # type: ignore[arg-type]
                result.evaluations
            ),
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


def test_result_rejects_wrong_hit_count() -> None:
    result = create_result()

    changed_first = replace(
        result.evaluations[0],
        hit_count=2,
    )

    with pytest.raises(
        ValueError,
        match="hit_count",
    ):
        replace(
            result,
            evaluations=(
                changed_first,
                *result.evaluations[1:],
            ),
        )


def test_result_rejects_wrong_approval() -> None:
    result = create_result()

    changed_first = replace(
        result.evaluations[0],
        is_approved=True,
    )

    with pytest.raises(
        ValueError,
        match="approval",
    ):
        replace(
            result,
            evaluations=(
                changed_first,
                *result.evaluations[1:],
            ),
        )