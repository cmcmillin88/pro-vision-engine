"""Tests for total 1-X-2 outcome-count rules."""

import pytest

from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
    OutcomeCountCondition,
)
from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow


def create_rule() -> OneXTwoReductionRule:
    """Create the standard three-condition rule."""

    return OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                outcome=Outcome.AWAY,
                min_count=1,
                max_count=2,
            ),
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
        )
    )


def test_condition_exposes_expected_properties() -> None:
    condition = OutcomeCountCondition(
        outcome=Outcome.DRAW,
        min_count=1,
        max_count=3,
    )

    assert condition.outcome is Outcome.DRAW
    assert condition.min_count == 1
    assert condition.max_count == 3
    assert condition.condition_text == "X 1/3"


def test_condition_counts_and_uses_inclusive_interval() -> None:
    condition = OutcomeCountCondition(
        outcome=Outcome.DRAW,
        min_count=1,
        max_count=2,
    )

    assert condition.count_in(
        ReductionRow.from_symbols(
            "11XX22"
        )
    ) == 2

    assert condition.is_approved(
        ReductionRow.from_symbols(
            "11X222"
        )
    ) is True

    assert condition.is_approved(
        ReductionRow.from_symbols(
            "111222"
        )
    ) is False


def test_condition_rejects_invalid_outcome() -> None:
    with pytest.raises(
        TypeError,
        match="must be an Outcome",
    ):
        OutcomeCountCondition(
            outcome="1",  # type: ignore[arg-type]
            min_count=0,
            max_count=1,
        )


def test_condition_rejects_boolean_minimum() -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        OutcomeCountCondition(
            outcome=Outcome.HOME,
            min_count=True,  # type: ignore[arg-type]
            max_count=1,
        )


def test_condition_rejects_negative_count() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        OutcomeCountCondition(
            outcome=Outcome.HOME,
            min_count=-1,
            max_count=2,
        )


def test_condition_rejects_minimum_above_maximum() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        OutcomeCountCondition(
            outcome=Outcome.HOME,
            min_count=3,
            max_count=2,
        )


def test_rule_normalizes_to_official_order() -> None:
    rule = create_rule()

    assert rule.outcomes == (
        Outcome.HOME,
        Outcome.DRAW,
        Outcome.AWAY,
    )


def test_rule_exposes_condition_properties() -> None:
    rule = create_rule()

    assert rule.condition_count == 3
    assert rule.condition_pattern == (
        "1 5/6 | X 1/2 | 2 1/2"
    )


def test_rule_counts_every_active_outcome() -> None:
    rule = create_rule()
    row = ReductionRow.from_symbols(
        "11111X22"
    )

    assert rule.count_values(
        row
    ) == (
        5,
        1,
        2,
    )


def test_rule_uses_and_logic_between_conditions() -> None:
    rule = create_rule()

    assert rule.approval_states(
        ReductionRow.from_symbols(
            "11111X22"
        )
    ) == (
        True,
        True,
        True,
    )

    assert rule.is_approved(
        ReductionRow.from_symbols(
            "11111X22"
        )
    ) is True

    assert rule.is_approved(
        ReductionRow.from_symbols(
            "111111X1"
        )
    ) is False


def test_rule_supports_one_active_condition() -> None:
    rule = OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                outcome=Outcome.DRAW,
                min_count=2,
                max_count=3,
            ),
        )
    )

    assert rule.condition_count == 1
    assert rule.outcomes == (
        Outcome.DRAW,
    )


def test_rule_rejects_non_tuple_conditions() -> None:
    with pytest.raises(
        TypeError,
        match="must be a tuple",
    ):
        OneXTwoReductionRule(
            conditions=[],  # type: ignore[arg-type]
        )


def test_rule_rejects_empty_conditions() -> None:
    with pytest.raises(
        ValueError,
        match="at least one",
    ):
        OneXTwoReductionRule(
            conditions=()
        )


def test_rule_rejects_more_than_three_conditions() -> None:
    condition = OutcomeCountCondition(
        outcome=Outcome.HOME,
        min_count=0,
        max_count=1,
    )

    with pytest.raises(
        ValueError,
        match="at most three",
    ):
        OneXTwoReductionRule(
            conditions=(
                condition,
                condition,
                condition,
                condition,
            )
        )


def test_rule_rejects_invalid_condition_item() -> None:
    condition = OutcomeCountCondition(
        outcome=Outcome.HOME,
        min_count=0,
        max_count=1,
    )

    with pytest.raises(
        TypeError,
        match="OutcomeCountCondition",
    ):
        OneXTwoReductionRule(
            conditions=(
                condition,
                object(),  # type: ignore[arg-type]
            )
        )


def test_rule_rejects_duplicate_outcomes() -> None:
    with pytest.raises(
        ValueError,
        match="only appear once",
    ):
        OneXTwoReductionRule(
            conditions=(
                OutcomeCountCondition(
                    outcome=Outcome.HOME,
                    min_count=0,
                    max_count=4,
                ),
                OutcomeCountCondition(
                    outcome=Outcome.HOME,
                    min_count=1,
                    max_count=5,
                ),
            )
        )


def test_condition_for_rejects_invalid_outcome() -> None:
    with pytest.raises(
        TypeError,
        match="must be an Outcome",
    ):
        create_rule().condition_for(
            "1"  # type: ignore[arg-type]
        )


def test_condition_for_rejects_inactive_outcome() -> None:
    rule = OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                outcome=Outcome.HOME,
                min_count=0,
                max_count=8,
            ),
        )
    )

    with pytest.raises(
        KeyError,
        match="X",
    ):
        rule.condition_for(
            Outcome.DRAW
        )


def test_count_values_rejects_invalid_row() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionRow",
    ):
        create_rule().count_values(
            object()  # type: ignore[arg-type]
        )