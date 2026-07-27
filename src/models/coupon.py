"""
Coupon model for Pro Vision Engine.
"""

from dataclasses import dataclass, field

from src.models.match import Match


@dataclass(slots=True)
class Coupon:
    """Represents a betting coupon."""

    matches: list[Match] = field(default_factory=list)

    def add_match(self, match: Match) -> None:
        """Add a match to the coupon."""
        self.matches.append(match)

    def __len__(self) -> int:
        return len(self.matches)

    def __str__(self) -> str:
        lines = [
            "==============================",
            "Coupon",
            "=============================="
        ]

        for match in self.matches:
            lines.append(str(match))
            lines.append("")

        lines.append(f"Total matches: {len(self.matches)}")

        return "\n".join(lines)