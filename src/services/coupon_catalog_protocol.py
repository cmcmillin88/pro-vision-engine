"""Shared contract for coupon catalog services."""

from typing import Protocol, runtime_checkable

from src.models.coupon import Coupon


class CouponNotFoundError(LookupError):
    """Raised when a requested coupon does not exist."""


@runtime_checkable
class CouponCatalog(Protocol):
    """Defines the behavior required from a coupon source."""

    @property
    def source_name(self) -> str:
        """Return the machine-readable source name."""

        ...

    @property
    def source_display_name(self) -> str:
        """Return the human-readable source name."""

        ...

    @property
    def is_live(self) -> bool:
        """Return whether the source provides live data."""

        ...

    @property
    def available_game_types(self) -> tuple[str, ...]:
        """Return the game types available from the source."""

        ...

    def load(
        self,
        game_type_name: str,
    ) -> Coupon:
        """Load one coupon from the source."""

        ...