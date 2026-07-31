"""Tests for deterministic total-odds reduction results."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.models.odds_reduction_result import (
    OddsReductionRowEvaluation,
)
from tests.odds_reduction_helpers import (
    create_result,
)


def test_row_evaluation_rejects_non_decimal_odds() -> None:
    result = create_result()

    with pytest.raises(
        TypeError,
        match="Decimal",
    ):
        OddsReductionRowEvaluation(
            row=result.base_system.rows[0],
            total_odds=192,  # type: ignore[arg-type]
            is_approved=False,
        )


def test_result_exposes_counts() -> None:
    result = create_result()

    assert result.original_row_count == 27
    assert result.approved_count == 13
    assert result.rejected_count == 14


def test_result_preserves_surviving_row_order() -> None:
    result = create_result()

    assert tuple(
        row.symbols
        for row in result.approved_rows
    ) == (
        "1XX11111",
        "1X211111",
        "12111111",
        "12X11111",
        "X1211111",
        "XXX11111",
        "XX211111",
        "X2111111",
        "21X11111",
        "21211111",
        "2X111111",
        "2XX11111",
        "22111111",
    )


def test_result_exposes_percentages() -> None:
    result = create_result()

    assert result.retained_percentage == Decimal(
        "48.15"
    )
    assert result.reduction_percentage == Decimal(
        "51.85"
    )
    assert result.is_empty is False


def test_result_exposes_observed_range() -> None:
    result = create_result()

    assert result.minimum_observed_odds == Decimal(
        "192.0000000"
    )
    assert result.maximum_observed_odds == Decimal(
        "3840.0000000"
    )


def test_result_exposes_exact_distribution() -> None:
    result = create_result()

    assert result.total_odds_distribution[0] == (
        Decimal("192.0000000"),
        1,
    )
    assert result.total_odds_distribution[-1] == (
        Decimal("3840.0000000"),
        1,
    )


def test_result_counts_one_exact_total() -> None:
    assert create_result().row_count_for_total_odds(
        Decimal("768")
    ) == 4


def test_result_returns_one_based_evaluation() -> None:
    result = create_result()

    assert result.evaluation_at(
        1
    ).row == result.base_system.rows[0]


def test_result_exposes_summary_line() -> None:
    assert create_result().summary_line == (
        "Odds MIN 700.00 | MAX < 1600.00 | "
        "Ursprung 27 | Kvar 13 | Bort 14 | "
        "Reducering 51.85%"
    )


def test_result_rejects_wrong_evaluation_count() -> None:
    result = create_result()

    with pytest.raises(
        ValueError,
        match="one entry",
    ):
        replace(
            result,
            evaluations=result.evaluations[:-1],
        )


def test_result_rejects_changed_row_order() -> None:
    result = create_result()

    with pytest.raises(
        ValueError,
        match="row order",
    ):
        replace(
            result,
            evaluations=tuple(
                reversed(
                    result.evaluations
                )
            ),
        )


def test_result_rejects_changed_total_odds() -> None:
    result = create_result()
    first = result.evaluations[0]

    changed = replace(
        first,
        total_odds=first.total_odds
        + Decimal("1"),
    )

    with pytest.raises(
        ValueError,
        match="total_odds",
    ):
        replace(
            result,
            evaluations=(
                changed,
                *result.evaluations[1:],
            ),
        )


def test_result_rejects_changed_approval() -> None:
    result = create_result()
    first = result.evaluations[0]

    changed = replace(
        first,
        is_approved=not first.is_approved,
    )

    with pytest.raises(
        ValueError,
        match="approval",
    ):
        replace(
            result,
            evaluations=(
                changed,
                *result.evaluations[1:],
            ),
        )