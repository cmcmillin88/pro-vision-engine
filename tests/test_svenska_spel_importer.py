"""Tests for the Svenska Spel coupon importer."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.importer.importer_protocol import CouponImporter
from src.importer.svenska_spel_importer import (
    SvenskaSpelImporter,
    SvenskaSpelImportError,
)
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.providers.svenska_spel.models import (
    SvenskaSpelCouponData,
    SvenskaSpelMatchData,
)
from src.services.coupon_import_service import CouponImportService


class FakeSvenskaSpelClient:
    """Test client that returns prepared Svenska Spel data."""

    def __init__(
        self,
        coupon_data: SvenskaSpelCouponData,
    ) -> None:
        self.coupon_data = coupon_data
        self.received_reference: str | Path | None = None

    def fetch_coupon(
        self,
        source_reference: str | Path,
    ) -> SvenskaSpelCouponData:
        """Record the source and return prepared data."""

        self.received_reference = source_reference

        return self.coupon_data


def create_topptipset_data() -> SvenskaSpelCouponData:
    """Create complete Svenska Spel Topptipset test data."""

    deadline = datetime(
        2026,
        8,
        1,
        15,
        0,
        tzinfo=timezone.utc,
    )

    matches = tuple(
        SvenskaSpelMatchData(
            match_number=match_number,
            home_team=f"Home Team {match_number}",
            away_team=f"Away Team {match_number}",
            competition="Test League",
        )
        for match_number in range(1, 9)
    )

    return SvenskaSpelCouponData(
        game_type="Topptipset",
        coupon_id="TT-SVENSKA-SPEL-001",
        deadline=deadline,
        matches=matches,
    )


def test_svenska_spel_importer_creates_coupon() -> None:
    provider_data = create_topptipset_data()
    client = FakeSvenskaSpelClient(provider_data)
    importer = SvenskaSpelImporter(client)

    coupon = importer.load_coupon(
        "svenska-spel://topptipset/current"
    )

    assert client.received_reference == (
        "svenska-spel://topptipset/current"
    )

    assert coupon.game_type is GameType.TOPPTIPSET
    assert coupon.source is ImportSource.SVENSKA_SPEL
    assert coupon.coupon_id == "TT-SVENSKA-SPEL-001"
    assert coupon.deadline == provider_data.deadline
    assert len(coupon) == 8

    assert coupon.matches[0].match_number == 1
    assert coupon.matches[0].home_team == "Home Team 1"
    assert coupon.matches[0].away_team == "Away Team 1"
    assert coupon.matches[0].competition == "Test League"


def test_svenska_spel_importer_satisfies_importer_protocol() -> None:
    client = FakeSvenskaSpelClient(
        create_topptipset_data()
    )

    importer = SvenskaSpelImporter(client)

    assert isinstance(importer, CouponImporter)


def test_svenska_spel_importer_allows_metadata_overrides() -> None:
    provider_data = create_topptipset_data()
    client = FakeSvenskaSpelClient(provider_data)
    importer = SvenskaSpelImporter(client)

    override_deadline = datetime(
        2026,
        8,
        1,
        16,
        0,
        tzinfo=timezone.utc,
    )

    coupon = importer.load_coupon(
        "svenska-spel://topptipset/current",
        game_type=GameType.TOPPTIPSET,
        coupon_id="OVERRIDE-ID",
        deadline=override_deadline,
    )

    assert coupon.game_type is GameType.TOPPTIPSET
    assert coupon.coupon_id == "OVERRIDE-ID"
    assert coupon.deadline == override_deadline


def test_svenska_spel_importer_rejects_unknown_game_type() -> None:
    provider_data = SvenskaSpelCouponData(
        game_type="Unknown Game",
        matches=(),
    )

    client = FakeSvenskaSpelClient(provider_data)
    importer = SvenskaSpelImporter(client)

    with pytest.raises(
        SvenskaSpelImportError,
        match="Unsupported Svenska Spel game type",
    ):
        importer.load_coupon(
            "svenska-spel://unknown"
        )


def test_import_service_accepts_svenska_spel_importer() -> None:
    client = FakeSvenskaSpelClient(
        create_topptipset_data()
    )

    importer = SvenskaSpelImporter(client)
    service = CouponImportService(importer)

    coupon = service.import_coupon(
        "svenska-spel://topptipset/current"
    )

    assert coupon.source is ImportSource.SVENSKA_SPEL
    assert coupon.game_type is GameType.TOPPTIPSET
    assert len(coupon) == 8