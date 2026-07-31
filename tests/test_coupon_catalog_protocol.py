"""Tests for the shared coupon catalog protocol."""

from pathlib import Path

from src.services.coupon_catalog_protocol import (
    CouponCatalog,
)
from src.services.demo_coupon_catalog import (
    DemoCouponCatalog,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COUPON_DIRECTORY = (
    PROJECT_ROOT
    / "examples"
    / "svenska_spel"
)


def test_demo_catalog_satisfies_shared_protocol() -> None:
    catalog = DemoCouponCatalog(
        COUPON_DIRECTORY
    )

    assert isinstance(
        catalog,
        CouponCatalog,
    )
    assert catalog.source_name == "demo"
    assert (
        catalog.source_display_name
        == "Local demonstration data"
    )
    assert catalog.is_live is False