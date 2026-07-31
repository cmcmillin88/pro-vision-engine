"""Tests for the Pro Vision text importer."""

import pytest

from src.importer.text_importer import TextImporter


def test_parse_line_creates_match() -> None:
    importer = TextImporter()

    match = importer.parse_line("Arsenal - Chelsea", 1)

    assert match.match_number == 1
    assert match.home_team == "Arsenal"
    assert match.away_team == "Chelsea"
    assert match.status == "NEW"


def test_parse_line_removes_extra_spaces() -> None:
    importer = TextImporter()

    match = importer.parse_line("  Arsenal   -   Chelsea  ", 1)

    assert match.home_team == "Arsenal"
    assert match.away_team == "Chelsea"


def test_parse_line_accepts_hyphen_in_team_name() -> None:
    importer = TextImporter()

    match = importer.parse_line("Paris Saint-Germain - Marseille", 1)

    assert match.home_team == "Paris Saint-Germain"
    assert match.away_team == "Marseille"


def test_parse_line_rejects_missing_separator() -> None:
    importer = TextImporter()

    with pytest.raises(ValueError, match="Invalid match format"):
        importer.parse_line("Arsenal Chelsea", 1)


def test_parse_line_rejects_empty_home_team() -> None:
    importer = TextImporter()

    with pytest.raises(ValueError):
        importer.parse_line(" - Chelsea", 1)


def test_parse_line_rejects_empty_away_team() -> None:
    importer = TextImporter()

    with pytest.raises(ValueError):
        importer.parse_line("Arsenal - ", 1)


def test_parse_line_rejects_empty_line() -> None:
    importer = TextImporter()

    with pytest.raises(ValueError):
        importer.parse_line("", 1)