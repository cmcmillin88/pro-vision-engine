"""Tests for importing a coupon from a text file."""

from pathlib import Path

from src.importer.text_importer import TextImporter


def test_load_coupon_from_file(tmp_path: Path) -> None:
    coupon_file = tmp_path / "coupon.txt"

    coupon_file.write_text(
        "Arsenal - Chelsea\n"
        "\n"
        "Liverpool - Everton\n",
        encoding="utf-8",
    )

    importer = TextImporter()
    coupon = importer.load_coupon(coupon_file)

    assert len(coupon) == 2

    assert coupon.matches[0].match_number == 1
    assert coupon.matches[0].home_team == "Arsenal"
    assert coupon.matches[0].away_team == "Chelsea"

    assert coupon.matches[1].match_number == 2
    assert coupon.matches[1].home_team == "Liverpool"
    assert coupon.matches[1].away_team == "Everton"