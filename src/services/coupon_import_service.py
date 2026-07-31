"""Service for importing and validating football pool coupons."""

from datetime import datetime
from pathlib import Path

from src.importer.importer_protocol import CouponImporter
from src.models.coupon import Coupon
from src.models.game_type import GameType
from src.validators.coupon_validator import CouponValidator


class CouponImportService:
    """Coordinates coupon import and coupon validation."""

    def __init__(
        self,
        importer: CouponImporter,
        validator: CouponValidator | None = None,
    ) -> None:
        """Create the service with an importer and validator."""

        self._importer = importer
        self._validator = validator or CouponValidator()

    def import_coupon(
        self,
        source_reference: str | Path,
        *,
        game_type: GameType = GameType.UNKNOWN,
        coupon_id: str | None = None,
        deadline: datetime | None = None,
    ) -> Coupon:
        """Import, validate and return a coupon."""

        coupon = self._importer.load_coupon(
            source_reference,
            game_type=game_type,
            coupon_id=coupon_id,
            deadline=deadline,
        )

        self._validator.validate(coupon)

        return coupon