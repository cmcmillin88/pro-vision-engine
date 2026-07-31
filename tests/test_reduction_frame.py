"""Tests for reduction frames and complete base systems."""

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
from src.models.reduction_row import ReductionRow


def create_frame() -> ReductionFrame:
    """Create one compact four-row Topptipset frame."""

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
        coupon_id="Topptipset test",
    )


def create_rows() -> tuple[ReductionRow, ...]:
    """Create all rows belonging to the compact frame."""

    return (
        ReductionRow.from_symbols(
            "11111111"
        ),
        ReductionRow.from_symbols(
            "11211111"
        ),
        ReductionRow.from_symbols(
            "1X111111"
        ),
        ReductionRow.from_symbols(
            "1X211111"
        ),
    )


def test_frame_exposes_expected_properties() -> None:
    frame = create_frame()

    assert frame.game_type is GameType.TOPPTIPSET
    assert frame.match_count == 8
    assert frame.expected_row_count == 4
    assert (
        frame.recommendation_pattern
        == "1|1X|12|1|1|1|1|1"
    )


def test_frame_supports_match_lookup() -> None:
    frame = create_frame()

    assert frame.allowed_for_match(
        2
    ) == (
        Outcome.HOME,
        Outcome.DRAW,
    )
    assert frame.sign_count_for_match(
        2
    ) == 2
    assert frame.sign_count_for_match(
        4
    ) == 1


def test_frame_identifies_valid_and_invalid_rows() -> None:
    frame = create_frame()

    assert frame.contains(
        ReductionRow.from_symbols(
            "1X211111"
        )
    ) is True

    assert frame.contains(
        ReductionRow.from_symbols(
            "21111111"
        )
    ) is False


def test_frame_normalizes_coupon_id() -> None:
    frame = ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            (
                Outcome.HOME,
            ),
        ) * 8,
        coupon_id="  Topptipset   vecka  1  ",
    )

    assert frame.coupon_id == "Topptipset vecka 1"


def test_frame_can_be_created_from_coupon_analysis() -> None:
    coupon_analysis = Mock(
        spec=FinalCouponAnalysisReport
    )
    coupon_analysis.game_type = GameType.TOPPTIPSET
    coupon_analysis.coupon_id = "Coupon 1"
    coupon_analysis.match_reports = tuple(
        SimpleNamespace(
            recommended_outcomes=(
                Outcome.HOME,
                Outcome.AWAY,
            )
        )
        for _ in range(
            8
        )
    )

    frame = ReductionFrame.from_coupon_analysis(
        coupon_analysis
    )

    assert frame.expected_row_count == 256
    assert (
        frame.recommendation_pattern
        == "12|12|12|12|12|12|12|12"
    )


def test_frame_rejects_unknown_game_type() -> None:
    with pytest.raises(
        ValueError,
        match="supported game type",
    ):
        ReductionFrame(
            game_type=GameType.UNKNOWN,
            allowed_outcomes=(),
        )


def test_frame_rejects_wrong_match_count() -> None:
    with pytest.raises(
        ValueError,
        match="exactly 8 frame positions",
    ):
        ReductionFrame(
            game_type=GameType.TOPPTIPSET,
            allowed_outcomes=(
                (
                    Outcome.HOME,
                ),
            ) * 7,
        )


def test_frame_rejects_empty_position() -> None:
    positions = [
        (
            Outcome.HOME,
        )
        for _ in range(
            8
        )
    ]
    positions[3] = ()

    with pytest.raises(
        ValueError,
        match="at least one outcome",
    ):
        ReductionFrame(
            game_type=GameType.TOPPTIPSET,
            allowed_outcomes=tuple(
                positions
            ),
        )


def test_frame_rejects_unordered_position() -> None:
    positions = [
        (
            Outcome.HOME,
        )
        for _ in range(
            8
        )
    ]
    positions[2] = (
        Outcome.DRAW,
        Outcome.HOME,
    )

    with pytest.raises(
        ValueError,
        match="official 1-X-2 order",
    ):
        ReductionFrame(
            game_type=GameType.TOPPTIPSET,
            allowed_outcomes=tuple(
                positions
            ),
        )


def test_frame_rejects_duplicate_outcome() -> None:
    positions = [
        (
            Outcome.HOME,
        )
        for _ in range(
            8
        )
    ]
    positions[2] = (
        Outcome.HOME,
        Outcome.HOME,
    )

    with pytest.raises(
        ValueError,
        match="duplicate outcomes",
    ):
        ReductionFrame(
            game_type=GameType.TOPPTIPSET,
            allowed_outcomes=tuple(
                positions
            ),
        )


def test_frame_rejects_invalid_outcome_item() -> None:
    positions: list[tuple[object, ...]] = [
        (
            Outcome.HOME,
        )
        for _ in range(
            8
        )
    ]
    positions[2] = (
        object(),
    )

    with pytest.raises(
        TypeError,
        match="Outcome values",
    ):
        ReductionFrame(
            game_type=GameType.TOPPTIPSET,
            allowed_outcomes=tuple(  # type: ignore[arg-type]
                positions
            ),
        )


def test_base_system_exposes_expected_helpers() -> None:
    system = BaseReductionSystem(
        frame=create_frame(),
        rows=create_rows(),
    )

    assert system.row_count == 4
    assert system.is_complete_frame is True
    assert system.first_row.symbols == "11111111"
    assert system.last_row.symbols == "1X211111"
    assert system.row_at(
        2
    ).symbols == "11211111"
    assert system.contains(
        ReductionRow.from_symbols(
            "1X111111"
        )
    ) is True


def test_base_system_rejects_missing_row() -> None:
    with pytest.raises(
        ValueError,
        match="expected number of rows",
    ):
        BaseReductionSystem(
            frame=create_frame(),
            rows=create_rows()[:-1],
        )


def test_base_system_rejects_duplicate_row() -> None:
    rows = list(
        create_rows()
    )
    rows[3] = rows[0]

    with pytest.raises(
        ValueError,
        match="duplicate rows",
    ):
        BaseReductionSystem(
            frame=create_frame(),
            rows=tuple(
                rows
            ),
        )


def test_base_system_rejects_row_outside_frame() -> None:
    rows = list(
        create_rows()
    )
    rows[3] = ReductionRow.from_symbols(
        "21111111"
    )

    with pytest.raises(
        ValueError,
        match="belong to the frame",
    ):
        BaseReductionSystem(
            frame=create_frame(),
            rows=tuple(
                rows
            ),
        )


def test_base_system_rejects_invalid_row_item() -> None:
    rows: list[object] = list(
        create_rows()
    )
    rows[0] = object()

    with pytest.raises(
        TypeError,
        match="ReductionRow objects",
    ):
        BaseReductionSystem(
            frame=create_frame(),
            rows=tuple(rows),  # type: ignore[arg-type]
        )