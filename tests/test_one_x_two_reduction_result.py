"""Tests for completed 1-X-2 reduction results."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.models.game_type import GameType
from src.models.one_x_two_reduction_result import (
    OneXTwoReductionResult,
    OneXTwoReductionRowEvaluation,
    OutcomeCountRowEvaluation,
)
from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
    OutcomeCountCondition,
)
from src.models.outcome import Outcome
from src.models.reduction_frame import ReductionFrame
from src.services.one_x_two_reduction_engine import (
    OneXTwoReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_frame() -> ReductionFrame:
    """Create an 81-row Topptipset frame."""

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


def create_rule() -> OneXTwoReductionRule:
    """Create the standard complete 1X2 rule."""

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


def create_result() -> OneXTwoReductionResult:
    """Create the standard completed result."""

    base_system = ReductionRowGenerator().generate(
        create_frame()
    )

    return OneXTwoReductionEngine().apply(
        base_system,
        create_rule(),
    )


def test_result_exposes_jointly_approved_rows() -> None:
    result = create_result()

    assert result.original_row_count == 81
    assert result.approved_count == 36
    assert result.rejected_count == 45

    assert result.approved_rows[0].symbols == (
        "11X21111"
    )
    assert result.approved_rows[-1].symbols == (
        "22X11111"
    )


def test_result_exposes_percentages() -> None:
    result = create_result()

    assert (
        result.retained_percentage
        == Decimal("44.44")
    )
    assert (
        result.reduction_percentage
        == Decimal("55.56")
    )
    assert result.is_empty is False


def test_result_counts_each_condition_independently() -> None:
    result = create_result()

    assert result.approved_count_for_outcome(
        Outcome.HOME
    ) == 56
    assert result.approved_count_for_outcome(
        Outcome.DRAW
    ) == 56
    assert result.approved_count_for_outcome(
        Outcome.AWAY
    ) == 56

    assert result.rejected_count_for_outcome(
        Outcome.HOME
    ) == 25


def test_result_exposes_summary_line() -> None:
    result = create_result()

    assert result.summary_line == (
        "1X2 1 5/6 | X 1/2 | 2 1/2 | "
        "Ursprung 81 | Kvar 36 | Bort 45 | "
        "Reducering 55.56%"
    )


def test_row_evaluation_exposes_total_counts() -> None:
    result = create_result()

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "11X21111"
    )

    assert evaluation.count_for(
        Outcome.HOME
    ) == 6
    assert evaluation.count_for(
        Outcome.DRAW
    ) == 1
    assert evaluation.count_for(
        Outcome.AWAY
    ) == 1
    assert evaluation.is_approved is True


def test_failed_conditions_remain_independent() -> None:
    result = create_result()

    evaluation = next(
        evaluation
        for evaluation in result.evaluations
        if evaluation.row.symbols == "111X1111"
    )

    assert evaluation.approved_outcomes == (
        Outcome.DRAW,
    )
    assert evaluation.rejected_outcomes == (
        Outcome.HOME,
        Outcome.AWAY,
    )
    assert evaluation.is_approved is False


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


def test_result_rejects_invalid_rule() -> None:
    result = create_result()

    with pytest.raises(
        TypeError,
        match="OneXTwoReductionRule",
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


def test_result_rejects_changed_condition_set() -> None:
    result = create_result()
    first = result.evaluations[0]

    changed_home_condition = OutcomeCountCondition(
        outcome=Outcome.HOME,
        min_count=4,
        max_count=8,
    )

    changed_home_evaluation = (
        OutcomeCountRowEvaluation(
            condition=changed_home_condition,
            count=first.row.count(
                Outcome.HOME
            ),
        )
    )

    changed_first = OneXTwoReductionRowEvaluation(
        row=first.row,
        condition_evaluations=(
            changed_home_evaluation,
            *first.condition_evaluations[1:],
        ),
    )

    with pytest.raises(
        ValueError,
        match="condition order",
    ):
        replace(
            result,
            evaluations=(
                changed_first,
                *result.evaluations[1:],
            ),
        )


def test_row_evaluation_rejects_wrong_count() -> None:
    result = create_result()
    first = result.evaluations[0]
    home = first.condition_evaluations[0]

    wrong_home = OutcomeCountRowEvaluation(
        condition=home.condition,
        count=home.count - 1,
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        OneXTwoReductionRowEvaluation(
            row=first.row,
            condition_evaluations=(
                wrong_home,
                *first.condition_evaluations[1:],
            ),
        )


def test_evaluation_at_rejects_invalid_number() -> None:
    with pytest.raises(
        IndexError,
        match="outside",
    ):
        create_result().evaluation_at(
            0
        )


def test_outcome_count_rejects_invalid_outcome() -> None:
    with pytest.raises(
        TypeError,
        match="must be an Outcome",
    ):
        create_result().approved_count_for_outcome(
            "1"  # type: ignore[arg-type]
        )