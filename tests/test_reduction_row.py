"""Tests for individual mathematical reduction rows."""

from dataclasses import FrozenInstanceError

import pytest

from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow


def test_row_exposes_symbols_and_match_count() -> None:
    row = ReductionRow(
        outcomes=(
            Outcome.HOME,
            Outcome.DRAW,
            Outcome.AWAY,
        )
    )

    assert row.match_count == 3
    assert row.symbols == "1X2"
    assert str(row) == "1X2"


def test_row_can_be_created_from_symbols() -> None:
    row = ReductionRow.from_symbols(
        " 1 X 2 "
    )

    assert row.outcomes == (
        Outcome.HOME,
        Outcome.DRAW,
        Outcome.AWAY,
    )


def test_row_supports_count_and_lookup() -> None:
    row = ReductionRow.from_symbols(
        "11XX22"
    )

    assert row.outcome_at(1) is Outcome.HOME
    assert row.outcome_at(4) is Outcome.DRAW
    assert row.outcome_at(6) is Outcome.AWAY
    assert row.count(Outcome.HOME) == 2
    assert row.count("X") == 2
    assert row.count(Outcome.AWAY) == 2


def test_row_calculates_hamming_distance() -> None:
    first = ReductionRow.from_symbols(
        "1X21"
    )
    second = ReductionRow.from_symbols(
        "1121"
    )

    assert first.hamming_distance(
        second
    ) == 1


def test_row_rejects_non_tuple_outcomes() -> None:
    with pytest.raises(
        TypeError,
        match="must be a tuple",
    ):
        ReductionRow(
            outcomes=[  # type: ignore[arg-type]
                Outcome.HOME
            ]
        )


def test_row_rejects_empty_outcomes() -> None:
    with pytest.raises(
        ValueError,
        match="at least one outcome",
    ):
        ReductionRow(
            outcomes=()
        )


def test_row_rejects_invalid_outcome_item() -> None:
    with pytest.raises(
        TypeError,
        match="Outcome values",
    ):
        ReductionRow(
            outcomes=(
                object(),  # type: ignore[arg-type]
            )
        )


def test_row_rejects_invalid_match_number() -> None:
    row = ReductionRow.from_symbols(
        "1X2"
    )

    with pytest.raises(
        IndexError,
        match="outside the row",
    ):
        row.outcome_at(
            4
        )


def test_row_rejects_distance_to_other_length() -> None:
    first = ReductionRow.from_symbols(
        "1X2"
    )
    second = ReductionRow.from_symbols(
        "1X"
    )

    with pytest.raises(
        ValueError,
        match="same number",
    ):
        first.hamming_distance(
            second
        )


def test_row_is_immutable() -> None:
    row = ReductionRow.from_symbols(
        "1X2"
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        row.outcomes = (Outcome.HOME,)  # type: ignore[misc]