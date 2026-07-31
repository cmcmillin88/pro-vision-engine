"""Tests for the versioned coupon-analysis document wrapper."""

from dataclasses import replace

import pytest

from src.importer.coupon_analysis_json_importer import (
    CouponAnalysisJsonImporter,
)
from src.models.coupon_analysis_document import (
    CouponAnalysisDocument,
)
from src.models.game_type import GameType
from tests.analysis_input_helpers import EXAMPLE_PATH


def create_document() -> CouponAnalysisDocument:
    """Load the official Topptipset example document."""

    return CouponAnalysisJsonImporter().from_file(
        EXAMPLE_PATH
    )


def test_document_exposes_current_schema_version() -> None:
    assert (
        CouponAnalysisDocument.CURRENT_SCHEMA_VERSION
        == "p13-analysis-input-v1"
    )


def test_document_exposes_coupon_properties() -> None:
    document = create_document()

    assert document.coupon_id == "TT-EXEMPEL-2026-08-01"
    assert document.game_type is GameType.TOPPTIPSET
    assert document.match_count == 8
    assert len(document.matches) == 8


def test_document_normalizes_source_name() -> None:
    document = replace(
        create_document(),
        source_name="  Manuell   fil  ",
    )

    assert document.source_name == "Manuell fil"


def test_document_exposes_summary_line() -> None:
    assert create_document().summary_line == (
        "Topptipset | Kupong TT-EXEMPEL-2026-08-01 | "
        "Matcher 8 | Kontrakt p13-analysis-input-v1"
    )


def test_document_supports_missing_coupon_id() -> None:
    document = create_document()
    analysis_input = replace(
        document.analysis_input,
        coupon_id=None,
    )

    changed = replace(
        document,
        analysis_input=analysis_input,
    )

    assert "Kupong utan id" in changed.summary_line


def test_document_rejects_non_string_version() -> None:
    with pytest.raises(
        TypeError,
        match="schema_version",
    ):
        replace(
            create_document(),
            schema_version=1,  # type: ignore[arg-type]
        )


def test_document_rejects_unsupported_version() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        replace(
            create_document(),
            schema_version="p13-analysis-input-v2",
        )


def test_document_rejects_invalid_analysis_input() -> None:
    with pytest.raises(
        TypeError,
        match="CouponAnalysisInput",
    ):
        replace(
            create_document(),
            analysis_input=object(),  # type: ignore[arg-type]
        )


def test_document_rejects_invalid_source_name() -> None:
    with pytest.raises(
        TypeError,
        match="source_name",
    ):
        replace(
            create_document(),
            source_name=1,  # type: ignore[arg-type]
        )


def test_document_rejects_empty_source_name() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        replace(
            create_document(),
            source_name="   ",
        )