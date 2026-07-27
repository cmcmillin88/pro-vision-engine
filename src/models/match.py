"""
Match model for Pro Vision Engine.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Match:
    """Represents a football match."""

    match_number: int
    home_team: str
    away_team: str
    competition: Optional[str] = None
    kickoff: Optional[datetime] = None
    status: str = "NEW"

    def __str__(self) -> str:
        return (
            f"⚽ Match {self.match_number}\n"
            f"Home Team : {self.home_team}\n"
            f"Away Team : {self.away_team}\n"
            f"Status    : {self.status}"
        )