"""Tests for the payout-reduction engine."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.payout_reduction_rule import (
    PayoutReductionRule,
    PayoutReductionSnapshot,
)
from src.models.reduction_frame import ReductionFrame
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.payout_reduction_engine import (
    PayoutReductionEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)
from tests.payout_reduction_helpers import (
    create_base_system,
    create_rule,
    create_snapshot,
)


def test_engine_applies_inclusive_interval() -> None:
    result = PayoutReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    assert result.approved_count == 11


def test_engine_preserves_base_row_order() -> None:
    base_system = create_base_system()

    result = PayoutReductionEngine().apply(
        base_system,
        create_rule(),
    )

    assert tuple(
        evaluation.row
        for evaluation in result.evaluations
    ) == base_system.rows


def test_engine_preserves_forecast_evidence() -> None:
    result = PayoutReductionEngine().apply(
        create_base_system(),
        create_rule(),
    )

    evaluation = result.evaluations[0]

    assert evaluation.row.symbols == "11111111"
    assert evaluation.row_share == Decimal("0.00375000")
    assert (
        evaluation.expected_winning_units
        == Decimal("3750.00000000")
    )
    assert evaluation.estimated_payout == Decimal("106.67")
    assert evaluation.is_approved is False


def test_engine_is_deterministic() -> None:
    base_system = create_base_system()
    rule = create_rule()
    engine = PayoutReductionEngine()

    assert engine.apply(
        base_system,
        rule,
    ) == engine.apply(
        base_system,
        rule,
    )


def test_engine_supports_thirteen_match_frame() -> None:
    frame = ReductionFrame(
        game_type=GameType.STRYKTIPSET,
        allowed_outcomes=(
            Outcome.ordered(),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
        ),
    )

    snapshot = PayoutReductionSnapshot(
        captured_at=create_snapshot().captured_at,
        match_percentages=tuple(
            ThreeWayPercentages("50", "30", "20")
            for _ in range(13)
        ),
        turnover="1000000",
        top_prize_pool="400000",
        source="13-match test",
    )

    rule = PayoutReductionRule(
        snapshot=snapshot,
        min_estimated_payout="0",
        max_estimated_payout="400000",
    )

    result = PayoutReductionEngine().apply(
        ReductionRowGenerator().generate(
            frame
        ),
        rule,
    )

    assert result.original_row_count == 3
    assert result.approved_count == 3


def test_engine_rejects_snapshot_match_count_mismatch() -> None:
    short_snapshot = replace(
        create_snapshot(),
        match_percentages=(
            create_snapshot().match_percentages[:-1]
        ),
    )
    rule = replace(
        create_rule(),
        snapshot=short_snapshot,
    )

    with pytest.raises(
        ValueError,
        match="exactly one complete",
    ):
        PayoutReductionEngine().apply(
            create_base_system(),
            rule,
        )


def test_engine_rejects_invalid_base_system() -> None:
    with pytest.raises(
        TypeError,
        match="BaseReductionSystem",
    ):
        PayoutReductionEngine().apply(
            object(),  # type: ignore[arg-type]
            create_rule(),
        )


def test_engine_rejects_invalid_rule() -> None:
    with pytest.raises(
        TypeError,
        match="PayoutReductionRule",
    ):
        PayoutReductionEngine().apply(
            create_base_system(),
            object(),  # type: ignore[arg-type]
        )