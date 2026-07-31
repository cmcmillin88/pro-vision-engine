"""Tests for payout-reduction result models."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.models.payout_reduction_result import (
    PayoutReductionRowEvaluation,
)
from tests.payout_reduction_helpers import (
    create_result,
)


def test_result_exposes_row_counts() -> None:
    result = create_result()

    assert result.original_row_count == 27
    assert result.approved_count == 11
    assert result.rejected_count == 16


def test_result_exposes_surviving_rows_in_order() -> None:
    result = create_result()

    assert tuple(
        row.symbols
        for row in result.approved_rows
    ) == (
        "1X211111",
        "12111111",
        "12X11111",
        "12211111",
        "XX111111",
        "XXX11111",
        "XX211111",
        "X2111111",
        "21211111",
        "2X111111",
        "2XX11111",
    )


def test_result_exposes_percentages() -> None:
    result = create_result()

    assert result.retained_percentage == Decimal("40.74")
    assert result.reduction_percentage == Decimal("59.26")
    assert result.is_empty is False


def test_result_exposes_observed_range() -> None:
    result = create_result()

    assert result.minimum_observed_payout == Decimal("106.67")
    assert result.maximum_observed_payout == Decimal("1706.67")


def test_result_exposes_payout_distribution() -> None:
    result = create_result()

    assert result.estimated_payout_distribution[0] == (
        Decimal("106.67"),
        1,
    )
    assert result.estimated_payout_distribution[-1] == (
        Decimal("1706.67"),
        1,
    )
    assert result.row_count_for_estimated_payout(
        Decimal("426.67")
    ) == 3


def test_result_exposes_one_based_evaluation() -> None:
    result = create_result()

    assert result.evaluation_at(
        1
    ).row == result.base_system.rows[0]


def test_result_exposes_summary_line() -> None:
    assert create_result().summary_line == (
        "Utdelning MIN 400.00 | MAX 800.00 | "
        "Ursprung 27 | Kvar 11 | Bort 16 | "
        "Reducering 59.26%"
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


def test_result_rejects_inconsistent_payout() -> None:
    result = create_result()
    first = result.evaluations[0]

    changed_first = replace(
        first,
        estimated_payout=Decimal("999.99"),
    )

    with pytest.raises(
        ValueError,
        match="estimated_payout",
    ):
        replace(
            result,
            evaluations=(
                changed_first,
                *result.evaluations[1:],
            ),
        )


def test_row_evaluation_rejects_share_above_one() -> None:
    result = create_result()
    first = result.evaluations[0]

    with pytest.raises(
        ValueError,
        match="must not exceed 1",
    ):
        PayoutReductionRowEvaluation(
            row=first.row,
            row_share=Decimal("1.01"),
            expected_winning_units=Decimal("1"),
            estimated_payout=Decimal("1"),
            is_approved=True,
        )


def test_result_rejects_invalid_lookup_type() -> None:
    with pytest.raises(
        TypeError,
        match="Decimal",
    ):
        create_result().row_count_for_estimated_payout(
            400  # type: ignore[arg-type]
        )