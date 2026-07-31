"""Tests for the deterministic total-odds reduction engine."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.models.game_type import GameType
from src.models.odds_reduction_rule import (
    OddsReductionRule,
    OddsReductionSnapshot,
)
from src.models.outcome import Outcome
from src.models.reduction_frame import ReductionFrame
from src.models.reduction_row import ReductionRow
from src.models.three_way_odds import ThreeWayOdds
from src.services.odds_reduction_engine import (
    OddsReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)
from tests.odds_reduction_helpers import (
    create_base_system,
    create_rule,
    create_snapshot,
)


def test_engine_applies_standard_interval() -> None:
    result = OddsReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    assert result.approved_count == 13
    assert result.rejected_count == 14


def test_engine_preserves_exact_row_totals() -> None:
    result = OddsReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    assert result.evaluations[0].total_odds == Decimal(
        "192.0000000"
    )
    assert result.evaluations[-1].total_odds == Decimal(
        "3840.0000000"
    )


def test_engine_supports_empty_result() -> None:
    result = OddsReductionEngine().apply(
        create_base_system(),
        create_rule(
            minimum="5000",
            maximum="6000",
        ),
    )

    assert result.approved_count == 0
    assert result.is_empty is True


def test_engine_is_deterministic() -> None:
    base_system = create_base_system()
    rule = create_rule()
    engine = OddsReductionEngine()

    assert engine.apply(
        base_system,
        rule,
    ) == engine.apply(
        base_system,
        rule,
    )


def test_engine_rejects_invalid_base_system() -> None:
    with pytest.raises(
        TypeError,
        match="BaseReductionSystem",
    ):
        OddsReductionEngine().apply(
            object(),  # type: ignore[arg-type]
            create_rule(),
        )


def test_engine_rejects_invalid_rule() -> None:
    with pytest.raises(
        TypeError,
        match="OddsReductionRule",
    ):
        OddsReductionEngine().apply(
            create_base_system(),
            object(),  # type: ignore[arg-type]
        )


def test_engine_rejects_snapshot_count_mismatch() -> None:
    short_snapshot = replace(
        create_snapshot(),
        match_odds=create_snapshot().match_odds[:-1],
    )
    rule = OddsReductionRule(
        snapshot=short_snapshot,
        min_total_odds="1",
        max_total_odds="10000",
    )

    with pytest.raises(
        ValueError,
        match="exactly one complete",
    ):
        OddsReductionEngine().apply(
            create_base_system(),
            rule,
        )


def test_frozen_snapshot_does_not_change_after_creation() -> None:
    snapshot = create_snapshot()
    rule = OddsReductionRule(
        snapshot=snapshot,
        min_total_odds="700",
        max_total_odds="1600",
    )
    row = ReductionRow.from_symbols(
        "12X11111"
    )

    first_total = rule.total_odds(
        row
    )

    replacement_snapshot = replace(
        snapshot,
        match_odds=(
            ThreeWayOdds("9", "9", "9"),
            *snapshot.match_odds[1:],
        ),
    )

    assert replacement_snapshot != snapshot
    assert rule.total_odds(row) == first_total


def test_engine_keeps_exact_lower_boundary() -> None:
    result = OddsReductionEngine().apply(
        create_base_system(),
        create_rule(
            minimum="768",
            maximum="769",
        ),
    )

    assert result.approved_count == 4


def test_engine_removes_exact_upper_boundary() -> None:
    result = OddsReductionEngine().apply(
        create_base_system(),
        create_rule(
            minimum="700",
            maximum="768",
        ),
    )

    assert all(
        evaluation.total_odds
        < Decimal("768")
        for evaluation in result.approved_evaluations
    )
    assert result.approved_count == 1


def test_spiked_matches_are_included_in_total_odds() -> None:
    snapshot = OddsReductionSnapshot(
        captured_at=create_snapshot().captured_at,
        match_odds=(
            ThreeWayOdds("2", "3", "4"),
            ThreeWayOdds("2", "3", "4"),
            ThreeWayOdds("2", "3", "4"),
            ThreeWayOdds("5", "6", "7"),
            ThreeWayOdds("2", "2", "2"),
            ThreeWayOdds("2", "2", "2"),
            ThreeWayOdds("2", "2", "2"),
            ThreeWayOdds("2", "2", "2"),
        ),
    )
    rule = OddsReductionRule(
        snapshot=snapshot,
        min_total_odds="1",
        max_total_odds="100000",
    )

    row = ReductionRow.from_symbols(
        "11111111"
    )

    assert rule.total_odds(row) == Decimal(
        "640"
    )


def test_engine_works_for_thirteen_match_frame() -> None:
    frame = ReductionFrame(
        game_type=GameType.STRYKTIPSET,
        allowed_outcomes=tuple(
            (Outcome.HOME,)
            for _ in range(13)
        ),
    )
    snapshot = OddsReductionSnapshot(
        captured_at=create_snapshot().captured_at,
        match_odds=tuple(
            ThreeWayOdds("2", "3", "4")
            for _ in range(13)
        ),
    )
    rule = OddsReductionRule(
        snapshot=snapshot,
        min_total_odds="8000",
        max_total_odds="9000",
    )

    result = OddsReductionEngine().apply(
        ReductionRowGenerator().generate(frame),
        rule,
    )

    assert result.approved_count == 1
    assert result.approved_rows[0].symbols == (
        "1" * 13
    )