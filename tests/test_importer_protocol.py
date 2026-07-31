"""Tests for the common coupon importer contract."""

from src.importer.importer_protocol import CouponImporter
from src.importer.text_importer import TextImporter


def test_text_importer_satisfies_importer_protocol() -> None:
    importer = TextImporter()

    assert isinstance(importer, CouponImporter)