"""Tests for one color-based MIN/MAX rule."""

import pytest

from src.models.color_reduction_rule import (
    ColoredOutcomeCell,
    ColorReductionRule,
    ReductionColor,
)
from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow


def create_rule(
    *,
    min_hits: int = 2,
    max_hits: int = 2,
) -> ColorReductionRule:
    """Create the standard red test rule."""

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
        min_hits=min_hits,
        max_hits=max_hits,
    )


def test_cell_exposes_expected_values() -> None:
    cell = ColoredOutcomeCell(
        match_number=3,
        outcome=Outcome.AWAY,
    )

    assert cell.match_number == 3
    assert cell.outcome is Outcome.AWAY
    assert cell.key == (
        3,
        Outcome.AWAY,
    )
    assert str(cell) == "3:2"


def test_cell_rejects_boolean_match_number() -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        ColoredOutcomeCell(
            match_number=True,  # type: ignore[arg-type]
            outcome=Outcome.HOME,
        )


def test_cell_rejects_non_positive_match_number() -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        ColoredOutcomeCell(
            match_number=0,
            outcome=Outcome.HOME,
        )


def test_cell_rejects_invalid_outcome() -> None:
    with pytest.raises(
        TypeError,
        match="must be an Outcome",
    ):
        ColoredOutcomeCell(
            match_number=1,
            outcome="1",  # type: ignore[arg-type]
        )


def test_rule_exposes_expected_properties() -> None:
    rule = create_rule()

    assert rule.color is ReductionColor.RED
    assert rule.color.display_name == "Röd"
    assert rule.cell_count == 3
    assert rule.marked_match_numbers == (
        1,
        2,
    )
    assert rule.marked_match_count == 2
    assert rule.maximum_possible_hits == 2
    assert rule.condition_text == "2/2"


def test_rule_allows_multiple_cells_for_same_match() -> None:
    rule = create_rule()

    assert rule.cells_for_match(
        2
    ) == (
        Outcome.HOME,
        Outcome.AWAY,
    )


def test_rule_normalizes_cell_order() -> None:
    rule = ColorReductionRule(
        color=ReductionColor.BLUE,
        cells=(
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.AWAY,
            ),
            ColoredOutcomeCell(
                match_number=1,
                outcome=Outcome.DRAW,
            ),
            ColoredOutcomeCell(
                match_number=2,
                outcome=Outcome.HOME,
            ),
        ),
        min_hits=1,
        max_hits=2,
    )

    assert rule.cells == (
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
    )


def test_rule_counts_hits_per_match() -> None:
    rule = create_rule()

    assert rule.hit_count(
        ReductionRow.from_symbols(
            "X2"
        )
    ) == 2

    assert rule.hit_count(
        ReductionRow.from_symbols(
            "11"
        )
    ) == 1


def test_rule_uses_inclusive_interval() -> None:
    rule = create_rule(
        min_hits=1,
        max_hits=2,
    )

    assert rule.is_approved(
        ReductionRow.from_symbols(
            "11"
        )
    ) is True

    assert rule.is_approved(
        ReductionRow.from_symbols(
            "X2"
        )
    ) is True

    assert rule.is_approved(
        ReductionRow.from_symbols(
            "1X"
        )
    ) is False


def test_rule_rejects_invalid_color() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionColor",
    ):
        ColorReductionRule(
            color=object(),  # type: ignore[arg-type]
            cells=(
                ColoredOutcomeCell(
                    match_number=1,
                    outcome=Outcome.HOME,
                ),
            ),
            min_hits=0,
            max_hits=1,
        )


def test_rule_rejects_empty_cells() -> None:
    with pytest.raises(
        ValueError,
        match="at least one marked cell",
    ):
        ColorReductionRule(
            color=ReductionColor.YELLOW,
            cells=(),
            min_hits=0,
            max_hits=0,
        )


def test_rule_rejects_duplicate_cell() -> None:
    cell = ColoredOutcomeCell(
        match_number=1,
        outcome=Outcome.HOME,
    )

    with pytest.raises(
        ValueError,
        match="duplicate marked cells",
    ):
        ColorReductionRule(
            color=ReductionColor.RED,
            cells=(
                cell,
                cell,
            ),
            min_hits=0,
            max_hits=1,
        )


def test_rule_rejects_negative_minimum() -> None:
    with pytest.raises(
        ValueError,
        match="must not be negative",
    ):
        ColorReductionRule(
            color=ReductionColor.RED,
            cells=(
                ColoredOutcomeCell(
                    match_number=1,
                    outcome=Outcome.HOME,
                ),
            ),
            min_hits=-1,
            max_hits=1,
        )


def test_rule_rejects_minimum_above_maximum() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        ColorReductionRule(
            color=ReductionColor.RED,
            cells=(
                ColoredOutcomeCell(
                    match_number=1,
                    outcome=Outcome.HOME,
                ),
            ),
            min_hits=1,
            max_hits=0,
        )


def test_rule_rejects_maximum_above_distinct_match_count() -> None:
    with pytest.raises(
        ValueError,
        match="distinct marked matches",
    ):
        ColorReductionRule(
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
            min_hits=0,
            max_hits=3,
        )