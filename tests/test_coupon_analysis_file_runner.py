"""Tests for the practical JSON-file analysis runner."""

from datetime import datetime, timezone

import pytest

from src.importer.coupon_analysis_json_importer import (
    CouponAnalysisJsonImporter,
)
from src.services.coupon_analysis_file_runner import (
    CouponAnalysisFileRunner,
)
from src.services.final_coupon_analysis_engine import (
    FinalCouponAnalysisEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)
from tests.coupon_analysis_run_helpers import (
    EXAMPLE_PATH,
    FIXED_ANALYZED_AT,
)


def test_runner_executes_complete_file_pipeline() -> None:
    run = CouponAnalysisFileRunner().run_file(
        EXAMPLE_PATH,
        analyzed_at=FIXED_ANALYZED_AT,
    )

    assert run.match_count == 8
    assert run.base_system.is_complete_frame is True


def test_runner_supports_imported_document() -> None:
    document = CouponAnalysisJsonImporter().from_file(
        EXAMPLE_PATH
    )

    run = CouponAnalysisFileRunner().run_document(
        document,
        analyzed_at=FIXED_ANALYZED_AT,
    )

    assert run.input_document == document


def test_runner_generates_timezone_aware_timestamp_by_default() -> None:
    document = CouponAnalysisJsonImporter().from_file(
        EXAMPLE_PATH
    )

    run = CouponAnalysisFileRunner().run_document(
        document
    )

    assert run.analyzed_at.tzinfo is not None
    assert run.analyzed_at.utcoffset() is not None


def test_runner_preserves_supplied_timestamp() -> None:
    supplied = datetime(
        2026,
        8,
        1,
        2,
        30,
        tzinfo=timezone.utc,
    )

    run = CouponAnalysisFileRunner().run_file(
        EXAMPLE_PATH,
        analyzed_at=supplied,
    )

    assert run.analyzed_at == supplied


def test_runner_rejects_missing_file() -> None:
    with pytest.raises(
        FileNotFoundError,
    ):
        CouponAnalysisFileRunner().run_file(
            "examples/missing-analysis-input.json"
        )


def test_runner_rejects_invalid_document_type() -> None:
    with pytest.raises(
        TypeError,
        match="CouponAnalysisDocument",
    ):
        CouponAnalysisFileRunner().run_document(
            object()  # type: ignore[arg-type]
        )


def test_runner_rejects_naive_timestamp() -> None:
    document = CouponAnalysisJsonImporter().from_file(
        EXAMPLE_PATH
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        CouponAnalysisFileRunner().run_document(
            document,
            analyzed_at=datetime(
                2026,
                8,
                1,
                2,
                30,
            ),
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "expected_text",
    ),
    (
        (
            "importer",
            "CouponAnalysisJsonImporter",
        ),
        (
            "analysis_engine",
            "FinalCouponAnalysisEngine",
        ),
        (
            "row_generator",
            "ReductionRowGenerator",
        ),
    ),
)
def test_runner_rejects_invalid_dependencies(
    field_name: str,
    expected_text: str,
) -> None:
    with pytest.raises(
        TypeError,
        match=expected_text,
    ):
        CouponAnalysisFileRunner(
            **{
                field_name: object(),
            }
        )


def test_runner_accepts_explicit_dependencies() -> None:
    runner = CouponAnalysisFileRunner(
        importer=CouponAnalysisJsonImporter(),
        analysis_engine=FinalCouponAnalysisEngine(),
        row_generator=ReductionRowGenerator(),
    )

    run = runner.run_file(
        EXAMPLE_PATH,
        analyzed_at=FIXED_ANALYZED_AT,
    )

    assert run.match_count == 8