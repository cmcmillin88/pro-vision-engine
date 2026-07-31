"""Supported football pool game types."""

from enum import Enum


class GameType(str, Enum):
    """Represents a football pool game type."""

    UNKNOWN = "unknown"
    TOPPTIPSET = "topptipset"
    STRYKTIPSET = "stryktipset"
    EUROPATIPSET = "europatipset"

    @property
    def display_name(self) -> str:
        """Return a human-readable game type name."""

        names = {
            GameType.UNKNOWN: "Unknown",
            GameType.TOPPTIPSET: "Topptipset",
            GameType.STRYKTIPSET: "Stryktipset",
            GameType.EUROPATIPSET: "Europatipset",
        }

        return names[self]

    @property
    def expected_match_count(self) -> int | None:
        """Return the expected number of matches for the game type."""

        if self is GameType.TOPPTIPSET:
            return 8

        if self in {
            GameType.STRYKTIPSET,
            GameType.EUROPATIPSET,
        }:
            return 13

        return None