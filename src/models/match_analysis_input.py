"""Input model for one complete football match analysis."""

from dataclasses import dataclass

from src.models.market_snapshot import MarketSnapshot
from src.models.team_match_performance import (
    TeamMatchPerformance,
)


@dataclass(frozen=True, slots=True)
class MatchAnalysisInput:
    """Contains all data required for one complete match analysis."""

    home_team_name: str
    away_team_name: str
    home_performances: tuple[
        TeamMatchPerformance,
        ...,
    ]
    away_performances: tuple[
        TeamMatchPerformance,
        ...,
    ]
    earlier_market_snapshot: MarketSnapshot
    later_market_snapshot: MarketSnapshot
    match_reference: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the complete analysis input."""

        normalized_home_team = self._normalize_required_text(
            self.home_team_name,
            field_name="home_team_name",
        )
        normalized_away_team = self._normalize_required_text(
            self.away_team_name,
            field_name="away_team_name",
        )

        if (
            normalized_home_team.casefold()
            == normalized_away_team.casefold()
        ):
            raise ValueError(
                "Home and away teams must be different."
            )

        object.__setattr__(
            self,
            "home_team_name",
            normalized_home_team,
        )
        object.__setattr__(
            self,
            "away_team_name",
            normalized_away_team,
        )

        self._validate_performances(
            self.home_performances,
            field_name="home_performances",
            expected_team_name=normalized_home_team,
        )
        self._validate_performances(
            self.away_performances,
            field_name="away_performances",
            expected_team_name=normalized_away_team,
        )

        if not isinstance(
            self.earlier_market_snapshot,
            MarketSnapshot,
        ):
            raise TypeError(
                "earlier_market_snapshot must be "
                "a MarketSnapshot."
            )

        if not isinstance(
            self.later_market_snapshot,
            MarketSnapshot,
        ):
            raise TypeError(
                "later_market_snapshot must be "
                "a MarketSnapshot."
            )

        if self.match_reference is not None:
            normalized_reference = (
                self._normalize_required_text(
                    self.match_reference,
                    field_name="match_reference",
                )
            )

            object.__setattr__(
                self,
                "match_reference",
                normalized_reference,
            )

    @property
    def home_performance_count(self) -> int:
        """Return supplied home-team performance count."""

        return len(
            self.home_performances
        )

    @property
    def away_performance_count(self) -> int:
        """Return supplied away-team performance count."""

        return len(
            self.away_performances
        )

    @staticmethod
    def _validate_performances(
        performances: object,
        *,
        field_name: str,
        expected_team_name: str,
    ) -> None:
        """Validate one immutable performance collection."""

        if not isinstance(
            performances,
            tuple,
        ):
            raise TypeError(
                f"{field_name} must be a tuple."
            )

        if not performances:
            raise ValueError(
                f"{field_name} must not be empty."
            )

        for performance in performances:
            if not isinstance(
                performance,
                TeamMatchPerformance,
            ):
                raise TypeError(
                    f"{field_name} may only contain "
                    "TeamMatchPerformance objects."
                )

            if (
                performance.team_name.casefold()
                != expected_team_name.casefold()
            ):
                raise ValueError(
                    f"All {field_name} must belong "
                    f"to {expected_team_name}."
                )

    @staticmethod
    def _normalize_required_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """Normalize one required text value."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized_value = " ".join(
            value.split()
        )

        if not normalized_value:
            raise ValueError(
                f"{field_name} must not be empty."
            )

        return normalized_value