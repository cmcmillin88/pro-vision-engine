"""Coupon model for Pro Vision Engine."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.models.match import Match


def current_utc_time() -> datetime:
    """Return the current timezone-aware UTC time."""

    return datetime.now(timezone.utc)


@dataclass(slots=True)
class Coupon:
    """Represents an imported football pool coupon."""

    matches: list[Match] = field(default_factory=list)
    game_type: GameType = GameType.UNKNOWN
    source: ImportSource = ImportSource.MANUAL
    coupon_id: str | None = None
    deadline: datetime | None = None
    imported_at: datetime = field(default_factory=current_utc_time)

    def add_match(self, match: Match) -> None:
        """Add a match to the coupon."""

        self.matches.append(match)

    @property
    def expected_match_count(self) -> int | None:
        """Return the expected match count for this coupon."""

        return self.game_type.expected_match_count

    def __len__(self) -> int:
        """Return the number of matches in the coupon."""

        return len(self.matches)

    def __str__(self) -> str:
        """Return a human-readable coupon representation."""

        header_lines = [
            "=" * 30,
            "Coupon",
            "=" * 30,
            f"Game type : {self.game_type.display_name}",
            f"Source    : {self.source.display_name}",
        ]

        if self.coupon_id is not None:
            header_lines.append(f"Coupon ID : {self.coupon_id}")

        if self.deadline is not None:
            header_lines.append(
                f"Deadline  : {self.deadline.isoformat()}"
            )

        header = "\n".join(header_lines)

        if self.matches:
            match_text = "\n\n".join(
                str(match) for match in self.matches
            )
        else:
            match_text = "No matches imported."

        return (
            f"{header}\n\n"
            f"{match_text}\n\n"
            f"Total matches: {len(self)}"
        )