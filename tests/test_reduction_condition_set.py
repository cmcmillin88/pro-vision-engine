"""Tests for common reduction-condition sets."""

from datetime import datetime, timezone

import pytest

from src.models.color_reduction_rule import (
    ColorReductionRule,
    ColoredOutcomeCell,
    ReductionColor,
)
from src.models.color_reduction_rule_set import (
    ColorReductionRuleSet,
)
from src.models.odds_reduction_rule import (
    OddsReductionRule,
    OddsReductionSnapshot,
)
from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
    OutcomeCountCondition,
)
from src.models.outcome import Outcome
from src.models.point_reduction_rule import (
    PointAssignment,
    PointReductionRule,
)
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.models.reduction_row import ReductionRow
from src.models.three_way_odds import ThreeWayOdds


def create_color_rule_set() -> ColorReductionRuleSet:
    """Create the standard two-color rule set."""

    return ColorReductionRuleSet(
        rules=(
            ColorReductionRule(
                color=ReductionColor.RED,
                cells=(
                    ColoredOutcomeCell(
                        1,
                        Outcome.HOME,
                    ),
                    ColoredOutcomeCell(
                        2,
                        Outcome.DRAW,
                    ),
                    ColoredOutcomeCell(
                        3,
                        Outcome.AWAY,
                    ),
                ),
                min_hits=1,
                max_hits=1,
            ),
            ColorReductionRule(
                color=ReductionColor.YELLOW,
                cells=(
                    ColoredOutcomeCell(
                        1,
                        Outcome.DRAW,
                    ),
                    ColoredOutcomeCell(
                        2,
                        Outcome.HOME,
                    ),
                    ColoredOutcomeCell(
                        3,
                        Outcome.DRAW,
                    ),
                ),
                min_hits=1,
                max_hits=2,
            ),
        )
    )


def create_one_x_two_rule() -> OneXTwoReductionRule:
    """Create the standard 1X2 rule."""

    return OneXTwoReductionRule(
        conditions=(
            OutcomeCountCondition(
                Outcome.HOME,
                5,
                6,
            ),
            OutcomeCountCondition(
                Outcome.DRAW,
                1,
                2,
            ),
            OutcomeCountCondition(
                Outcome.AWAY,
                0,
                1,
            ),
        )
    )


def create_point_rule() -> PointReductionRule:
    """Create the standard point rule."""

    return PointReductionRule(
        assignments=(
            PointAssignment(
                1,
                Outcome.HOME,
                5,
            ),
            PointAssignment(
                1,
                Outcome.DRAW,
                2,
            ),
            PointAssignment(
                2,
                Outcome.HOME,
                4,
            ),
            PointAssignment(
                2,
                Outcome.DRAW,
                3,
            ),
            PointAssignment(
                2,
                Outcome.AWAY,
                1,
            ),
            PointAssignment(
                3,
                Outcome.HOME,
                3,
            ),
            PointAssignment(
                3,
                Outcome.DRAW,
                2,
            ),
            PointAssignment(
                3,
                Outcome.AWAY,
                1,
            ),
            PointAssignment(
                4,
                Outcome.HOME,
                2,
            ),
        ),
        min_points=10,
        max_points=12,
    )


def create_odds_rule() -> OddsReductionRule:
    """Create one complete eight-match frozen odds rule."""

    return OddsReductionRule(
        snapshot=OddsReductionSnapshot(
            captured_at=datetime(
                2026,
                7,
                31,
                18,
                0,
                tzinfo=timezone.utc,
            ),
            match_odds=tuple(
                ThreeWayOdds(
                    "2",
                    "3",
                    "4",
                )
                for _ in range(8)
            ),
        ),
        min_total_odds="100",
        max_total_odds="10000",
    )


def create_condition_set() -> ReductionConditionSet:
    """Create the standard complete pre-odds condition set."""

    return ReductionConditionSet(
        color_rule_set=create_color_rule_set(),
        one_x_two_rule=create_one_x_two_rule(),
        point_rule=create_point_rule(),
    )


