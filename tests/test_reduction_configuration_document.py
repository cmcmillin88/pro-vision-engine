"""Tests for practical reduction-configuration documents."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from src.importer.reduction_configuration_json_importer import (
    ReductionConfigurationJsonImporter,
)
from src.models.game_type import GameType
from src.models.reduction_configuration_document import (
    MarketSnapshotSelection,
    ReductionConfigurationDocument,
)
from tests.coupon_analysis_run_helpers import (
    create_analysis_run,
)
from tests.reduction_configuration_helpers import (
    create_configuration_document,
    create_full_payload,
    load_example_payload,
)


def test_document_exposes_current_schema_version() -> None:
    assert (
        ReductionConfigurationDocument.CURRENT_SCHEMA_VERSION
        == "p13-reduction-input-v1"
    )


def test_document_links_the_exact_analysis_run() -> None:
    document = create_configuration_document()

    assert document.analysis_run == create_analysis_run()


def test_document_exposes_coupon_metadata() -> None:
    document = create_configuration_document()

    assert document.coupon_id == "TT-EXEMPEL-2026-08-01"
    assert document.game_type is GameType.TOPPTIPSET
    assert document.frame_pattern == (
        create_analysis_run().recommendation_pattern
    )


def test_document_exposes_all_condition_counts() -> None:
    document = create_configuration_document()

    assert document.condition_count == 5
    assert document.atomic_condition_count == 8


def test_document_normalizes_row_price_to_ore() -> None:
    document = replace(
        create_configuration_document(),
        row_price="1.006",  # type: ignore[arg-type]
    )

    assert document.row_price == Decimal("1.01")


def test_document_exposes_snapshot_selections() -> None:
    document = create_configuration_document()

    assert (
        document.odds_snapshot_selection
        is MarketSnapshotSelection.LATER
    )
    assert (
        document.payout_snapshot_selection
        is MarketSnapshotSelection.LATER
    )


def test_document_exposes_unique_frozen_sources() -> None:
    document = create_configuration_document()

    assert document.frozen_sources == (
        "Exempelmarknad",
    )


def test_document_exposes_condition_pattern() -> None:
    document = create_configuration_document()

    assert "Färg Röd 0/2 + Gul 0/1" in document.condition_pattern
    assert "Poäng 0/12" in document.condition_pattern
    assert "Odds 1.00 <= odds < 999999999.00" in (
        document.condition_pattern
    )
    assert "Utdelning 0.00 <= utdelning <= 400000.00" in (
        document.condition_pattern
    )


def test_document_exposes_summary_line() -> None:
    document = create_configuration_document()

    assert document.summary_line == (
        "Topptipset | Kupong TT-EXEMPEL-2026-08-01 | "
        "Villkor 5 | Atomvillkor 8 | Radpris 1.00 kr | "
        "Kontrakt p13-reduction-input-v1"
    )


def test_document_preserves_source_name() -> None:
    document = create_configuration_document()

    assert document.source_name == "test-reduction-config.json"


def test_document_is_immutable() -> None:
    document = create_configuration_document()

    with pytest.raises(
        FrozenInstanceError,
    ):
        document.row_price = Decimal("2.00")  # type: ignore[misc]


def test_document_rejects_unsupported_schema_version() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        replace(
            create_configuration_document(),
            schema_version="p13-reduction-input-v2",
        )


def test_document_rejects_invalid_analysis_run_type() -> None:
    with pytest.raises(
        TypeError,
        match="CouponAnalysisRun",
    ):
        replace(
            create_configuration_document(),
            analysis_run=object(),  # type: ignore[arg-type]
        )


def test_document_rejects_invalid_condition_set_type() -> None:
    with pytest.raises(
        TypeError,
        match="ReductionConditionSet",
    ):
        replace(
            create_configuration_document(),
            condition_set=object(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "row_price",
    (
        "0",
        "-1",
    ),
)
def test_document_rejects_non_positive_row_price(
    row_price: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        replace(
            create_configuration_document(),
            row_price=row_price,  # type: ignore[arg-type]
        )


def test_document_rejects_invalid_target_game_type() -> None:
    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        replace(
            create_configuration_document(),
            target_game_type=GameType.STRYKTIPSET,
        )


def test_document_rejects_unknown_target_game_type() -> None:
    with pytest.raises(
        ValueError,
        match="supported",
    ):
        replace(
            create_configuration_document(),
            target_game_type=GameType.UNKNOWN,
        )


def test_document_rejects_wrong_coupon_id() -> None:
    with pytest.raises(
        ValueError,
        match="target_coupon_id",
    ):
        replace(
            create_configuration_document(),
            target_coupon_id="OTHER-COUPON",
        )


def test_document_rejects_wrong_frame_pattern() -> None:
    with pytest.raises(
        ValueError,
        match="expected_frame_pattern",
    ):
        replace(
            create_configuration_document(),
            expected_frame_pattern="INVALID-FRAME-PATTERN",
        )


def test_document_requires_odds_snapshot_metadata_when_active() -> None:
    with pytest.raises(
        ValueError,
        match="odds_snapshot_selection",
    ):
        replace(
            create_configuration_document(),
            odds_snapshot_selection=None,
        )


def test_document_requires_payout_snapshot_metadata_when_active() -> None:
    with pytest.raises(
        ValueError,
        match="payout_snapshot_selection",
    ):
        replace(
            create_configuration_document(),
            payout_snapshot_selection=None,
        )


def test_document_rejects_snapshot_metadata_without_rule() -> None:
    run = create_analysis_run()
    payload = load_example_payload()
    del payload["conditions"]["odds"]
    del payload["conditions"]["payout"]

    document = ReductionConfigurationJsonImporter().from_dict(
        payload,
        run,
    )

    with pytest.raises(
        ValueError,
        match="odds_snapshot_selection",
    ):
        replace(
            document,
            odds_snapshot_selection=MarketSnapshotSelection.LATER,
        )


def test_document_supports_optional_target_fields() -> None:
    run = create_analysis_run()
    payload = create_full_payload(
        run
    )
    payload["target"]["coupon_id"] = None
    payload["target"]["frame_pattern"] = None

    document = ReductionConfigurationJsonImporter().from_dict(
        payload,
        run,
    )

    assert document.target_coupon_id is None
    assert document.expected_frame_pattern is None