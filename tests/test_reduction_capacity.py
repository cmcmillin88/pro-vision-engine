"""Tests for reduction-frame capacity policy and assessment models."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

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


def create_capacity_frame() -> ReductionFrame:
    """Create a 72-row frame with all sign-count categories."""

    return ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            (Outcome.HOME,),
            (Outcome.DRAW,),
            (Outcome.AWAY,),
            (Outcome.HOME, Outcome.DRAW),
            (Outcome.HOME, Outcome.AWAY),
            (Outcome.DRAW, Outcome.AWAY),
            Outcome.ordered(),
            Outcome.ordered(),
        ),
        coupon_id="Kapacitetstest",
    )


def test_capacity_level_has_swedish_display_names() -> None:
    assert ReductionCapacityLevel.SAFE.display_name == "Säker"
    assert ReductionCapacityLevel.WARNING.display_name == "Varning"
    assert ReductionCapacityLevel.BLOCKED.display_name == "Blockerad"


def test_policy_uses_project_defaults() -> None:
    policy = ReductionCapacityPolicy()

    assert policy.warning_row_count == 25_000
    assert policy.maximum_materialized_rows == 100_000


def test_policy_summary_exposes_both_limits() -> None:
    summary = ReductionCapacityPolicy().summary_line

    assert "Varning från 25000" in summary
    assert "Max 100000 rader" in summary


@pytest.mark.parametrize(
    "field_name",
    (
        "warning_row_count",
        "maximum_materialized_rows",
    ),
)
@pytest.mark.parametrize(
    "invalid_value",
    (
        True,
        "100",
        Decimal("100"),
    ),
)
def test_policy_rejects_invalid_limit_types(
    field_name: str,
    invalid_value: object,
) -> None:
    values = {
        "warning_row_count": 25,
        "maximum_materialized_rows": 100,
    }
    values[field_name] = invalid_value

    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        ReductionCapacityPolicy(
            **values  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "warning_row_count",
        "maximum_materialized_rows",
    ),
)
@pytest.mark.parametrize(
    "invalid_value",
    (
        0,
        -1,
    ),
)
def test_policy_rejects_non_positive_limits(
    field_name: str,
    invalid_value: int,
) -> None:
    values = {
        "warning_row_count": 25,
        "maximum_materialized_rows": 100,
    }
    values[field_name] = invalid_value

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        ReductionCapacityPolicy(
            **values
        )


def test_policy_rejects_warning_above_hard_limit() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        ReductionCapacityPolicy(
            warning_row_count=101,
            maximum_materialized_rows=100,
        )


def test_policy_allows_warning_at_hard_limit() -> None:
    policy = ReductionCapacityPolicy(
        warning_row_count=100,
        maximum_materialized_rows=100,
    )

    assert policy.warning_row_count == 100


def test_assessment_exposes_exact_frame_size() -> None:
    assessment = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=100,
            maximum_materialized_rows=200,
        ),
    )

    assert assessment.expected_row_count == 72


def test_assessment_counts_singles_doubles_and_triples() -> None:
    assessment = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(),
    )

    assert assessment.single_count == 3
    assert assessment.double_count == 3
    assert assessment.triple_count == 2


@pytest.mark.parametrize(
    (
        "warning_rows",
        "maximum_rows",
        "expected_level",
    ),
    (
        (
            100,
            200,
            ReductionCapacityLevel.SAFE,
        ),
        (
            72,
            200,
            ReductionCapacityLevel.WARNING,
        ),
        (
            50,
            72,
            ReductionCapacityLevel.WARNING,
        ),
        (
            50,
            71,
            ReductionCapacityLevel.BLOCKED,
        ),
    ),
)
def test_assessment_resolves_capacity_level(
    warning_rows: int,
    maximum_rows: int,
    expected_level: ReductionCapacityLevel,
) -> None:
    assessment = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=warning_rows,
            maximum_materialized_rows=maximum_rows,
        ),
    )

    assert assessment.level is expected_level


def test_assessment_exposes_materialization_flags() -> None:
    warning = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=50,
            maximum_materialized_rows=100,
        ),
    )
    blocked = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=50,
            maximum_materialized_rows=71,
        ),
    )

    assert warning.can_materialize is True
    assert warning.requires_warning is True
    assert blocked.can_materialize is False
    assert blocked.requires_warning is False


def test_assessment_calculates_exact_utilization() -> None:
    assessment = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=50,
            maximum_materialized_rows=200,
        ),
    )

    assert assessment.utilization_percentage == Decimal("36.00")


def test_assessment_exposes_signed_row_margin() -> None:
    safe = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=50,
            maximum_materialized_rows=100,
        ),
    )
    blocked = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=50,
            maximum_materialized_rows=70,
        ),
    )

    assert safe.row_margin == 28
    assert blocked.row_margin == -2


def test_assessment_summary_contains_capacity_diagnostics() -> None:
    summary = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=50,
            maximum_materialized_rows=100,
        ),
    ).summary_line

    assert "Kapacitet Varning" in summary
    assert "Rader 72/100" in summary
    assert "Singlar 3" in summary
    assert "Halvor 3" in summary
    assert "Helor 2" in summary
    assert "Utnyttjande 72.00%" in summary


def test_assessment_allows_materializable_frame() -> None:
    assessment = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=50,
            maximum_materialized_rows=100,
        ),
    )

    assert assessment.require_materializable() is None


def test_assessment_raises_precise_error_for_blocked_frame() -> None:
    assessment = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=ReductionCapacityPolicy(
            warning_row_count=50,
            maximum_materialized_rows=71,
        ),
    )

    with pytest.raises(
        ReductionCapacityExceededError,
        match="72 rows.*limit of 71",
    ):
        assessment.require_materializable()


def test_assessment_rejects_invalid_dependencies() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionFrame",
    ):
        ReductionCapacityAssessment(
            frame=object(),  # type: ignore[arg-type]
            policy=ReductionCapacityPolicy(),
        )

    with pytest.raises(
        TypeError,
        match="ReductionCapacityPolicy",
    ):
        ReductionCapacityAssessment(
            frame=create_capacity_frame(),
            policy=object(),  # type: ignore[arg-type]
        )


def test_capacity_models_are_immutable() -> None:
    policy = ReductionCapacityPolicy()
    assessment = ReductionCapacityAssessment(
        frame=create_capacity_frame(),
        policy=policy,
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        policy.warning_row_count = 1  # type: ignore[misc]

    with pytest.raises(
        FrozenInstanceError,
    ):
        assessment.policy = policy  # type: ignore[misc]