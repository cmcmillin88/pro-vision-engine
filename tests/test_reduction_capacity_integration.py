"""Integration tests for capacity-aware practical analysis runs."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.exporters.coupon_analysis_console_renderer import (
    CouponAnalysisConsoleRenderer,
)
from src.exporters.coupon_analysis_result_json_exporter import (
    CouponAnalysisResultJsonExporter,
)
from src.importer.coupon_analysis_json_importer import (
    CouponAnalysisJsonImporter,
)
from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.reduction_capacity import (
    ReductionCapacityExceededError,
    ReductionCapacityLevel,
)
from src.models.reduction_frame import ReductionFrame
from src.services.coupon_analysis_file_runner import (
    CouponAnalysisFileRunner,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)
from tests.coupon_analysis_run_helpers import (
    EXAMPLE_PATH,
    FIXED_ANALYZED_AT,
    create_analysis_run,
)


def create_four_row_frame() -> ReductionFrame:
    """Create a compact deterministic capacity-test frame."""

    return ReductionFrame(
        game_type=GameType.TOPPTIPSET,
        allowed_outcomes=(
            (Outcome.HOME, Outcome.DRAW),
            (Outcome.HOME, Outcome.AWAY),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
            (Outcome.HOME,),
        ),
    )


def test_generator_exposes_capacity_policy() -> None:
    generator = ReductionRowGenerator(
        maximum_materialized_rows=10,
        warning_row_count=5,
    )

    assert generator.maximum_materialized_rows == 10
    assert generator.warning_row_count == 5
    assert (
        generator.capacity_policy.maximum_materialized_rows
        == 10
    )


def test_generator_derives_warning_for_small_limit() -> None:
    generator = ReductionRowGenerator(
        maximum_materialized_rows=3
    )

    assert generator.warning_row_count == 3


def test_generator_rejects_invalid_warning_threshold() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        ReductionRowGenerator(
            maximum_materialized_rows=10,
            warning_row_count=11,
        )


def test_generator_assesses_without_materializing() -> None:
    generator = ReductionRowGenerator(
        maximum_materialized_rows=3,
        warning_row_count=2,
    )

    assessment = generator.assess(
        create_four_row_frame()
    )

    assert assessment.expected_row_count == 4
    assert assessment.level is ReductionCapacityLevel.BLOCKED


def test_generator_returns_assessment_with_system() -> None:
    generator = ReductionRowGenerator(
        maximum_materialized_rows=4,
        warning_row_count=4,
    )

    assessment, system = generator.generate_with_assessment(
        create_four_row_frame()
    )

    assert assessment.expected_row_count == system.row_count
    assert assessment.level is ReductionCapacityLevel.WARNING
    assert system.row_count == 4


def test_lazy_iteration_still_bypasses_hard_limit() -> None:
    generator = ReductionRowGenerator(
        maximum_materialized_rows=1
    )

    rows = tuple(
        generator.iter_rows(
            create_four_row_frame()
        )
    )

    assert len(rows) == 4


def test_materialization_uses_capacity_error() -> None:
    generator = ReductionRowGenerator(
        maximum_materialized_rows=3,
        warning_row_count=2,
    )

    with pytest.raises(
        ReductionCapacityExceededError,
        match="4 rows.*limit of 3",
    ):
        generator.generate(
            create_four_row_frame()
        )


def test_practical_run_contains_capacity_assessment() -> None:
    run = create_analysis_run()

    assert (
        run.capacity_assessment.frame
        == run.reduction_frame
    )
    assert (
        run.capacity_assessment.expected_row_count
        == run.base_row_count
    )
    assert run.capacity_assessment.can_materialize is True
    assert run.capacity_level is run.capacity_assessment.level


def test_practical_runner_exposes_row_generator() -> None:
    row_generator = ReductionRowGenerator(
        maximum_materialized_rows=100_000,
        warning_row_count=1,
    )
    runner = CouponAnalysisFileRunner(
        row_generator=row_generator
    )

    assert runner.row_generator is row_generator


def test_practical_runner_blocks_before_materialization() -> None:
    document = CouponAnalysisJsonImporter().from_file(
        EXAMPLE_PATH
    )
    runner = CouponAnalysisFileRunner(
        row_generator=ReductionRowGenerator(
            maximum_materialized_rows=1
        )
    )

    with pytest.raises(
        ReductionCapacityExceededError,
        match="materialization limit",
    ):
        runner.run_document(
            document,
            analyzed_at=FIXED_ANALYZED_AT,
        )


def test_analysis_export_contains_capacity_metadata() -> None:
    payload = CouponAnalysisResultJsonExporter().to_dict(
        create_analysis_run()
    )
    capacity = payload["capacity"]

    assert capacity["level"] in {
        "safe",
        "warning",
    }
    assert capacity["can_materialize"] is True
    assert (
        capacity["expected_row_count"]
        == payload["frame"]["row_count"]
    )
    assert capacity["maximum_materialized_rows"] == 100_000
    assert capacity["utilization_percentage"]


def test_console_renderer_contains_capacity_summary() -> None:
    console_text = CouponAnalysisConsoleRenderer().render(
        create_analysis_run()
    )

    assert "Kapacitet " in console_text
    assert "Utnyttjande " in console_text
    assert "Singlar " in console_text


def test_analysis_api_returns_capacity_metadata() -> None:
    analysis_document = json.loads(
        Path(
            "examples/topptipset-analysis-input.json"
        ).read_text(
            encoding="utf-8"
        )
    )
    client = TestClient(
        create_app()
    )

    response = client.post(
        "/api/v1/analysis-runs",
        json={
            "analysis_document": analysis_document,
        },
    )

    assert response.status_code == 200

    result = response.json()["result"]

    assert result["capacity"]["can_materialize"] is True
    assert (
        result["capacity"]["expected_row_count"]
        == result["frame"]["row_count"]
    )