"""Tests for the Pro Vision coupon model."""

from src.importer.text_importer import TextImporter
from src.models.coupon import Coupon


def test_coupon_can_add_match() -> None:
    coupon = Coupon()
    importer = TextImporter()
    match = importer.parse_line("Arsenal - Chelsea", 1)

    coupon.add_match(match)

    assert len(coupon) == 1
    assert coupon.matches[0].home_team == "Arsenal"
    assert coupon.matches[0].away_team == "Chelsea"


def test_coupon_can_hold_multiple_matches() -> None:
    coupon = Coupon()
    importer = TextImporter()

    coupon.add_match(importer.parse_line("Arsenal - Chelsea", 1))
    coupon.add_match(importer.parse_line("Liverpool - Everton", 2))

    assert len(coupon) == 2

    assert coupon.matches[0].match_number == 1
    assert coupon.matches[0].home_team == "Arsenal"
    assert coupon.matches[0].away_team == "Chelsea"

    assert coupon.matches[1].match_number == 2
    assert coupon.matches[1].home_team == "Liverpool"
    assert coupon.matches[1].away_team == "Everton"


def test_coupon_string_contains_match_information() -> None:
    coupon = Coupon()
    importer = TextImporter()

    coupon.add_match(importer.parse_line("Arsenal - Chelsea", 1))

    coupon_text = str(coupon)

    assert "Coupon" in coupon_text
    assert "Arsenal" in coupon_text
    assert "Chelsea" in coupon_text
    assert "Total matches: 1" in coupon_text