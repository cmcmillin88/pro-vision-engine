"""Tests for completed point-reduction results."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.point_reduction_result import (
    PointReductionResult,
    PointReductionRowEvaluation,
)
from src.models.point_reduction_rule import (
    PointAssignment,
    PointReductionRule,
)
from src.models.reduction_frame import ReductionFrame
from src.services.point_reduction_engine import (
    PointReductionEngine,
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


def create_result() -> PointReductionResult:
    """Create the standard completed result."""

    base_system = ReductionRowGenerator().generate(
        create_frame()
    )

    return PointReductionEngine().apply(
        base_system,
        create_rule(),
    )


def test_result_exposes_approved_rows() -> None:
    result = create_result()

    assert result.original_row_count == 27
    assert result.approved_count == 8
    assert result.rejected_count == 19

    assert tuple(
        row.symbols
        for row in result.approved_rows
    ) == (
        "11211111",
        "1XX11111",
        "1X211111",
        "12111111",
        "12X11111",
        "X1111111",
        "X1X11111",
        "XX111111",
    )


def test_result_exposes_percentages() -> None:
    result = create_result()

    assert result.retained_percentage == Decimal(
        "29.63"
    )
    assert result.reduction_percentage == Decimal(
        "70.37"
    )
    assert result.is_empty is False


def test_result_exposes_point_distribution() -> None:
    result = create_result()

    assert result.point_distribution == (
        (4, 1),
        (5, 1),
        (6, 3),
        (7, 3),
        (8, 4),
        (9, 4),
        (10, 3),
        (11, 3),
        (12, 2),
        (13, 2),
        (14, 1),
    )
    assert result.minimum_observed_points == 4
    assert result.maximum_observed_points == 14


def test_result_counts_rows_for_exact_points() -> None:
    result = create_result()

    assert result.row_count_for_points(
        10
    ) == 3
    assert result.row_count_for_points(
        15
    ) == 0


def test_result_exposes_summary_line() -> None:
    assert create_result().summary_line == (
        "Poäng MIN 10 | MAX 12 | "
        "Ursprung 27 | Kvar 8 | Bort 19 | "
        "Reducering 70.37%"
    )


def test_row_evaluation_exposes_total_and_approval() -> None:
    result = create_result()

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "1X211111"
    )

    assert evaluation.total_points == 11
    assert evaluation.is_approved is True


def test_result_returns_evaluation_by_row_number() -> None:
    result = create_result()

    assert result.evaluation_at(
        1
    ).row == result.base_system.rows[0]


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


def test_result_rejects_invalid_rule() -> None:
    result = create_result()

    with pytest.raises(
        TypeError,
        match="PointReductionRule",
    ):
        replace(
            result,
            rule=object(),  # type: ignore[arg-type]
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


def test_row_evaluation_rejects_wrong_points() -> None:
    result = create_result()
    first = result.evaluations[0]

    changed_first = PointReductionRowEvaluation(
        row=first.row,
        total_points=first.total_points - 1,
        is_approved=first.is_approved,
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        replace(
            result,
            evaluations=(
                changed_first,
                *result.evaluations[1:],
            ),
        )