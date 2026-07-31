"""Tests for transparent estimated-payout rules."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.outcome import Outcome
from src.models.payout_reduction_rule import (
    PayoutReductionRule,
    PayoutReductionSnapshot,
)
from src.models.reduction_row import ReductionRow
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from tests.payout_reduction_helpers import (
    create_snapshot,
)


def test_snapshot_normalizes_money_and_source() -> None:
    snapshot = create_snapshot()

    assert snapshot.turnover == Decimal("1000000.00")
    assert snapshot.top_prize_pool == Decimal("400000.00")
    assert snapshot.base_unit_stake == Decimal("1.00")
    assert snapshot.source == "Testpool"


def test_snapshot_exposes_version_and_pool_units() -> None:
    snapshot = create_snapshot()

    assert snapshot.method_version == "p13-public-share-v1"
    assert snapshot.match_count == 8
    assert snapshot.pool_units == Decimal("1000000")


def test_snapshot_returns_frozen_percentage() -> None:
    snapshot = create_snapshot()

    assert snapshot.percentage_for(
        1,
        Outcome.HOME,
    ) == Decimal("50")

    assert snapshot.percentage_for(
        2,
        Outcome.AWAY,
    ) == Decimal("15")


def test_snapshot_calculates_exact_row_share() -> None:
    snapshot = create_snapshot()
    row = ReductionRow.from_symbols(
        "11111111"
    )

    assert snapshot.row_share(
        row
    ) == Decimal("0.00375000")


def test_snapshot_calculates_expected_winning_units() -> None:
    snapshot = create_snapshot()
    row = ReductionRow.from_symbols(
        "11111111"
    )

    assert snapshot.expected_winning_units(
        row
    ) == Decimal("3750.00000000")


def test_snapshot_calculates_and_rounds_payout() -> None:
    snapshot = create_snapshot()
    row = ReductionRow.from_symbols(
        "11111111"
    )

    assert snapshot.estimated_payout(
        row
    ) == Decimal("106.67")


def test_snapshot_caps_payout_at_prize_pool() -> None:
    snapshot = replace(
        create_snapshot(),
        turnover="100",
    )
    row = ReductionRow.from_symbols(
        "22211111"
    )

    assert (
        snapshot.expected_winning_units(
            row
        )
        < Decimal("1")
    )
    assert snapshot.estimated_payout(
        row
    ) == Decimal("400000.00")


def test_snapshot_accepts_zero_selected_public_share() -> None:
    percentages = (
        ThreeWayPercentages("100", "0", "0"),
        *create_snapshot().match_percentages[1:],
    )
    snapshot = replace(
        create_snapshot(),
        match_percentages=percentages,
    )
    row = ReductionRow.from_symbols(
        "21111111"
    )

    assert snapshot.row_share(
        row
    ) == Decimal("0")
    assert snapshot.estimated_payout(
        row
    ) == snapshot.top_prize_pool


def test_snapshot_is_immutable() -> None:
    snapshot = create_snapshot()

    with pytest.raises(FrozenInstanceError):
        snapshot.turnover = Decimal("1")  # type: ignore[misc]


def test_snapshot_rejects_naive_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        replace(
            create_snapshot(),
            captured_at=datetime(
                2026,
                7,
                31,
                18,
                0,
            ),
        )


def test_snapshot_rejects_empty_match_percentages() -> None:
    with pytest.raises(
        ValueError,
        match="at least one match",
    ):
        replace(
            create_snapshot(),
            match_percentages=(),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "turnover",
        "top_prize_pool",
        "base_unit_stake",
    ),
)
def test_snapshot_rejects_nonpositive_money(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        replace(
            create_snapshot(),
            **{
                field_name: "0",
            },
        )


def test_snapshot_rejects_wrong_row_length() -> None:
    with pytest.raises(
        ValueError,
        match="same number of matches",
    ):
        create_snapshot().estimated_payout(
            ReductionRow.from_symbols(
                "111"
            )
        )


def test_rule_normalizes_interval_to_ore() -> None:
    rule = PayoutReductionRule(
        snapshot=create_snapshot(),
        min_estimated_payout="400.004",
        max_estimated_payout="800.005",
    )

    assert rule.min_estimated_payout == Decimal("400.00")
    assert rule.max_estimated_payout == Decimal("800.01")


def test_rule_uses_inclusive_boundaries() -> None:
    rule = PayoutReductionRule(
        snapshot=create_snapshot(),
        min_estimated_payout="400",
        max_estimated_payout="800",
    )

    assert rule.minimum_inclusive is True
    assert rule.maximum_inclusive is True
    assert rule.contains(
        Decimal("400")
    ) is True
    assert rule.contains(
        Decimal("800")
    ) is True
    assert rule.contains(
        Decimal("399.99")
    ) is False
    assert rule.contains(
        Decimal("800.01")
    ) is False


def test_rule_exposes_condition_text() -> None:
    rule = PayoutReductionRule(
        snapshot=create_snapshot(),
        min_estimated_payout="400",
        max_estimated_payout="800",
    )

    assert rule.condition_text == (
        "400.00 <= utdelning <= 800.00"
    )


def test_rule_evaluates_row() -> None:
    rule = PayoutReductionRule(
        snapshot=create_snapshot(),
        min_estimated_payout="100",
        max_estimated_payout="200",
    )

    row = ReductionRow.from_symbols(
        "11111111"
    )

    assert rule.estimated_payout(
        row
    ) == Decimal("106.67")
    assert rule.is_approved(
        row
    ) is True


def test_rule_rejects_invalid_interval() -> None:
    with pytest.raises(
        ValueError,
        match="greater than",
    ):
        PayoutReductionRule(
            snapshot=create_snapshot(),
            min_estimated_payout="800",
            max_estimated_payout="800",
        )


def test_snapshot_accepts_aware_non_utc_timestamp() -> None:
    snapshot = replace(
        create_snapshot(),
        captured_at=datetime.now().astimezone(),
    )

    assert snapshot.captured_at.utcoffset() is not None