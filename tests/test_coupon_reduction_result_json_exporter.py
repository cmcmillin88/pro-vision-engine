"""Tests for the practical coupon-reduction JSON exporter."""

import json

import pytest

from src.exporters.coupon_reduction_result_json_exporter import (
    CouponReductionResultJsonExporter,
)
from tests.coupon_reduction_run_helpers import create_reduction_run


def test_exporter_creates_versioned_payload() -> None:
    payload = CouponReductionResultJsonExporter().to_dict(
        create_reduction_run()
    )

    assert payload["schema_version"] == "p13-reduction-result-v1"


def test_exporter_serializes_coupon_metadata() -> None:
    payload = CouponReductionResultJsonExporter().to_dict(
        create_reduction_run()
    )

    assert payload["coupon"]["id"] == "TT-EXEMPEL-2026-08-01"
    assert payload["coupon"]["game_type"] == "topptipset"
    assert payload["coupon"]["match_count"] == 8


def test_exporter_serializes_configuration_metadata() -> None:
    payload = CouponReductionResultJsonExporter().to_dict(
        create_reduction_run()
    )

    assert payload["configuration"]["row_price"] == "1.00"
    assert payload["configuration"]["condition_count"] == 3
    assert payload["configuration"]["atomic_condition_count"] == 5


def test_exporter_embeds_complete_reduction_report() -> None:
    payload = CouponReductionResultJsonExporter().to_dict(
        create_reduction_run()
    )

    assert payload["result"]["version"] == "p13-reduction-report-v1"
    assert payload["result"]["counts"]["original"] > 0


def test_exporter_embeds_complete_analysis_result() -> None:
    payload = CouponReductionResultJsonExporter().to_dict(
        create_reduction_run()
    )

    assert payload["analysis"]["schema_version"] == (
        "p13-analysis-result-v1"
    )
    assert len(payload["analysis"]["matches"]) == 8


def test_exporter_serializes_all_surviving_rows() -> None:
    run = create_reduction_run()
    payload = CouponReductionResultJsonExporter().to_dict(run)

    assert payload["rows"]["approved_count"] == run.approved_row_count
    assert payload["rows"]["approved"] == list(run.approved_symbols)


def test_exporter_serializes_exact_costs_as_strings() -> None:
    payload = CouponReductionResultJsonExporter().to_dict(
        create_reduction_run()
    )

    assert isinstance(payload["cost"]["original"], str)
    assert isinstance(payload["cost"]["final"], str)
    assert isinstance(payload["cost"]["savings"], str)


def test_exporter_preserves_unicode() -> None:
    json_text = CouponReductionResultJsonExporter().to_json(
        create_reduction_run()
    )

    assert "Utdelning" in json_text
    assert "Ã" not in json_text


def test_exporter_supports_compact_json() -> None:
    json_text = CouponReductionResultJsonExporter().to_json(
        create_reduction_run(),
        indent=None,
    )

    assert "\n" not in json_text
    assert json.loads(json_text)["schema_version"] == (
        "p13-reduction-result-v1"
    )


def test_exporter_rejects_invalid_run_type() -> None:
    with pytest.raises(TypeError, match="CouponReductionRun"):
        CouponReductionResultJsonExporter().to_dict(
            object()  # type: ignore[arg-type]
        )


def test_exporter_rejects_boolean_indent() -> None:
    with pytest.raises(TypeError, match="indent"):
        CouponReductionResultJsonExporter().to_json(
            create_reduction_run(),
            indent=True,  # type: ignore[arg-type]
        )


def test_exporter_rejects_negative_indent() -> None:
    with pytest.raises(ValueError, match="negative"):
        CouponReductionResultJsonExporter().to_json(
            create_reduction_run(),
            indent=-1,
        )