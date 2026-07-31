"""Structured data models returned by a Svenska Spel client."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SvenskaSpelMatchData:
    """Represents one match received from Svenska Spel."""

    match_number: int
    home_team: str
    away_team: str
    competition: str | None = None
    kickoff: datetime | None = None


@dataclass(frozen=True, slots=True)
class SvenskaSpelCouponData:
    """Represents coupon data received from Svenska Spel."""

    game_type: str
    matches: tuple[SvenskaSpelMatchData, ...]
    coupon_id: str | None = None
    deadline: datetime | None = None