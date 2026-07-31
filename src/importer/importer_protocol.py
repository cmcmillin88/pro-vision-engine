"""Common contract for coupon importers."""

from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from src.models.coupon import Coupon
from src.models.game_type import GameType


@runtime_checkable
class CouponImporter(Protocol):
    """Defines the required behavior for coupon importers."""

    def load_coupon(
        self,
        source_reference: str | Path,
        *,
        game_type: GameType = GameType.UNKNOWN,
        coupon_id: str | None = None,
        deadline: datetime | None = None,
    ) -> Coupon:
        """Load a coupon from a source reference."""

        ...