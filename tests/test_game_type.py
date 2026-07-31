"""Tests for supported football pool game types."""

import pytest

from src.models.game_type import GameType


@pytest.mark.parametrize(
    ("game_type", "expected_count"),
    [
        (GameType.TOPPTIPSET, 8),
        (GameType.STRYKTIPSET, 13),
        (GameType.EUROPATIPSET, 13),
    ],
)
def test_game_type_expected_match_count(
    game_type: GameType,
    expected_count: int,
) -> None:
    assert game_type.expected_match_count == expected_count


def test_unknown_game_type_has_no_expected_match_count() -> None:
    assert GameType.UNKNOWN.expected_match_count is None


def test_game_types_have_human_readable_names() -> None:
    assert GameType.TOPPTIPSET.display_name == "Topptipset"
    assert GameType.STRYKTIPSET.display_name == "Stryktipset"
    assert GameType.EUROPATIPSET.display_name == "Europatipset"