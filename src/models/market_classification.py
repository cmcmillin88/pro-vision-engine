"""Market classification models for football pool analysis."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.models.market_alert import MarketAlertReport
from src.models.market_value import MarketValueAnalysis
from src.models.outcome import Outcome


class MarketRole(str, Enum):
    """Describes one analytical role for a 1-X-2 outcome."""

    MARKET_FAVORITE = "market_favorite"
    PUBLIC_FAVORITE = "public_favorite"
    VALUE_PLAY = "value_play"
    PUBLIC_TRAP = "public_trap"
    ODDS_STEAM = "odds_steam"
    PUBLIC_SURGE = "public_surge"
    VALUE_EROSION = "value_erosion"
    CONTRARIAN_VALUE = "contrarian_value"

    @property
    def display_name(self) -> str:
        """Return a human-readable market role."""

        names = {
            MarketRole.MARKET_FAVORITE: "Market favorite",
            MarketRole.PUBLIC_FAVORITE: "Public favorite",
            MarketRole.VALUE_PLAY: "Value play",
            MarketRole.PUBLIC_TRAP: "Public trap",
            MarketRole.ODDS_STEAM: "Odds steam",
            MarketRole.PUBLIC_SURGE: "Public surge",
            MarketRole.VALUE_EROSION: "Value erosion",
            MarketRole.CONTRARIAN_VALUE: "Contrarian value",
        }

        return names[self]


@dataclass(frozen=True, slots=True)
class OutcomeMarketProfile:
    """Contains all market classifications for one outcome."""

    outcome: Outcome
    market_probability: Decimal
    public_percentage: Decimal
    edge_percentage_points: Decimal
    value_index: Decimal | None
    roles: tuple[MarketRole, ...]

    def __post_init__(self) -> None:
        """Validate one classified outcome profile."""

        if not isinstance(
            self.outcome,
            Outcome,
        ):
            raise TypeError(
                "OutcomeMarketProfile outcome "
                "must be an Outcome."
            )

        for field_name in (
            "market_probability",
            "public_percentage",
            "edge_percentage_points",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                Decimal,
            ):
                raise TypeError(
                    f"{field_name} must be a Decimal."
                )

            if not value.is_finite():
                raise ValueError(
                    f"{field_name} must be finite."
                )

        for field_name in (
            "market_probability",
            "public_percentage",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not Decimal("0") <= value <= Decimal("100"):
                raise ValueError(
                    f"{field_name} must be between 0 and 100."
                )

        if self.value_index is not None:
            if not isinstance(
                self.value_index,
                Decimal,
            ):
                raise TypeError(
                    "value_index must be a Decimal or None."
                )

            if not self.value_index.is_finite():
                raise ValueError(
                    "value_index must be finite."
                )

            if self.value_index < Decimal("0"):
                raise ValueError(
                    "value_index must not be negative."
                )

        if not isinstance(
            self.roles,
            tuple,
        ):
            raise TypeError(
                "OutcomeMarketProfile roles "
                "must be a tuple."
            )

        for role in self.roles:
            if not isinstance(
                role,
                MarketRole,
            ):
                raise TypeError(
                    "OutcomeMarketProfile roles may only "
                    "contain MarketRole values."
                )

        if len(set(self.roles)) != len(self.roles):
            raise ValueError(
                "OutcomeMarketProfile roles "
                "must not contain duplicates."
            )

    def has_role(
        self,
        role: MarketRole,
    ) -> bool:
        """Return whether the profile has one market role."""

        if not isinstance(
            role,
            MarketRole,
        ):
            raise TypeError(
                "Role must be a MarketRole."
            )

        return role in self.roles

    @property
    def is_value_play(self) -> bool:
        """Return whether the outcome is classified as value."""

        return self.has_role(
            MarketRole.VALUE_PLAY
        )

    @property
    def is_public_trap(self) -> bool:
        """Return whether the outcome is a public trap."""

        return self.has_role(
            MarketRole.PUBLIC_TRAP
        )


@dataclass(frozen=True, slots=True)
class MarketClassificationReport:
    """Complete market classification for one match."""

    value_analysis: MarketValueAnalysis
    alert_report: MarketAlertReport | None
    profiles: tuple[OutcomeMarketProfile, ...]

    def __post_init__(self) -> None:
        """Validate the complete classification report."""

        if not isinstance(
            self.value_analysis,
            MarketValueAnalysis,
        ):
            raise TypeError(
                "MarketClassificationReport value_analysis "
                "must be a MarketValueAnalysis."
            )

        if (
            self.alert_report is not None
            and not isinstance(
                self.alert_report,
                MarketAlertReport,
            )
        ):
            raise TypeError(
                "MarketClassificationReport alert_report "
                "must be a MarketAlertReport or None."
            )

        if not isinstance(
            self.profiles,
            tuple,
        ):
            raise TypeError(
                "MarketClassificationReport profiles "
                "must be a tuple."
            )

        outcome_order = tuple(
            profile.outcome
            for profile in self.profiles
        )

        if outcome_order != Outcome.ordered():
            raise ValueError(
                "Market profiles must follow "
                "official 1-X-2 order."
            )

        market_favorite_count = sum(
            profile.has_role(
                MarketRole.MARKET_FAVORITE
            )
            for profile in self.profiles
        )
        public_favorite_count = sum(
            profile.has_role(
                MarketRole.PUBLIC_FAVORITE
            )
            for profile in self.profiles
        )

        if market_favorite_count != 1:
            raise ValueError(
                "A classification report must contain "
                "exactly one market favorite."
            )

        if public_favorite_count != 1:
            raise ValueError(
                "A classification report must contain "
                "exactly one public favorite."
            )

        for profile in self.profiles:
            outcome_value = (
                self.value_analysis.for_outcome(
                    profile.outcome
                )
            )

            if (
                profile.market_probability
                != outcome_value.market_probability
                or profile.public_percentage
                != outcome_value.public_percentage
                or profile.edge_percentage_points
                != outcome_value.edge_percentage_points
                or profile.value_index
                != outcome_value.value_index
            ):
                raise ValueError(
                    "Market profile values must match "
                    "the supplied value analysis."
                )

        if (
            self.alert_report is not None
            and (
                self.alert_report
                .movement_analysis
                .later_value_analysis
                != self.value_analysis
            )
        ):
            raise ValueError(
                "Alert report must describe the same "
                "latest value analysis."
            )

    def for_outcome(
        self,
        outcome: Outcome,
    ) -> OutcomeMarketProfile:
        """Return the profile for one outcome."""

        resolved_outcome = Outcome.parse(
            outcome
        )

        for profile in self.profiles:
            if profile.outcome is resolved_outcome:
                return profile

        raise LookupError(
            f"No market profile exists for "
            f"{resolved_outcome.value}."
        )

    @property
    def market_favorite(
        self,
    ) -> OutcomeMarketProfile:
        """Return the odds market's favorite."""

        return self._profile_with_role(
            MarketRole.MARKET_FAVORITE
        )

    @property
    def public_favorite(
        self,
    ) -> OutcomeMarketProfile:
        """Return the most selected public outcome."""

        return self._profile_with_role(
            MarketRole.PUBLIC_FAVORITE
        )

    @property
    def best_value(
        self,
    ) -> OutcomeMarketProfile:
        """Return the outcome with the strongest edge."""

        return max(
            self.profiles,
            key=lambda profile: (
                profile.edge_percentage_points
            ),
        )

    @property
    def market_and_public_agree(self) -> bool:
        """Return whether market and public favorites agree."""

        return (
            self.market_favorite.outcome
            is self.public_favorite.outcome
        )

    @property
    def value_plays(
        self,
    ) -> tuple[OutcomeMarketProfile, ...]:
        """Return all outcomes classified as value plays."""

        return tuple(
            profile
            for profile in self.profiles
            if profile.is_value_play
        )

    @property
    def public_traps(
        self,
    ) -> tuple[OutcomeMarketProfile, ...]:
        """Return all outcomes classified as public traps."""

        return tuple(
            profile
            for profile in self.profiles
            if profile.is_public_trap
        )

    def _profile_with_role(
        self,
        role: MarketRole,
    ) -> OutcomeMarketProfile:
        """Return the unique profile with one role."""

        for profile in self.profiles:
            if profile.has_role(role):
                return profile

        raise LookupError(
            f"No market profile has role {role.value}."
        )