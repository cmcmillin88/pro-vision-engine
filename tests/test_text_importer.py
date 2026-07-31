"""Tests for the Pro Vision text importer."""

from src.importer.text_importer import TextImporter


def test_parse_line_creates_match() -> None:
    importer = TextImporter()

    match = importer.parse_line("Arsenal - Chelsea", 1)

    assert match.match_number == 1
    assert match.home_team == "Arsenal"
    assert match.away_team == "Chelsea"
    assert match.status == "NEW"