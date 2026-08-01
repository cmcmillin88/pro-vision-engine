"""Tests for exact reduction-frame capacity planning."""

import pytest

from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.reduction_capacity import (
    ReductionCapacityAssessment,
    ReductionCapacityExceededError,
    ReductionCapacityLevel,
    ReductionCapacityPolicy,
)
from src.models.reduction_frame import ReductionFrame
from src.services.reduction_capacity_planner import (
    ReductionCapacityPlanner,
)


def create_four_row_frame() -> ReductionFrame:
    """Create one deterministic four-row frame."""

    return ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            (Outcome.HOME, Outcome.DRAW),
            (Outcome.HOME, Outcome.AWAY),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
        ),
    )


def test_planner_uses_default_policy() -> None:
    planner = ReductionCapacityPlanner()

    assert planner.policy == ReductionCapacityPolicy()


def test_planner_preserves_explicit_policy() -> None:
    policy = ReductionCapacityPolicy(
        warning_row_count=3,
        maximum_materialized_rows=5,
    )
    planner = ReductionCapacityPlanner(
        policy
    )

    assert planner.policy is policy


def test_planner_rejects_invalid_policy() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionCapacityPolicy",
    ):
        ReductionCapacityPlanner(
            object()  # type: ignore[arg-type]
        )


def test_planner_creates_exact_assessment() -> None:
    planner = ReductionCapacityPlanner(
        ReductionCapacityPolicy(
            warning_row_count=3,
            maximum_materialized_rows=5,
        )
    )

    assessment = planner.assess(
        create_four_row_frame()
    )

    assert isinstance(
        assessment,
        ReductionCapacityAssessment,
    )
    assert assessment.expected_row_count == 4
    assert assessment.level is ReductionCapacityLevel.WARNING


def test_planner_rejects_invalid_frame() -> None:
    with pytest.raises(
        TypeError,
        match="requires a ReductionFrame",
    ):
        ReductionCapacityPlanner().assess(
            object()  # type: ignore[arg-type]
        )


def test_planner_returns_materializable_assessment() -> None:
    planner = ReductionCapacityPlanner(
        ReductionCapacityPolicy(
            warning_row_count=3,
            maximum_materialized_rows=4,
        )
    )

    assessment = planner.require_materializable(
        create_four_row_frame()
    )

    assert assessment.level is ReductionCapacityLevel.WARNING
    assert assessment.can_materialize is True


def test_planner_blocks_frame_above_limit() -> None:
    planner = ReductionCapacityPlanner(
        ReductionCapacityPolicy(
            warning_row_count=2,
            maximum_materialized_rows=3,
        )
    )

    with pytest.raises(
        ReductionCapacityExceededError,
        match="exceeds the configured",
    ):
        planner.require_materializable(
            create_four_row_frame()
        )


def test_planner_is_deterministic() -> None:
    planner = ReductionCapacityPlanner(
        ReductionCapacityPolicy(
            warning_row_count=3,
            maximum_materialized_rows=5,
        )
    )
    frame = create_four_row_frame()

    assert planner.assess(
        frame
    ) == planner.assess(
        frame
    )