"""Tests for deterministic point-reduction rules."""

import pytest

from src.models.outcome import Outcome
from src.models.point_reduction_rule import (
    PointAssignment,
    PointReductionRule,
)
from src.models.reduction_row import ReductionRow


def create_rule() -> PointReductionRule:
    """Create the standard point-reduction rule."""

    return PointReductionRule(
        assignments=(
            PointAssignment(3, Outcome.AWAY, 1),
            PointAssignment(1, Outcome.DRAW, 2),
            PointAssignment(2, Outcome.AWAY, 1),
            PointAssignment(4, Outcome.HOME, 2),
            PointAssignment(1, Outcome.HOME, 5),
            PointAssignment(3, Outcome.HOME, 3),
            PointAssignment(2, Outcome.DRAW, 3),
            PointAssignment(3, Outcome.DRAW, 2),
            PointAssignment(2, Outcome.HOME, 4),
        ),
        min_points=10,
        max_points=12,
    )


def test_assignment_exposes_expected_properties() -> None:
    assignment = PointAssignment(
        match_number=2,
        outcome=Outcome.DRAW,
        points=7,
    )

    assert assignment.key == (
        2,
        Outcome.DRAW,
    )
    assert str(assignment) == "2:X=7"


def test_assignment_rejects_invalid_match_number() -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        PointAssignment(
            match_number=0,
            outcome=Outcome.HOME,
            points=1,
        )


def test_assignment_rejects_invalid_outcome() -> None:
    with pytest.raises(
        TypeError,
        match="must be an Outcome",
    ):
        PointAssignment(
            match_number=1,
            outcome="1",  # type: ignore[arg-type]
            points=1,
        )


def test_assignment_rejects_invalid_points_type() -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        PointAssignment(
            match_number=1,
            outcome=Outcome.HOME,
            points=True,  # type: ignore[arg-type]
        )


def test_assignment_rejects_points_outside_range() -> None:
    with pytest.raises(
        ValueError,
        match="between 1 and 99",
    ):
        PointAssignment(
            match_number=1,
            outcome=Outcome.HOME,
            points=0,
        )

    with pytest.raises(
        ValueError,
        match="between 1 and 99",
    ):
        PointAssignment(
            match_number=1,
            outcome=Outcome.HOME,
            points=100,
        )


def test_rule_normalizes_assignments() -> None:
    rule = create_rule()

    assert tuple(
        assignment.key
        for assignment in rule.assignments
    ) == (
        (1, Outcome.HOME),
        (1, Outcome.DRAW),
        (2, Outcome.HOME),
        (2, Outcome.DRAW),
        (2, Outcome.AWAY),
        (3, Outcome.HOME),
        (3, Outcome.DRAW),
        (3, Outcome.AWAY),
        (4, Outcome.HOME),
    )


def test_rule_exposes_expected_properties() -> None:
    rule = create_rule()

    assert rule.assignment_count == 9
    assert rule.marked_match_numbers == (
        1,
        2,
        3,
        4,
    )
    assert rule.marked_match_count == 4
    assert rule.maximum_possible_points == 14
    assert rule.condition_text == "10/12"


def test_rule_returns_assignments_for_match() -> None:
    rule = create_rule()

    assert tuple(
        assignment.points
        for assignment in rule.assignments_for_match(
            2
        )
    ) == (
        4,
        3,
        1,
    )


def test_rule_returns_zero_for_unmarked_cell() -> None:
    assert create_rule().points_for(
        1,
        Outcome.AWAY,
    ) == 0


def test_rule_scores_one_selected_outcome_per_match() -> None:
    assert create_rule().row_points(
        ReductionRow.from_symbols(
            "1X211111"
        )
    ) == 11


def test_rule_counts_pointed_spiked_match() -> None:
    assert create_rule().row_points(
        ReductionRow.from_symbols(
            "22211111"
        )
    ) == 4


def test_rule_uses_inclusive_boundaries() -> None:
    rule = create_rule()

    assert rule.is_approved(
        ReductionRow.from_symbols(
            "11211111"
        )
    ) is True

    assert rule.is_approved(
        ReductionRow.from_symbols(
            "1X211111"
        )
    ) is True

    assert rule.is_approved(
        ReductionRow.from_symbols(
            "11111111"
        )
    ) is False


def test_rule_rejects_non_tuple_assignments() -> None:
    with pytest.raises(
        TypeError,
        match="must be a tuple",
    ):
        PointReductionRule(
            assignments=[],  # type: ignore[arg-type]
            min_points=0,
            max_points=0,
        )


def test_rule_rejects_empty_assignments() -> None:
    with pytest.raises(
        ValueError,
        match="at least one",
    ):
        PointReductionRule(
            assignments=(),
            min_points=0,
            max_points=0,
        )


def test_rule_rejects_invalid_assignment_item() -> None:
    assignment = PointAssignment(
        match_number=1,
        outcome=Outcome.HOME,
        points=1,
    )

    with pytest.raises(
        TypeError,
        match="PointAssignment",
    ):
        PointReductionRule(
            assignments=(
                assignment,
                object(),  # type: ignore[arg-type]
            ),
            min_points=0,
            max_points=1,
        )


def test_rule_rejects_duplicate_cell() -> None:
    assignment = PointAssignment(
        match_number=1,
        outcome=Outcome.HOME,
        points=1,
    )

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        PointReductionRule(
            assignments=(
                assignment,
                assignment,
            ),
            min_points=0,
            max_points=1,
        )


def test_rule_rejects_invalid_interval() -> None:
    assignment = PointAssignment(
        match_number=1,
        outcome=Outcome.HOME,
        points=5,
    )

    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        PointReductionRule(
            assignments=(
                assignment,
            ),
            min_points=4,
            max_points=3,
        )


def test_rule_rejects_maximum_above_possible() -> None:
    assignment = PointAssignment(
        match_number=1,
        outcome=Outcome.HOME,
        points=5,
    )

    with pytest.raises(
        ValueError,
        match="maximum possible",
    ):
        PointReductionRule(
            assignments=(
                assignment,
            ),
            min_points=0,
            max_points=6,
        )


def test_rule_rejects_invalid_row() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionRow",
    ):
        create_rule().row_points(
            object()  # type: ignore[arg-type]
        )