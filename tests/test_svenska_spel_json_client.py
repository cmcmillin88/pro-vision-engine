"""Tests for the local Svenska Spel JSON client."""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from src.importer.svenska_spel_importer import (
    SvenskaSpelImporter,
)
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.providers.svenska_spel.client_protocol import (
    SvenskaSpelClient,
)
from src.providers.svenska_spel.json_client import (
    SvenskaSpelJsonClient,
    SvenskaSpelJsonClientError,
)
from src.services.coupon_import_service import (
    CouponImportService,
)


def create_valid_payload(
    match_count: int = 8,
) -> dict[str, object]:
    """Create valid Svenska Spel JSON test data."""

    matches = [
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
        "game_type": "Topptipset",
        "coupon_id": "TT-JSON-TEST-001",
        "deadline": "2026-08-01T15:00:00+02:00",
        "matches": matches,
    }


def write_payload(
    path: Path,
    payload: dict[str, object],
) -> None:
    """Write JSON test data to a file."""

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_json_client_loads_coupon_data(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "topptipset.json"

    write_payload(
        coupon_file,
        create_valid_payload(),
    )

    client = SvenskaSpelJsonClient()
    coupon_data = client.fetch_coupon(coupon_file)

    assert coupon_data.game_type == "Topptipset"
    assert coupon_data.coupon_id == "TT-JSON-TEST-001"
    assert coupon_data.deadline is not None
    assert coupon_data.deadline.utcoffset() == timedelta(
        hours=2
    )
    assert len(coupon_data.matches) == 8

    first_match = coupon_data.matches[0]

    assert first_match.match_number == 1
    assert first_match.home_team == "Home Team 1"
    assert first_match.away_team == "Away Team 1"
    assert first_match.competition == "Test League"
    assert first_match.kickoff is not None


def test_json_client_satisfies_client_protocol() -> None:
    client = SvenskaSpelJsonClient()

    assert isinstance(client, SvenskaSpelClient)


def test_json_client_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "invalid.json"

    coupon_file.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    client = SvenskaSpelJsonClient()

    with pytest.raises(
        SvenskaSpelJsonClientError,
        match="Invalid JSON",
    ):
        client.fetch_coupon(coupon_file)


def test_json_client_rejects_missing_game_type(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "missing-game-type.json"
    payload = create_valid_payload()
    del payload["game_type"]

    write_payload(
        coupon_file,
        payload,
    )

    client = SvenskaSpelJsonClient()

    with pytest.raises(
        SvenskaSpelJsonClientError,
        match="Missing required field: 'game_type'",
    ):
        client.fetch_coupon(coupon_file)


def test_json_client_rejects_non_list_matches(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "invalid-matches.json"
    payload = create_valid_payload()
    payload["matches"] = {}

    write_payload(
        coupon_file,
        payload,
    )

    client = SvenskaSpelJsonClient()

    with pytest.raises(
        SvenskaSpelJsonClientError,
        match="'matches' must be a list",
    ):
        client.fetch_coupon(coupon_file)


def test_json_client_rejects_datetime_without_timezone(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "invalid-deadline.json"
    payload = create_valid_payload()
    payload["deadline"] = "2026-08-01T15:00:00"

    write_payload(
        coupon_file,
        payload,
    )

    client = SvenskaSpelJsonClient()

    with pytest.raises(
        SvenskaSpelJsonClientError,
        match="must include a timezone",
    ):
        client.fetch_coupon(coupon_file)


def test_complete_json_import_chain(
    tmp_path: Path,
) -> None:
    coupon_file = tmp_path / "topptipset.json"

    write_payload(
        coupon_file,
        create_valid_payload(),
    )

    client = SvenskaSpelJsonClient()
    importer = SvenskaSpelImporter(client)
    service = CouponImportService(importer)

    coupon = service.import_coupon(coupon_file)

    assert coupon.game_type is GameType.TOPPTIPSET
    assert coupon.source is ImportSource.SVENSKA_SPEL
    assert coupon.coupon_id == "TT-JSON-TEST-001"
    assert coupon.deadline is not None
    assert len(coupon) == 8