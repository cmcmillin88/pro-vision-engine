"""Tests for deterministic mathematical row generation."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.models.final_coupon_analysis import (
    FinalCouponAnalysisReport,
)
from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.reduction_frame import (
    BaseReductionSystem,
    ReductionFrame,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


def create_frame() -> ReductionFrame:
    """Create one compact four-row frame."""

    return ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
                Outcome.DRAW,
            ),
            (
                Outcome.HOME,
                Outcome.AWAY,
            ),
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
            ),
            (
                Outcome.HOME,
            ),
        ),
    )


def test_generator_builds_complete_four_row_system() -> None:
    system = ReductionRowGenerator().generate(
        create_frame()
    )

    assert isinstance(
        system,
        BaseReductionSystem,
    )
    assert system.row_count == 4
    assert system.is_complete_frame is True


def test_generator_uses_deterministic_cartesian_order() -> None:
    system = ReductionRowGenerator().generate(
        create_frame()
    )

    assert tuple(
        row.symbols
        for row in system.rows
    ) == (
        "11111111",
        "11211111",
        "1X111111",
        "1X211111",
    )


def test_generator_builds_256_rows_for_eight_doubles() -> None:
    frame = ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            (
                Outcome.HOME,
                Outcome.AWAY,
            ),
        ) * 8,
    )

    system = ReductionRowGenerator().generate(
        frame
    )

    assert system.row_count == 256
    assert system.first_row.symbols == "11111111"
    assert system.last_row.symbols == "22222222"


def test_lazy_iteration_is_not_blocked_by_materialization_limit() -> None:
    generator = ReductionRowGenerator(
        maximum_materialized_rows=1
    )

    rows = tuple(
        generator.iter_rows(
            create_frame()
        )
    )

    assert len(
        rows
    ) == 4


def test_generator_enforces_materialization_limit() -> None:
    generator = ReductionRowGenerator(
        maximum_materialized_rows=3
    )

    with pytest.raises(
        ValueError,
        match="exceeds the configured",
    ):
        generator.generate(
            create_frame()
        )


def test_generator_rejects_invalid_limit_type() -> None:
    with pytest.raises(
        TypeError,
        match="must be an integer",
    ):
        ReductionRowGenerator(
            maximum_materialized_rows=True
        )


def test_generator_rejects_non_positive_limit() -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        ReductionRowGenerator(
            maximum_materialized_rows=0
        )


def test_generator_rejects_invalid_frame() -> None:
    generator = ReductionRowGenerator()

    with pytest.raises(
        TypeError,
        match="requires a ReductionFrame",
    ):
        generator.iter_rows(
            object()  # type: ignore[arg-type]
        )


def test_generator_builds_frame_from_coupon_analysis() -> None:
    coupon_analysis = Mock(
        spec=FinalCouponAnalysisReport
    )
    coupon_analysis.game_type = GameType.TOPPTIPSET
    coupon_analysis.coupon_id = "Topptipset demo"
    coupon_analysis.match_reports = (
        SimpleNamespace(
            recommended_outcomes=(
                Outcome.HOME,
            )
        ),
        *(
            SimpleNamespace(
                recommended_outcomes=(
                    Outcome.HOME,
                    Outcome.AWAY,
                )
            )
            for _ in range(
                7
            )
        ),
    )

    system = (
        ReductionRowGenerator()
        .generate_from_coupon_analysis(
            coupon_analysis
        )
    )

    assert system.frame.coupon_id == "Topptipset demo"
    assert system.row_count == 128
    assert (
        system.frame.recommendation_pattern
        == "1|12|12|12|12|12|12|12"
    )


def test_generator_is_deterministic() -> None:
    generator = ReductionRowGenerator()
    frame = create_frame()

    first_system = generator.generate(
        frame
    )
    second_system = generator.generate(
        frame
    )

    assert first_system == second_system