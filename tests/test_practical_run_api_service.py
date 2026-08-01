"""Tests for in-memory practical API workflow service."""

import json
from pathlib import Path

import pytest

from src.exporters.coupon_analysis_result_json_exporter import (
    CouponAnalysisResultJsonExporter,
)
from src.exporters.coupon_reduction_result_json_exporter import (
    CouponReductionResultJsonExporter,
)
from src.importer.coupon_analysis_json_importer import (
    CouponAnalysisJsonImporter,
)
from src.importer.reduction_configuration_json_importer import (
    ReductionConfigurationJsonImporter,
)
from src.services.coupon_analysis_file_runner import (
    CouponAnalysisFileRunner,
)
from src.services.coupon_reduction_file_runner import (
    CouponReductionFileRunner,
)
from src.services.practical_run_api_service import (
    PracticalRunApiService,
)


ANALYSIS_PATH = Path(
    "examples/topptipset-analysis-input.json"
)
REDUCTION_PATH = Path(
    "examples/topptipset-reduction-config.json"
)


def load_json(path: Path) -> dict[str, object]:
    """Load one committed UTF-8 JSON example."""

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def test_service_creates_complete_analysis_result() -> None:
    result = PracticalRunApiService().create_analysis_run(
        load_json(
            ANALYSIS_PATH
        )
    )

    assert result["schema_version"] == (
        "p13-analysis-result-v1"
    )
    assert result["coupon"]["match_count"] == 8
    assert len(result["matches"]) == 8


def test_analysis_result_preserves_coupon_id() -> None:
    result = PracticalRunApiService().create_analysis_run(
        load_json(
            ANALYSIS_PATH
        )
    )

    assert result["coupon"]["id"] == (
        "TT-EXEMPEL-2026-08-01"
    )


def test_analysis_result_contains_turquoise_frame() -> None:
    result = PracticalRunApiService().create_analysis_run(
        load_json(
            ANALYSIS_PATH
        )
    )

    assert result["frame"]["pattern"]
    assert result["frame"]["row_count"] > 0


def test_analysis_result_uses_api_source_name() -> None:
    result = PracticalRunApiService().create_analysis_run(
        load_json(
            ANALYSIS_PATH
        )
    )

    assert result["analysis"]["source_name"] == "api"


def test_service_creates_complete_reduction_result() -> None:
    result = PracticalRunApiService().create_reduction_run(
        load_json(
            ANALYSIS_PATH
        ),
        load_json(
            REDUCTION_PATH
        ),
    )

    assert result["schema_version"] == (
        "p13-reduction-result-v1"
    )
    assert result["result"]["version"] == (
        "p13-reduction-report-v1"
    )


def test_reduction_result_preserves_analysis_contract() -> None:
    result = PracticalRunApiService().create_reduction_run(
        load_json(
            ANALYSIS_PATH
        ),
        load_json(
            REDUCTION_PATH
        ),
    )

    assert result["analysis"]["schema_version"] == (
        "p13-analysis-result-v1"
    )


def test_reduction_result_preserves_configuration_contract() -> None:
    result = PracticalRunApiService().create_reduction_run(
        load_json(
            ANALYSIS_PATH
        ),
        load_json(
            REDUCTION_PATH
        ),
    )

    assert result["reduction"]["configuration_schema_version"] == (
        "p13-reduction-input-v1"
    )


def test_reduction_result_contains_consistent_counts() -> None:
    result = PracticalRunApiService().create_reduction_run(
        load_json(
            ANALYSIS_PATH
        ),
        load_json(
            REDUCTION_PATH
        ),
    )

    counts = result["result"]["counts"]

    assert (
        counts["approved"]
        + counts["rejected"]
        == counts["original"]
    )


def test_reduction_result_contains_approved_rows() -> None:
    result = PracticalRunApiService().create_reduction_run(
        load_json(
            ANALYSIS_PATH
        ),
        load_json(
            REDUCTION_PATH
        ),
    )

    assert result["rows"]["approved_count"] == len(
        result["rows"]["approved"]
    )


def test_reduction_result_uses_api_configuration_source() -> None:
    result = PracticalRunApiService().create_reduction_run(
        load_json(
            ANALYSIS_PATH
        ),
        load_json(
            REDUCTION_PATH
        ),
    )

    assert result["reduction"]["configuration_source"] == "api"


@pytest.mark.parametrize(
    "invalid_value",
    (
        None,
        [],
        "document",
        42,
    ),
)
def test_analysis_rejects_non_mapping_document(
    invalid_value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="analysis_document must be a mapping",
    ):
        PracticalRunApiService().create_analysis_run(
            invalid_value  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    (
        "analysis_value",
        "reduction_value",
        "expected_field",
    ),
    (
        (
            None,
            {},
            "analysis_document",
        ),
        (
            {},
            None,
            "reduction_configuration",
        ),
        (
            [],
            {},
            "analysis_document",
        ),
        (
            {},
            [],
            "reduction_configuration",
        ),
    ),
)
def test_reduction_rejects_non_mapping_documents(
    analysis_value: object,
    reduction_value: object,
    expected_field: str,
) -> None:
    with pytest.raises(
        TypeError,
        match=f"{expected_field} must be a mapping",
    ):
        PracticalRunApiService().create_reduction_run(
            analysis_value,  # type: ignore[arg-type]
            reduction_value,  # type: ignore[arg-type]
        )


def test_analysis_propagates_strict_document_validation() -> None:
    payload = load_json(
        ANALYSIS_PATH
    )
    payload["schema_version"] = "unsupported"

    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        PracticalRunApiService().create_analysis_run(
            payload
        )


def test_reduction_propagates_strict_configuration_validation() -> None:
    configuration = load_json(
        REDUCTION_PATH
    )
    configuration["schema_version"] = "unsupported"

    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        PracticalRunApiService().create_reduction_run(
            load_json(
                ANALYSIS_PATH
            ),
            configuration,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "expected_type",
    ),
    (
        (
            "analysis_importer",
            "CouponAnalysisJsonImporter",
        ),
        (
            "analysis_runner",
            "CouponAnalysisFileRunner",
        ),
        (
            "reduction_importer",
            "ReductionConfigurationJsonImporter",
        ),
        (
            "reduction_runner",
            "CouponReductionFileRunner",
        ),
        (
            "analysis_exporter",
            "CouponAnalysisResultJsonExporter",
        ),
        (
            "reduction_exporter",
            "CouponReductionResultJsonExporter",
        ),
    ),
)
def test_service_rejects_invalid_dependencies(
    field_name: str,
    expected_type: str,
) -> None:
    with pytest.raises(
        TypeError,
        match=expected_type,
    ):
        PracticalRunApiService(
            **{
                field_name: object(),
            }
        )


def test_service_accepts_explicit_dependencies() -> None:
    service = PracticalRunApiService(
        analysis_importer=CouponAnalysisJsonImporter(),
        analysis_runner=CouponAnalysisFileRunner(),
        reduction_importer=(
            ReductionConfigurationJsonImporter()
        ),
        reduction_runner=CouponReductionFileRunner(),
        analysis_exporter=(
            CouponAnalysisResultJsonExporter()
        ),
        reduction_exporter=(
            CouponReductionResultJsonExporter()
        ),
    )

    result = service.create_analysis_run(
        load_json(
            ANALYSIS_PATH
        )
    )

    assert result["coupon"]["match_count"] == 8