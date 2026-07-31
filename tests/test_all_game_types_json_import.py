"""Integration tests for all supported JSON coupon types."""

import json
from pathlib import Path
from typing import cast

import pytest

from src.importer.svenska_spel_importer import (
    SvenskaSpelImporter,
)
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.providers.svenska_spel.json_client import (
    SvenskaSpelJsonClient,
)
from src.services.coupon_import_service import (
    CouponImportService,
)
from src.validators.coupon_validator import (
    CouponValidationError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIRECTORY = (
    PROJECT_ROOT
    / "examples"
    / "svenska_spel"
)


def create_import_service() -> CouponImportService:
    """Create the complete local JSON import service."""

    client = SvenskaSpelJsonClient()
    importer = SvenskaSpelImporter(client)

    return CouponImportService(importer)


def create_payload(
    *,
    game_type: str = "Topptipset",
    match_count: int = 8,
) -> dict[str, object]:
    """Create structured coupon JSON test data."""

    matches: list[dict[str, object]] = [
        {
            "match_number": match_number,
            "home_team": f"Home Team {match_number}",
            "away_team": f"Away Team {match_number}",
            "competition": "Test League",
            "kickoff": "2026-08-01T16:00:00+02:00",
        }
        for match_number in range(1, match_count + 1)
    ]

    return {
        "game_type": game_type,
        "coupon_id": "TEST-COUPON-001",
        "deadline": "2026-08-01T15:00:00+02:00",
        "matches": matches,
    }


def write_payload(
    path: Path,
    payload: dict[str, object],
) -> None:
    """Write structured coupon data to a JSON file."""

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    (
        "filename",
        "expected_game_type",
        "expected_match_count",
    ),
    [
        (
            "topptipset.json",
            GameType.TOPPTIPSET,
            8,
        ),
        (
            "stryktipset.json",
            GameType.STRYKTIPSET,
            13,
        ),
        (
            "europatipset.json",
            GameType.EUROPATIPSET,
            13,
        ),
    ],
)
def test_example_coupon_imports_successfully(
    filename: str,
    expected_game_type: GameType,
    expected_match_count: int,
) -> None:
    service = create_import_service()

    coupon = service.import_coupon(
        EXAMPLE_DIRECTORY / filename
    )

    assert coupon.game_type is expected_game_type
    assert coupon.source is ImportSource.SVENSKA_SPEL
    assert len(coupon) == expected_match_count
    assert coupon.expected_match_count == expected_match_count


def test_unknown_json_fields_are_ignored(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "extra-fields.json"
    payload = create_payload()

    payload["provider_version"] = "1.0"
    payload["unexpected_coupon_field"] = {
        "ignored": True,
    }

    matches = cast(
        list[dict[str, object]],
        payload["matches"],
    )
    matches[0]["unexpected_match_field"] = "ignored"

    write_payload(
        coupon_file,
        payload,
    )

    service = create_import_service()
    coupon = service.import_coupon(coupon_file)

    assert coupon.game_type is GameType.TOPPTIPSET
    assert len(coupon) == 8


def test_incomplete_topptipset_is_rejected(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "incomplete.json"

    write_payload(
        coupon_file,
        create_payload(
            match_count=7,
        ),
    )

    service = create_import_service()

    with pytest.raises(
        CouponValidationError,
        match="requires exactly 8 matches",
    ):
        service.import_coupon(coupon_file)


def test_duplicate_match_numbers_are_rejected(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "duplicates.json"
    payload = create_payload()

    matches = cast(
        list[dict[str, object]],
        payload["matches"],
    )
    matches[-1]["match_number"] = 1

    write_payload(
        coupon_file,
        payload,
    )

    service = create_import_service()

    with pytest.raises(
        CouponValidationError,
        match="must be unique",
    ):
        service.import_coupon(coupon_file)


def test_incorrect_match_order_is_rejected(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "incorrect-order.json"
    payload = create_payload()

    matches = cast(
        list[dict[str, object]],
        payload["matches"],
    )
    matches[0], matches[1] = (
        matches[1],
        matches[0],
    )

    write_payload(
        coupon_file,
        payload,
    )

    service = create_import_service()

    with pytest.raises(
        CouponValidationError,
        match="sequential and ordered",
    ):
        service.import_coupon(coupon_file)