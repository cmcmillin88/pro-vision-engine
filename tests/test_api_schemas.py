"""Tests for the Pro Vision Engine API schemas."""

from datetime import datetime
from typing import cast

import pytest
from pydantic import ValidationError

from src.api.schemas import (
    CouponListResponse,
    CouponResponse,
)


def create_coupon_payload() -> dict[str, object]:
    """Create a complete API coupon payload."""

    return {
        "schema_version": "1.0",
        "coupon": {
            "id": "TEST-TT-001",
            "game_type": "topptipset",
            "game_type_display": "Topptipset",
            "source": "svenska_spel",
            "source_display": "Svenska Spel",
            "deadline": "2026-08-01T15:00:00+02:00",
            "imported_at": "2026-07-31T12:00:00+00:00",
            "match_count": 8,
            "expected_match_count": 8,
        },
        "matches": [
            {
                "number": 1,
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "competition": "Premier League",
                "kickoff": "2026-08-01T16:00:00+02:00",
                "status": "NEW",
            }
        ],
    }


def test_coupon_response_validates_nested_payload() -> None:
    response = CouponResponse.model_validate(
        create_coupon_payload()
    )

    assert response.schema_version == "1.0"
    assert response.coupon.game_type == "topptipset"
    assert response.coupon.deadline == datetime.fromisoformat(
        "2026-08-01T15:00:00+02:00"
    )
    assert response.matches[0].home_team == "Arsenal"


def test_coupon_response_rejects_invalid_match_number() -> None:
    payload = create_coupon_payload()

    matches = cast(
        list[dict[str, object]],
        payload["matches"],
    )
    matches[0]["number"] = 0

    with pytest.raises(ValidationError):
        CouponResponse.model_validate(
            payload
        )


def test_coupon_list_rejects_negative_count() -> None:
    with pytest.raises(ValidationError):
        CouponListResponse(
            game_types=[],
            count=-1,
        )