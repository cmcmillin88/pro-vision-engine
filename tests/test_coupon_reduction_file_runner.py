"""Tests for the practical complete coupon-reduction file runner."""

from datetime import datetime, timedelta, timezone

import pytest

from src.importer.reduction_configuration_json_importer import (
    ReductionConfigurationJsonImporter,
)
from src.services.coupon_analysis_file_runner import (
    CouponAnalysisFileRunner,
)
from src.services.coupon_reduction_file_runner import (
    CouponReductionFileRunner,
)
from src.services.final_reduction_report_engine import (
    FinalReductionReportEngine,
)
from tests.coupon_reduction_run_helpers import (
    ANALYSIS_PATH,
    FIXED_ANALYZED_AT,
    FIXED_REDUCED_AT,
    REDUCTION_PATH,
    create_reduction_run,
)


def test_runner_executes_complete_two_file_pipeline() -> None:
    run = create_reduction_run()

    assert run.match_count == 8
    assert run.reduction_report.original_row_count > 0


def test_runner_supports_imported_configuration() -> None:
    analysis_run = CouponAnalysisFileRunner().run_file(
        ANALYSIS_PATH,
        analyzed_at=FIXED_ANALYZED_AT,
    )
    configuration = ReductionConfigurationJsonImporter().from_file(
        REDUCTION_PATH,
        analysis_run,
    )

    run = CouponReductionFileRunner().run_configuration(
        configuration,
        reduced_at=FIXED_REDUCED_AT,
    )

    assert run.configuration == configuration


def test_runner_preserves_supplied_timestamps() -> None:
    run = CouponReductionFileRunner().run_files(
        ANALYSIS_PATH,
        REDUCTION_PATH,
        analyzed_at=FIXED_ANALYZED_AT,
        reduced_at=FIXED_REDUCED_AT,
    )

    assert run.analysis_run.analyzed_at == FIXED_ANALYZED_AT
    assert run.reduced_at == FIXED_REDUCED_AT


def test_runner_generates_timezone_aware_default_reduction_time() -> None:
    analysis_run = CouponAnalysisFileRunner().run_file(ANALYSIS_PATH)
    configuration = ReductionConfigurationJsonImporter().from_file(
        REDUCTION_PATH,
        analysis_run,
    )

    run = CouponReductionFileRunner().run_configuration(configuration)

    assert run.reduced_at.tzinfo is not None
    assert run.reduced_at.utcoffset() is not None


def test_runner_rejects_missing_analysis_file() -> None:
    with pytest.raises(FileNotFoundError):
        CouponReductionFileRunner().run_files(
            "examples/missing-analysis.json",
            REDUCTION_PATH,
        )


def test_runner_rejects_missing_reduction_file() -> None:
    with pytest.raises(FileNotFoundError):
        CouponReductionFileRunner().run_files(
            ANALYSIS_PATH,
            "examples/missing-reduction.json",
        )


def test_runner_rejects_invalid_configuration_type() -> None:
    with pytest.raises(TypeError, match="ReductionConfigurationDocument"):
        CouponReductionFileRunner().run_configuration(
            object()  # type: ignore[arg-type]
        )


def test_runner_rejects_naive_reduction_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        CouponReductionFileRunner().run_files(
            ANALYSIS_PATH,
            REDUCTION_PATH,
            analyzed_at=FIXED_ANALYZED_AT,
            reduced_at=datetime(2026, 8, 1, 0, 20),
        )


def test_runner_rejects_reduction_before_analysis() -> None:
    with pytest.raises(ValueError, match="earlier than analyzed_at"):
        CouponReductionFileRunner().run_files(
            ANALYSIS_PATH,
            REDUCTION_PATH,
            analyzed_at=FIXED_ANALYZED_AT,
            reduced_at=FIXED_ANALYZED_AT - timedelta(seconds=1),
        )


def test_runner_accepts_explicit_dependencies() -> None:
    runner = CouponReductionFileRunner(
        analysis_runner=CouponAnalysisFileRunner(),
        configuration_importer=ReductionConfigurationJsonImporter(),
        report_engine=FinalReductionReportEngine(),
    )

    run = runner.run_files(
        ANALYSIS_PATH,
        REDUCTION_PATH,
        analyzed_at=FIXED_ANALYZED_AT,
        reduced_at=FIXED_REDUCED_AT,
    )

    assert run.reduced_at == FIXED_REDUCED_AT


def test_runner_rejects_invalid_analysis_runner_dependency() -> None:
    with pytest.raises(TypeError, match="CouponAnalysisFileRunner"):
        CouponReductionFileRunner(
            analysis_runner=object()  # type: ignore[arg-type]
        )


def test_runner_rejects_invalid_importer_dependency() -> None:
    with pytest.raises(TypeError, match="ReductionConfigurationJsonImporter"):
        CouponReductionFileRunner(
            configuration_importer=object()  # type: ignore[arg-type]
        )


def test_runner_rejects_invalid_report_engine_dependency() -> None:
    with pytest.raises(TypeError, match="FinalReductionReportEngine"):
        CouponReductionFileRunner(
            report_engine=object()  # type: ignore[arg-type]
        )