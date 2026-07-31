"""Registry for available coupon data sources."""

from collections.abc import Iterable

from src.models.coupon import Coupon
from src.services.coupon_catalog_protocol import (
    CouponCatalog,
)


class CouponSourceNotFoundError(LookupError):
    """Raised when a requested coupon source is unavailable."""


class DuplicateCouponSourceError(ValueError):
    """Raised when multiple sources use the same source name."""


class CouponSourceRegistry:
    """Stores and resolves provider-independent coupon sources."""

    def __init__(
        self,
        catalogs: Iterable[CouponCatalog],
        *,
        default_source_name: str | None = None,
    ) -> None:
        """Create a registry containing one or more catalogs."""

        resolved_catalogs = tuple(catalogs)

        if not resolved_catalogs:
            raise ValueError(
                "CouponSourceRegistry requires "
                "at least one coupon catalog."
            )

        self._catalogs: dict[str, CouponCatalog] = {}
        self._source_names: list[str] = []

        for catalog in resolved_catalogs:
            self._register_catalog(
                catalog
            )

        if default_source_name is None:
            first_source_name = self._source_names[0]
            default_key = self._normalize_source_name(
                first_source_name
            )
        else:
            default_key = self._normalize_source_name(
                default_source_name
            )

        if default_key not in self._catalogs:
            raise CouponSourceNotFoundError(
                self._unknown_source_message(
                    default_source_name
                )
            )

        self._default_key = default_key

    @property
    def available_sources(self) -> tuple[str, ...]:
        """Return all registered source names."""

        return tuple(
            self._source_names
        )

    @property
    def default_source_name(self) -> str:
        """Return the configured default source name."""

        return self._catalogs[
            self._default_key
        ].source_name

    def get_catalog(
        self,
        source_name: str | None = None,
    ) -> CouponCatalog:
        """Return a catalog by source name."""

        if source_name is None:
            source_key = self._default_key
        else:
            source_key = self._normalize_source_name(
                source_name
            )

        try:
            return self._catalogs[
                source_key
            ]
        except KeyError as error:
            raise CouponSourceNotFoundError(
                self._unknown_source_message(
                    source_name
                )
            ) from error

    def available_game_types(
        self,
        source_name: str | None = None,
    ) -> tuple[str, ...]:
        """Return game types available from one source."""

        catalog = self.get_catalog(
            source_name
        )

        return catalog.available_game_types

    def load(
        self,
        game_type_name: str,
        *,
        source_name: str | None = None,
    ) -> Coupon:
        """Load one coupon from the resolved source."""

        catalog = self.get_catalog(
            source_name
        )

        return catalog.load(
            game_type_name
        )

    def _register_catalog(
        self,
        catalog: CouponCatalog,
    ) -> None:
        """Validate and register one coupon catalog."""

        if not isinstance(
            catalog,
            CouponCatalog,
        ):
            raise TypeError(
                "Registered sources must satisfy "
                "the CouponCatalog protocol."
            )

        source_key = self._normalize_source_name(
            catalog.source_name
        )

        if source_key in self._catalogs:
            raise DuplicateCouponSourceError(
                f"Coupon source "
                f"{catalog.source_name!r} "
                "has already been registered."
            )

        self._catalogs[
            source_key
        ] = catalog
        self._source_names.append(
            catalog.source_name
        )

    def _unknown_source_message(
        self,
        source_name: str | None,
    ) -> str:
        """Create a helpful unknown-source message."""

        available_names = ", ".join(
            self.available_sources
        )

        return (
            f"Unknown coupon source "
            f"{source_name!r}. "
            f"Available sources: "
            f"{available_names}."
        )

    @staticmethod
    def _normalize_source_name(
        source_name: str,
    ) -> str:
        """Normalize a source name for reliable lookup."""

        if not isinstance(
            source_name,
            str,
        ):
            raise TypeError(
                "Coupon source name "
                "must be a string."
            )

        normalized_name = (
            source_name
            .strip()
            .casefold()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )

        if not normalized_name:
            raise ValueError(
                "Coupon source name "
                "must not be empty."
            )

        return normalized_name