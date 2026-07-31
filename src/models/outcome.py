"""Football pool outcomes for 1-X-2 markets."""

from __future__ import annotations

from enum import Enum


class Outcome(str, Enum):
    """Represents one possible result in a 1-X-2 market."""

    HOME = "1"
    DRAW = "X"
    AWAY = "2"

    @property
    def display_name(self) -> str:
        """Return a human-readable outcome name."""

        names = {
            Outcome.HOME: "Home win",
            Outcome.DRAW: "Draw",
            Outcome.AWAY: "Away win",
        }

        return names[self]

    @classmethod
    def ordered(cls) -> tuple[Outcome, ...]:
        """Return outcomes in official 1-X-2 order."""

        return (
            cls.HOME,
            cls.DRAW,
            cls.AWAY,
        )

    @classmethod
    def parse(
        cls,
        value: str | Outcome,
    ) -> Outcome:
        """Convert a symbol into an Outcome value."""

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "Outcome must be supplied as a string or Outcome."
            )

        normalized_value = value.strip().upper()

        try:
            return cls(normalized_value)
        except ValueError as error:
            raise ValueError(
                f"Unknown 1-X-2 outcome: {value!r}."
            ) from error