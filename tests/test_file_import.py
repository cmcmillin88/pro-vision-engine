"""Tests for importing a coupon from a text file."""

from datetime import datetime, timezone
from pathlib import Path

from src.importer.text_importer import TextImporter
from src.models.game_type import GameType
from src.models.import_source import ImportSource


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
    assert coupon.source is ImportSource.TEXT_FILE
    assert coupon.game_type is GameType.UNKNOWN

    assert coupon.matches[0].match_number == 1
    assert coupon.matches[0].home_team == "Arsenal"
    assert coupon.matches[0].away_team == "Chelsea"

    assert coupon.matches[1].match_number == 2
    assert coupon.matches[1].home_team == "Liverpool"
    assert coupon.matches[1].away_team == "Everton"


def test_load_coupon_with_metadata(tmp_path: Path) -> None:
    coupon_file = tmp_path / "topptipset.txt"

    coupon_file.write_text(
        "Arsenal - Chelsea\n",
        encoding="utf-8",
    )

    deadline = datetime(
        2026,
        8,
        1,
        15,
        0,
        tzinfo=timezone.utc,
    )

    importer = TextImporter()

    coupon = importer.load_coupon(
        coupon_file,
        game_type=GameType.TOPPTIPSET,
        coupon_id="TT-2026-08-01",
        deadline=deadline,
    )

    assert coupon.game_type is GameType.TOPPTIPSET
    assert coupon.source is ImportSource.TEXT_FILE
    assert coupon.coupon_id == "TT-2026-08-01"
    assert coupon.deadline == deadline
    assert coupon.expected_match_count == 8