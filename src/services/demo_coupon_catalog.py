"""Catalog service for local demonstration coupons."""

from pathlib import Path

from src.importer.svenska_spel_importer import (
    SvenskaSpelImporter,
)
from src.models.coupon import Coupon
from src.providers.svenska_spel.json_client import (
    SvenskaSpelJsonClient,
)
from src.services.coupon_import_service import (
    CouponImportService,
)


class DemoCouponNotFoundError(ValueError):
    """Raised when a requested demonstration coupon does not exist."""


class DemoCouponCatalog:
    """Provides validated local demonstration coupons."""

    _coupon_files = {
        "topptipset": "topptipset.json",
        "stryktipset": "stryktipset.json",
        "europatipset": "europatipset.json",
    }

    def __init__(
        self,
        coupon_directory: str | Path,
        import_service: CouponImportService | None = None,
    ) -> None:
        """Create the catalog for a local coupon directory."""

        self._coupon_directory = Path(coupon_directory)

        if import_service is None:
            client = SvenskaSpelJsonClient()
            importer = SvenskaSpelImporter(client)
            import_service = CouponImportService(importer)

        self._import_service = import_service

    @property
    def available_game_types(self) -> tuple[str, ...]:
        """Return all available demonstration game types."""

        return tuple(self._coupon_files)

    def load(
        self,
        game_type_name: str,
    ) -> Coupon:
        """Load and validate one demonstration coupon."""

        normalized_name = self._normalize_game_type_name(
            game_type_name
        )

        try:
            filename = self._coupon_files[normalized_name]
        except KeyError as error:
            available_names = ", ".join(
                self.available_game_types
            )

            raise DemoCouponNotFoundError(
                f"Unknown demonstration game type "
                f"{game_type_name!r}. "
                f"Available game types: {available_names}."
            ) from error

        coupon_file = (
            self._coupon_directory
            / filename
        )

        return self._import_service.import_coupon(
            coupon_file
        )

    @staticmethod
    def _normalize_game_type_name(
        game_type_name: str,
    ) -> str:
        """Normalize a game type supplied by a user or API client."""

        if not isinstance(game_type_name, str):
            raise TypeError(
                "Game type name must be a string."
            )

        return (
            game_type_name
            .strip()
            .casefold()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )