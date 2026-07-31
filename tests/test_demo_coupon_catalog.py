"""Tests for the local demonstration coupon catalog."""

from pathlib import Path

import pytest

from src.models.game_type import GameType
from src.services.demo_coupon_catalog import (
    DemoCouponCatalog,
    DemoCouponNotFoundError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COUPON_DIRECTORY = (
    PROJECT_ROOT
    / "examples"
    / "svenska_spel"
)


def create_catalog() -> DemoCouponCatalog:
    """Create the demonstration coupon catalog."""

    return DemoCouponCatalog(
        COUPON_DIRECTORY
    )


def test_catalog_lists_supported_game_types() -> None:
    catalog = create_catalog()

    assert catalog.available_game_types == (
        "topptipset",
        "stryktipset",
        "europatipset",
    )


@pytest.mark.parametrize(
    (
        "game_type_name",
        "expected_game_type",
        "expected_match_count",
    ),
    [
        (
            "topptipset",
            GameType.TOPPTIPSET,
            8,
        ),
        (
            "stryktipset",
            GameType.STRYKTIPSET,
            13,
        ),
        (
            "europatipset",
            GameType.EUROPATIPSET,
            13,
        ),
    ],
)
def test_catalog_loads_supported_coupon(
    game_type_name: str,
    expected_game_type: GameType,
    expected_match_count: int,
) -> None:
    catalog = create_catalog()

    coupon = catalog.load(
        game_type_name
    )

    assert coupon.game_type is expected_game_type
    assert len(coupon) == expected_match_count


def test_catalog_normalizes_game_type_name() -> None:
    catalog = create_catalog()

    coupon = catalog.load(
        "  TOPPTIPSET  "
    )

    assert coupon.game_type is GameType.TOPPTIPSET
    assert len(coupon) == 8


def test_catalog_rejects_unknown_game_type() -> None:
    catalog = create_catalog()

    with pytest.raises(
        DemoCouponNotFoundError,
        match="Unknown demonstration game type",
    ):
        catalog.load(
            "unknown"
        )