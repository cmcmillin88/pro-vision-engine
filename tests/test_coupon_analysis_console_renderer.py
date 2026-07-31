"""Tests for practical Swedish console rendering."""

import pytest

from src.exporters.coupon_analysis_console_renderer import (
    CouponAnalysisConsoleRenderer,
)
from tests.coupon_analysis_run_helpers import create_analysis_run


def create_text() -> str:
    """Render the standard practical run."""

    return CouponAnalysisConsoleRenderer().render(
        create_analysis_run()
    )


def test_renderer_includes_run_summary() -> None:
    text = create_text()

    assert "TT-EXEMPEL-2026-08-01" in text
    assert "Resultat p13-analysis-result-v1" in text


def test_renderer_includes_coupon_analysis_summary() -> None:
    text = create_text()

    assert "Matcher 8" in text
    assert "Rader " in text
    assert "Snittrisk " in text


def test_renderer_includes_turquoise_frame() -> None:
    assert "Turkos ram:" in create_text()


def test_renderer_contains_one_line_per_match() -> None:
    text = create_text()

    for match_number in range(
        1,
        9,
    ):
        assert f"{match_number}. " in text


def test_renderer_includes_swedish_decision_name() -> None:
    text = create_text()

    assert any(
        decision in text
        for decision in (
            "Spik",
            "Singel",
            "Halvgardering",
            "Helgardering",
        )
    )


def test_renderer_includes_risk_xg_and_scoreline() -> None:
    text = create_text()

    assert "Risk " in text
    assert "xG " in text
    assert "Troligast " in text


def test_renderer_preserves_unicode() -> None:
    text = create_text()

    assert "–" in text
    assert "Ã" not in text


def test_renderer_is_deterministic() -> None:
    renderer = CouponAnalysisConsoleRenderer()
    run = create_analysis_run()

    assert renderer.render(run) == renderer.render(run)


def test_renderer_rejects_invalid_run() -> None:
    with pytest.raises(
        TypeError,
        match="CouponAnalysisRun",
    ):
        CouponAnalysisConsoleRenderer().render(
            object()  # type: ignore[arg-type]
        )