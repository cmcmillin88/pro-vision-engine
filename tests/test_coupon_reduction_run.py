"""Tests for the complete practical coupon-reduction result model."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.models.coupon_reduction_run import CouponReductionRun
from tests.coupon_reduction_run_helpers import (
    FIXED_ANALYZED_AT,
    FIXED_REDUCED_AT,
    create_reduction_run,
)


def test_run_uses_versioned_result_contract() -> None:
    run = create_reduction_run()

    assert run.schema_version == "p13-reduction-result-v1"


def test_run_links_analysis_configuration_and_report() -> None:
    run = create_reduction_run()

    assert run.configuration.analysis_run == run.analysis_run
    assert run.reduction_report.base_system == run.analysis_run.base_system
    assert run.reduction_report.condition_set == run.configuration.condition_set


def test_run_exposes_coupon_and_condition_metadata() -> None:
    run = create_reduction_run()

    assert run.coupon_id == "TT-EXEMPEL-2026-08-01"
    assert run.match_count == 8
    assert run.condition_count == 3
    assert run.atomic_condition_count == 5


def test_run_exposes_deterministic_row_counts() -> None:
    run = create_reduction_run()

    assert run.original_row_count == run.analysis_run.base_row_count
    assert run.approved_row_count + run.rejected_row_count == (
        run.original_row_count
    )


def test_run_exposes_exact_costs() -> None:
    run = create_reduction_run()

    assert run.row_price == Decimal("1.00")
    assert run.original_cost == Decimal(run.original_row_count)
    assert run.final_cost == Decimal(run.approved_row_count)
    assert run.saved_cost == run.original_cost - run.final_cost


def test_run_exposes_surviving_rows_in_report_order() -> None:
    run = create_reduction_run()

    assert run.approved_rows == run.reduction_report.approved_rows
    assert run.approved_symbols == run.reduction_report.approved_symbols


def test_run_summary_contains_practical_result() -> None:
    summary = create_reduction_run().summary_line

    assert "Topptipset" in summary
    assert "Villkor 3" in summary
    assert "Ursprung" in summary
    assert "Kvar" in summary
    assert "p13-reduction-result-v1" in summary


def test_run_rejects_unsupported_schema_version() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        replace(
            create_reduction_run(),
            schema_version="p13-reduction-result-v999",
        )


def test_run_rejects_naive_reduction_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        replace(
            create_reduction_run(),
            reduced_at=datetime(2026, 8, 1, 0, 20),
        )


def test_run_rejects_reduction_before_analysis() -> None:
    with pytest.raises(ValueError, match="earlier than analyzed_at"):
        replace(
            create_reduction_run(),
            reduced_at=FIXED_ANALYZED_AT - timedelta(seconds=1),
        )


def test_run_is_immutable() -> None:
    run = create_reduction_run()

    with pytest.raises(FrozenInstanceError):
        run.reduced_at = FIXED_REDUCED_AT  # type: ignore[misc]