"""JSON exporter for validated football pool coupons."""

import json
from datetime import datetime
from typing import Any

from src.models.coupon import Coupon
from src.models.match import Match


class CouponJsonExporter:
    """Converts Coupon objects into a stable JSON contract."""

    schema_version = "1.0"

    def to_dict(
        self,
        coupon: Coupon,
    ) -> dict[str, Any]:
        """Convert a coupon into a JSON-compatible dictionary."""

        self._validate_coupon_type(coupon)

        return {
            "schema_version": self.schema_version,
            "coupon": {
                "id": coupon.coupon_id,
                "game_type": coupon.game_type.value,
                "game_type_display": coupon.game_type.display_name,
                "source": coupon.source.value,
                "source_display": coupon.source.display_name,
                "deadline": self._serialize_datetime(
                    coupon.deadline
                ),
                "imported_at": self._serialize_datetime(
                    coupon.imported_at
                ),
                "match_count": len(coupon),
                "expected_match_count": (
                    coupon.expected_match_count
                ),
            },
            "matches": [
                self._serialize_match(match)
                for match in coupon.matches
            ],
        }

    def to_json(
        self,
        coupon: Coupon,
        *,
        indent: int | None = 2,
    ) -> str:
        """Convert a coupon into a formatted JSON string."""

        payload = self.to_dict(coupon)

        return json.dumps(
            payload,
            ensure_ascii=False,
            indent=indent,
        )

    def _serialize_match(
        self,
        match: Match,
    ) -> dict[str, Any]:
        """Convert one match into JSON-compatible data."""

        return {
            "number": match.match_number,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "competition": match.competition,
            "kickoff": self._serialize_datetime(
                match.kickoff
            ),
            "status": match.status,
        }

    @staticmethod
    def _serialize_datetime(
        value: datetime | None,
    ) -> str | None:
        """Convert a datetime into an ISO 8601 string."""

        if value is None:
            return None

        return value.isoformat()

    @staticmethod
    def _validate_coupon_type(
        coupon: Coupon,
    ) -> None:
        """Ensure that the exporter receives a Coupon object."""

        if not isinstance(coupon, Coupon):
            raise TypeError(
                "CouponJsonExporter requires a Coupon object."
            )