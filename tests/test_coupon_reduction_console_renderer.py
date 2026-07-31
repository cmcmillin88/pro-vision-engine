"""Tests for the practical Swedish coupon-reduction console renderer."""

import pytest

from src.exporters.coupon_reduction_console_renderer import (
    CouponReductionConsoleRenderer,
)
from tests.coupon_reduction_run_helpers import create_reduction_run


def test_renderer_contains_complete_summary_chain() -> None:
    text = CouponReductionConsoleRenderer().render(
        create_reduction_run()
    )

    assert "p13-reduction-result-v1" in text
    assert "Turkos ram:" in text
    assert "Villkor:" in text


def test_renderer_contains_cost_summary() -> None:
    text = CouponReductionConsoleRenderer().render(
        create_reduction_run()
    )

    assert "Kostnad:" in text
    assert "Besparing" in text


def test_renderer_contains_condition_impacts() -> None:
    text = CouponReductionConsoleRenderer().render(
        create_reduction_run()
    )

    assert "Villkorseffekt:" in text
    assert "1X2" in text
    assert "Odds" in text
    assert "Utdelning" in text


def test_renderer_contains_rejection_pattern_section() -> None:
    text = CouponReductionConsoleRenderer().render(
        create_reduction_run()
    )

    assert "Bortfallsmönster:" in text


def test_renderer_contains_surviving_row_section() -> None:
    text = CouponReductionConsoleRenderer().render(
        create_reduction_run()
    )

    assert "Kvarvarande rader" in text


def test_renderer_limits_row_preview() -> None:
    run = create_reduction_run()
    text = CouponReductionConsoleRenderer(max_rows=1).render(run)

    if run.approved_row_count > 1:
        assert "ytterligare" in text


def test_renderer_exposes_preview_limit() -> None:
    renderer = CouponReductionConsoleRenderer(max_rows=7)

    assert renderer.max_rows == 7


def test_renderer_rejects_invalid_run_type() -> None:
    with pytest.raises(TypeError, match="CouponReductionRun"):
        CouponReductionConsoleRenderer().render(
            object()  # type: ignore[arg-type]
        )


def test_renderer_rejects_boolean_max_rows() -> None:
    with pytest.raises(TypeError, match="max_rows"):
        CouponReductionConsoleRenderer(max_rows=True)  # type: ignore[arg-type]


def test_renderer_rejects_non_positive_max_rows() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        CouponReductionConsoleRenderer(max_rows=0)