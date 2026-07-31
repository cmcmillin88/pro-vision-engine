"""Tests for deterministic total-odds reduction rules."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.odds_reduction_rule import (
    OddsReductionRule,
    OddsReductionSnapshot,
)
from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow
from src.models.three_way_odds import ThreeWayOdds
from tests.odds_reduction_helpers import (
    create_rule,
    create_snapshot,
)


def test_snapshot_normalizes_source() -> None:
    snapshot = create_snapshot()

    assert snapshot.source == "Testmarknad"
    assert snapshot.match_count == 8


def test_snapshot_rejects_naive_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        OddsReductionSnapshot(
            captured_at=datetime(2026, 7, 31, 18, 0),
            match_odds=(
                ThreeWayOdds("2", "3", "4"),
            ),
        )


def test_snapshot_rejects_empty_match_odds() -> None:
    with pytest.raises(
        ValueError,
        match="at least one",
    ):
        OddsReductionSnapshot(
            captured_at=datetime.now(
                timezone.utc
            ),
            match_odds=(),
        )


def test_snapshot_rejects_invalid_odds_type() -> None:
    with pytest.raises(
        TypeError,
        match="ThreeWayOdds",
    ):
        OddsReductionSnapshot(
            captured_at=datetime.now(
                timezone.utc
            ),
            match_odds=(
                object(),  # type: ignore[arg-type]
            ),
        )


def test_snapshot_returns_one_cell_odds() -> None:
    snapshot = create_snapshot()

    assert snapshot.odds_for(
        2,
        Outcome.AWAY,
    ) == Decimal("6.00")


def test_snapshot_rejects_invalid_match_number_type() -> None:
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        create_snapshot().odds_for(
            True,  # type: ignore[arg-type]
            Outcome.HOME,
        )


def test_snapshot_rejects_match_outside_snapshot() -> None:
    with pytest.raises(
        IndexError,
        match="outside",
    ):
        create_snapshot().odds_for(
            9,
            Outcome.HOME,
        )


def test_snapshot_multiplies_without_intermediate_rounding() -> None:
    snapshot = OddsReductionSnapshot(
        captured_at=datetime.now(
            timezone.utc
        ),
        match_odds=(
            ThreeWayOdds(
                "1.12345678901234567890",
                "2",
                "3",
            ),
            ThreeWayOdds(
                "1.98765432109876543210",
                "2",
                "3",
            ),
        ),
    )

    row = ReductionRow.from_symbols(
        "11"
    )

    assert snapshot.total_odds(row) == Decimal(
        "2.2330437412481329062237463801111263526900"
    )


def test_snapshot_rejects_wrong_row_length() -> None:
    with pytest.raises(
        ValueError,
        match="same number",
    ):
        create_snapshot().total_odds(
            ReductionRow.from_symbols(
                "1111111"
            )
        )


def test_rule_normalizes_numeric_bounds() -> None:
    rule = create_rule(
        minimum="700.0",
        maximum=1600,
    )

    assert rule.min_total_odds == Decimal("700.0")
    assert rule.max_total_odds == Decimal("1600")


def test_rule_exposes_boundary_policy() -> None:
    rule = create_rule()

    assert rule.minimum_inclusive is True
    assert rule.maximum_inclusive is False


def test_rule_exposes_condition_text() -> None:
    assert create_rule().condition_text == (
        "700.00 <= odds < 1600.00"
    )


def test_rule_includes_exact_minimum() -> None:
    assert create_rule().contains(
        Decimal("700")
    ) is True


def test_rule_excludes_exact_maximum() -> None:
    assert create_rule().contains(
        Decimal("1600")
    ) is False


def test_rule_rejects_below_minimum() -> None:
    assert create_rule().contains(
        Decimal("699.99")
    ) is False


def test_rule_rejects_invalid_total_odds() -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        create_rule().contains(
            Decimal("0")
        )


def test_rule_rejects_invalid_interval() -> None:
    with pytest.raises(
        ValueError,
        match="greater than",
    ):
        OddsReductionRule(
            snapshot=create_snapshot(),
            min_total_odds="1000",
            max_total_odds="1000",
        )


def test_rule_rejects_minimum_below_one() -> None:
    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        OddsReductionRule(
            snapshot=create_snapshot(),
            min_total_odds="0.99",
            max_total_odds="10",
        )