def test_condition_type_order_and_names() -> None:
    assert ReductionConditionType.ordered() == (
        ReductionConditionType.COLOR,
        ReductionConditionType.ONE_X_TWO,
        ReductionConditionType.POINT,
        ReductionConditionType.ODDS,
    )

    assert tuple(
        condition_type.display_name
        for condition_type
        in ReductionConditionType.ordered()
    ) == (
        "Färg",
        "1X2",
        "Poäng",
        "Odds",
    )


def test_set_exposes_active_types() -> None:
    condition_set = create_condition_set()

    assert condition_set.condition_types == (
        ReductionConditionType.COLOR,
        ReductionConditionType.ONE_X_TWO,
        ReductionConditionType.POINT,
    )
    assert condition_set.condition_count == 3


def test_set_exposes_color_rules() -> None:
    condition_set = create_condition_set()

    assert condition_set.has_color_condition is True
    assert condition_set.color_rule_count == 2

    assert tuple(
        rule.color
        for rule in condition_set.color_rules
    ) == (
        ReductionColor.RED,
        ReductionColor.YELLOW,
    )


def test_set_exposes_atomic_condition_count() -> None:
    assert (
        create_condition_set().atomic_condition_count
        == 6
    )


def test_set_exposes_condition_pattern() -> None:
    assert create_condition_set().condition_pattern == (
        "Färg Röd 1/1 + Gul 1/2 | "
        "1X2 1 5/6 | X 1/2 | 2 0/1 | "
        "Poäng 10/12"
    )


def test_set_supports_single_color_rule() -> None:
    rule = ColorReductionRule(
        color=ReductionColor.RED,
        cells=(
            ColoredOutcomeCell(
                1,
                Outcome.HOME,
            ),
        ),
        min_hits=0,
        max_hits=1,
    )

    condition_set = ReductionConditionSet(
        color_rule=rule
    )

    assert condition_set.condition_types == (
        ReductionConditionType.COLOR,
    )
    assert condition_set.color_rules == (
        rule,
    )


def test_set_supports_one_condition_group() -> None:
    condition_set = ReductionConditionSet(
        point_rule=create_point_rule()
    )

    assert condition_set.condition_count == 1
    assert condition_set.atomic_condition_count == 1


def test_set_supports_odds_condition() -> None:
    condition_set = ReductionConditionSet(
        odds_rule=create_odds_rule()
    )

    assert condition_set.condition_types == (
        ReductionConditionType.ODDS,
    )
    assert condition_set.atomic_condition_count == 1


def test_set_uses_and_logic() -> None:
    condition_set = create_condition_set()

    assert condition_set.is_approved(
        ReductionRow.from_symbols(
            "12X11111"
        )
    ) is True

    assert condition_set.is_approved(
        ReductionRow.from_symbols(
            "11211111"
        )
    ) is False


def test_set_rejects_invalid_row() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionRow",
    ):
        create_condition_set().is_approved(
            object()  # type: ignore[arg-type]
        )


def test_set_rejects_no_active_condition() -> None:
    with pytest.raises(
        ValueError,
        match="at least one",
    ):
        ReductionConditionSet()


def test_set_rejects_both_color_forms() -> None:
    single_rule = create_color_rule_set().rules[0]

    with pytest.raises(
        ValueError,
        match="not both",
    ):
        ReductionConditionSet(
            color_rule=single_rule,
            color_rule_set=create_color_rule_set(),
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "expected_message",
    ),
    (
        (
            "color_rule",
            "ColorReductionRule",
        ),
        (
            "color_rule_set",
            "ColorReductionRuleSet",
        ),
        (
            "one_x_two_rule",
            "OneXTwoReductionRule",
        ),
        (
            "point_rule",
            "PointReductionRule",
        ),
        (
            "odds_rule",
            "OddsReductionRule",
        ),
    ),
)
def test_set_rejects_invalid_rule_types(
    field_name: str,
    expected_message: str,
) -> None:
    with pytest.raises(
        TypeError,
        match=expected_message,
    ):
        ReductionConditionSet(
            **{
                field_name: object(),
            }
        )