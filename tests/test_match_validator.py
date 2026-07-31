"""Tests for the Pro Vision match validator."""

import pytest

from src.validators.match_validator import MatchValidator


def test_validator_splits_valid_match_line() -> None:
    validator = MatchValidator()

    home_team, away_team = validator.validate_and_split(
        "Arsenal - Chelsea",
        1,
    )

    assert home_team == "Arsenal"
    assert away_team == "Chelsea"


def test_validator_removes_extra_spaces() -> None:
    validator = MatchValidator()

    home_team, away_team = validator.validate_and_split(
        "  Arsenal   -   Chelsea  ",
        1,
    )

    assert home_team == "Arsenal"
    assert away_team == "Chelsea"


def test_validator_accepts_hyphen_inside_team_name() -> None:
    validator = MatchValidator()

    home_team, away_team = validator.validate_and_split(
        "Paris Saint-Germain - Marseille",
        1,
    )

    assert home_team == "Paris Saint-Germain"
    assert away_team == "Marseille"


def test_validator_accepts_structured_team_names() -> None:
    validator = MatchValidator()

    home_team, away_team = validator.validate_teams(
        "  Arsenal  ",
        "  Chelsea  ",
        1,
    )

    assert home_team == "Arsenal"
    assert away_team == "Chelsea"


def test_validator_rejects_non_string_team_name() -> None:
    validator = MatchValidator()

    with pytest.raises(
        TypeError,
        match="Home team must be a string",
    ):
        validator.validate_teams(
            123,
            "Chelsea",
            1,
        )


def test_validator_rejects_missing_separator() -> None:
    validator = MatchValidator()

    with pytest.raises(ValueError, match="Invalid match format"):
        validator.validate_and_split("Arsenal Chelsea", 1)


def test_validator_rejects_empty_home_team() -> None:
    validator = MatchValidator()

    with pytest.raises(ValueError, match="Home team must not be empty"):
        validator.validate_and_split(" - Chelsea", 1)


def test_validator_rejects_empty_away_team() -> None:
    validator = MatchValidator()

    with pytest.raises(ValueError, match="Away team must not be empty"):
        validator.validate_and_split("Arsenal - ", 1)


def test_validator_rejects_empty_line() -> None:
    validator = MatchValidator()

    with pytest.raises(ValueError, match="Match line must not be empty"):
        validator.validate_and_split("", 1)


def test_validator_rejects_non_positive_match_number() -> None:
    validator = MatchValidator()

    with pytest.raises(ValueError, match="greater than zero"):
        validator.validate_and_split("Arsenal - Chelsea", 0)