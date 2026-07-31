"""Tests for the coupon import service."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.models.coupon import Coupon
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.models.match import Match
from src.services.coupon_import_service import CouponImportService
from src.validators.coupon_validator import CouponValidationError


class FakeImporter:
    """Test importer that returns a prepared coupon."""

    def __init__(self, coupon: Coupon) -> None:
        self.coupon = coupon
        self.received_reference: str | Path | None = None
        self.received_game_type = GameType.UNKNOWN
        self.received_coupon_id: str | None = None
        self.received_deadline: datetime | None = None

    def load_coupon(
        self,
        source_reference: str | Path,
        *,
        game_type: GameType = GameType.UNKNOWN,
        coupon_id: str | None = None,
        deadline: datetime | None = None,
    ) -> Coupon:
        """Record the request and return the prepared coupon."""

        self.received_reference = source_reference
        self.received_game_type = game_type
        self.received_coupon_id = coupon_id
        self.received_deadline = deadline

        return self.coupon


def create_topptipset_coupon(
    match_count: int = 8,
) -> Coupon:
    """Create a Topptipset coupon for service tests."""

    coupon = Coupon(
        game_type=GameType.TOPPTIPSET,
        source=ImportSource.TEXT_FILE,
    )

    for match_number in range(1, match_count + 1):
        coupon.add_match(
            Match(
                match_number=match_number,
                home_team=f"Home Team {match_number}",
                away_team=f"Away Team {match_number}",
            )
        )

    return coupon


def test_service_imports_and_validates_coupon() -> None:
    coupon = create_topptipset_coupon()
    importer = FakeImporter(coupon)
    service = CouponImportService(importer)

    deadline = datetime(
        2026,
        8,
        1,
        15,
        0,
        tzinfo=timezone.utc,
    )

    result = service.import_coupon(
        "fake://topptipset",
        game_type=GameType.TOPPTIPSET,
        coupon_id="TT-TEST-001",
        deadline=deadline,
    )

    assert result is coupon
    assert importer.received_reference == "fake://topptipset"
    assert importer.received_game_type is GameType.TOPPTIPSET
    assert importer.received_coupon_id == "TT-TEST-001"
    assert importer.received_deadline == deadline


def test_service_rejects_invalid_coupon() -> None:
    coupon = create_topptipset_coupon(
        match_count=7,
    )

    importer = FakeImporter(coupon)
    service = CouponImportService(importer)

    with pytest.raises(
        CouponValidationError,
        match="requires exactly 8 matches",
    ):
        service.import_coupon(
            "fake://invalid-topptipset",
            game_type=GameType.TOPPTIPSET,
        )