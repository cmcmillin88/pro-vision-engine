"""Time-stamped market data for one football match."""

from dataclasses import dataclass
from datetime import datetime

from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """Represents odds and public percentages at one moment."""

    captured_at: datetime
    odds: ThreeWayOdds
    public_percentages: ThreeWayPercentages
    source_name: str = "combined-market"

    def __post_init__(self) -> None:
        """Validate and normalize the market snapshot."""

        if not isinstance(
            self.captured_at,
            datetime,
        ):
            raise TypeError(
                "MarketSnapshot captured_at "
                "must be a datetime."
            )

        if (
            self.captured_at.tzinfo is None
            or self.captured_at.utcoffset() is None
        ):
            raise ValueError(
                "MarketSnapshot captured_at "
                "must include timezone information."
            )

        if not isinstance(
            self.odds,
            ThreeWayOdds,
        ):
            raise TypeError(
                "MarketSnapshot odds "
                "must be ThreeWayOdds."
            )

        if not isinstance(
            self.public_percentages,
            ThreeWayPercentages,
        ):
            raise TypeError(
                "MarketSnapshot public percentages "
                "must be ThreeWayPercentages."
            )

        if not isinstance(
            self.source_name,
            str,
        ):
            raise TypeError(
                "MarketSnapshot source name "
                "must be a string."
            )

        normalized_source_name = (
            self.source_name.strip()
        )

        if not normalized_source_name:
            raise ValueError(
                "MarketSnapshot source name "
                "must not be empty."
            )

        object.__setattr__(
            self,
            "source_name",
            normalized_source_name,
        )