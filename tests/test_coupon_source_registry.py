"""Tests for the coupon source registry."""

import pytest

from src.models.coupon import Coupon
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.services.coupon_source_registry import (
    CouponSourceNotFoundError,
    CouponSourceRegistry,
    DuplicateCouponSourceError,
)


class StubCouponCatalog:
    """Minimal coupon catalog used by registry tests."""

    def __init__(
        self,
        source_name: str,
        *,
        source_display_name: str | None = None,
        is_live: bool = False,
        available_game_types: tuple[str, ...] = (
            "topptipset",
        ),
    ) -> None:
        """Create a configurable catalog stub."""

        self._source_name = source_name
        self._source_display_name = (
            source_display_name
            or source_name
        )
        self._is_live = is_live
        self._available_game_types = (
            available_game_types
        )
        self.loaded_game_types: list[str] = []

    @property
    def source_name(self) -> str:
        """Return the source name."""

        return self._source_name

    @property
    def source_display_name(self) -> str:
        """Return the source display name."""

        return self._source_display_name

    @property
    def is_live(self) -> bool:
        """Return whether the source is live."""

        return self._is_live

    @property
    def available_game_types(self) -> tuple[str, ...]:
        """Return supported game types."""

        return self._available_game_types

    def load(
        self,
        game_type_name: str,
    ) -> Coupon:
        """Return a simple coupon and record the request."""

        self.loaded_game_types.append(
            game_type_name
        )

        return Coupon(
            game_type=GameType.TOPPTIPSET,
            source=ImportSource.MANUAL,
            coupon_id=(
                f"{self.source_name}-coupon"
            ),
        )


def test_registry_lists_available_sources() -> None:
    demo_catalog = StubCouponCatalog(
        "demo"
    )
    live_catalog = StubCouponCatalog(
        "live",
        is_live=True,
    )

    registry = CouponSourceRegistry(
        [
            demo_catalog,
            live_catalog,
        ]
    )

    assert registry.available_sources == (
        "demo",
        "live",
    )
    assert (
        registry.available_game_types(
            "demo"
        )
        == ("topptipset",)
    )


def test_registry_uses_explicit_default_source() -> None:
    demo_catalog = StubCouponCatalog(
        "demo"
    )
    live_catalog = StubCouponCatalog(
        "live",
        is_live=True,
    )

    registry = CouponSourceRegistry(
        [
            demo_catalog,
            live_catalog,
        ],
        default_source_name=" LIVE ",
    )

    assert (
        registry.default_source_name
        == "live"
    )


def test_registry_loads_from_default_source() -> None:
    demo_catalog = StubCouponCatalog(
        "demo"
    )

    registry = CouponSourceRegistry(
        [demo_catalog]
    )

    coupon = registry.load(
        "topptipset"
    )

    assert coupon.coupon_id == (
        "demo-coupon"
    )
    assert demo_catalog.loaded_game_types == [
        "topptipset"
    ]


def test_registry_normalizes_explicit_source_name() -> None:
    catalog = StubCouponCatalog(
        "local-demo"
    )

    registry = CouponSourceRegistry(
        [catalog]
    )

    resolved_catalog = registry.get_catalog(
        " LOCAL_DEMO "
    )

    assert resolved_catalog is catalog


def test_registry_rejects_unknown_source() -> None:
    registry = CouponSourceRegistry(
        [
            StubCouponCatalog(
                "demo"
            )
        ]
    )

    with pytest.raises(
        CouponSourceNotFoundError,
        match="Unknown coupon source",
    ):
        registry.get_catalog(
            "missing"
        )


def test_registry_rejects_duplicate_sources() -> None:
    with pytest.raises(
        DuplicateCouponSourceError,
        match="already been registered",
    ):
        CouponSourceRegistry(
            [
                StubCouponCatalog(
                    "demo"
                ),
                StubCouponCatalog(
                    "DE-MO"
                ),
            ]
        )


def test_registry_requires_at_least_one_catalog() -> None:
    with pytest.raises(
        ValueError,
        match="at least one coupon catalog",
    ):
        CouponSourceRegistry(
            []
        )