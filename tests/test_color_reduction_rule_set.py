"""Tests for multiple independent color rules."""

import pytest

from src.models.color_reduction_rule import (
    ColoredOutcomeCell,
    ColorReductionRule,
    ReductionColor,
)
from src.models.color_reduction_rule_set import (
    ColorReductionRuleSet,
)
from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow


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
    """Create the standard three-color rule set."""

    red = create_rule(
        ReductionColor.RED,
        Outcome.AWAY,
        min_hits=0,
        max_hits=1,
    )
    yellow = create_rule(
        ReductionColor.YELLOW,
        Outcome.DRAW,
        min_hits=1,
        max_hits=2,
    )
    blue = create_rule(
        ReductionColor.BLUE,
        Outcome.HOME,
        min_hits=2,
        max_hits=3,
    )

    return ColorReductionRuleSet(
        rules=(
            blue,
            red,
            yellow,
        )
    )


def test_rule_set_normalizes_color_order() -> None:
    rule_set = create_rule_set()

    assert rule_set.colors == (
        ReductionColor.RED,
        ReductionColor.YELLOW,
        ReductionColor.BLUE,
    )
    assert rule_set.rule_count == 3


def test_rule_set_exposes_condition_pattern() -> None:
    rule_set = create_rule_set()

    assert rule_set.condition_pattern == (
        "Röd 0/1 | Gul 1/2 | Blå 2/3"
    )


def test_rule_set_returns_rule_for_color() -> None:
    rule_set = create_rule_set()

    assert (
        rule_set.rule_for_color(
            ReductionColor.BLUE
        ).color
        is ReductionColor.BLUE
    )


def test_rule_set_counts_each_color_independently() -> None:
    rule_set = create_rule_set()
    row = ReductionRow.from_symbols(
        "11X"
    )

    assert rule_set.hit_counts(
        row
    ) == (
        0,
        1,
        2,
    )


def test_rule_set_returns_independent_approval_states() -> None:
    rule_set = create_rule_set()
    row = ReductionRow.from_symbols(
        "11X"
    )

    assert rule_set.approval_states(
        row
    ) == (
        True,
        True,
        True,
    )


def test_rule_set_approves_only_when_every_color_approves() -> None:
    rule_set = create_rule_set()

    assert rule_set.is_approved(
        ReductionRow.from_symbols(
            "11X"
        )
    ) is True

    assert rule_set.is_approved(
        ReductionRow.from_symbols(
            "111"
        )
    ) is False


def test_same_cell_may_belong_to_multiple_colors() -> None:
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
    rule_set = ColorReductionRuleSet(
        rules=(
            blue,
            red,
        )
    )
    row = ReductionRow.from_symbols(
        "1X"
    )

    assert rule_set.hit_counts(
        row
    ) == (
        1,
        2,
    )
    assert rule_set.is_approved(
        row
    ) is True


def test_rule_set_rejects_non_tuple_rules() -> None:
    with pytest.raises(
        TypeError,
        match="must be a tuple",
    ):
        ColorReductionRuleSet(
            rules=[],  # type: ignore[arg-type]
        )


def test_rule_set_requires_at_least_two_rules() -> None:
    with pytest.raises(
        ValueError,
        match="at least two",
    ):
        ColorReductionRuleSet(
            rules=(
                create_rule(
                    ReductionColor.RED,
                    Outcome.HOME,
                    min_hits=0,
                    max_hits=1,
                ),
            )
        )


def test_rule_set_rejects_too_many_rules() -> None:
    rule = create_rule(
        ReductionColor.RED,
        Outcome.HOME,
        min_hits=0,
        max_hits=1,
    )

    with pytest.raises(
        ValueError,
        match="supported colors",
    ):
        ColorReductionRuleSet(
            rules=(
                rule,
                rule,
                rule,
                rule,
                rule,
                rule,
                rule,
            )
        )


def test_rule_set_rejects_invalid_rule_item() -> None:
    red = create_rule(
        ReductionColor.RED,
        Outcome.HOME,
        min_hits=0,
        max_hits=1,
    )

    with pytest.raises(
        TypeError,
        match="ColorReductionRule",
    ):
        ColorReductionRuleSet(
            rules=(
                red,
                object(),  # type: ignore[arg-type]
            )
        )


def test_rule_set_rejects_duplicate_colors() -> None:
    first_red = create_rule(
        ReductionColor.RED,
        Outcome.HOME,
        min_hits=0,
        max_hits=1,
    )
    second_red = create_rule(
        ReductionColor.RED,
        Outcome.DRAW,
        min_hits=0,
        max_hits=1,
    )

    with pytest.raises(
        ValueError,
        match="only appear once",
    ):
        ColorReductionRuleSet(
            rules=(
                first_red,
                second_red,
            )
        )


def test_rule_for_color_rejects_invalid_color() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionColor",
    ):
        create_rule_set().rule_for_color(
            "red"  # type: ignore[arg-type]
        )


def test_rule_for_color_rejects_inactive_color() -> None:
    with pytest.raises(
        KeyError,
        match="green",
    ):
        create_rule_set().rule_for_color(
            ReductionColor.GREEN
        )


def test_hit_counts_rejects_invalid_row() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionRow",
    ):
        create_rule_set().hit_counts(
            object()  # type: ignore[arg-type]
        )