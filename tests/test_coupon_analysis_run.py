"""Tests for complete practical coupon-analysis run models."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime

import pytest

from src.models.coupon_analysis_run import CouponAnalysisRun
from tests.coupon_analysis_run_helpers import (
    FIXED_ANALYZED_AT,
    create_analysis_run,
)


def test_run_uses_versioned_result_contract() -> None:
    run = create_analysis_run()

    assert run.schema_version == "p13-analysis-result-v1"
    assert (
        CouponAnalysisRun.CURRENT_SCHEMA_VERSION
        == "p13-analysis-result-v1"
    )


def test_run_exposes_coupon_metadata() -> None:
    run = create_analysis_run()

    assert run.coupon_id == "TT-EXEMPEL-2026-08-01"
    assert run.game_type.value == "topptipset"
    assert run.match_count == 8


def test_run_links_analysis_and_frame() -> None:
    run = create_analysis_run()

    assert (
        run.analysis_report.analysis_input
        == run.input_document.analysis_input
    )
    assert run.base_system.frame == run.reduction_frame


def test_run_exposes_complete_turquoise_system() -> None:
    run = create_analysis_run()

    assert run.recommendation_pattern
    assert run.base_row_count > 0
    assert (
        run.base_row_count
        == run.analysis_report.base_row_count
    )


def test_run_preserves_fixed_analysis_timestamp() -> None:
    assert create_analysis_run().analyzed_at == FIXED_ANALYZED_AT


def test_run_exposes_source_name() -> None:
    source_name = create_analysis_run().source_name

    assert source_name is not None
    assert source_name.endswith(
        "topptipset-analysis-input.json"
    )


def test_run_summary_contains_practical_chain() -> None:
    summary = create_analysis_run().summary_line

    assert "Topptipset" in summary
    assert "TT-EXEMPEL-2026-08-01" in summary
    assert "Matcher 8" in summary
    assert "Ram " in summary
    assert "Resultat p13-analysis-result-v1" in summary


def test_run_is_immutable() -> None:
    with pytest.raises(
        FrozenInstanceError,
    ):
        create_analysis_run().schema_version = "changed"  # type: ignore[misc]


def test_run_rejects_unsupported_schema_version() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        replace(
            create_analysis_run(),
            schema_version="v2",
        )


def test_run_rejects_naive_analysis_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        replace(
            create_analysis_run(),
            analyzed_at=datetime(
                2026,
                8,
                1,
                1,
                0,
            ),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "input_document",
        "analysis_report",
        "reduction_frame",
        "base_system",
    ),
)
def test_run_rejects_invalid_chain_types(
    field_name: str,
) -> None:
    with pytest.raises(
        TypeError,
    ):
        replace(
            create_analysis_run(),
            **{
                field_name: object(),
            },
        )