"""Parser for structured Svenska Spel coupon payloads."""

from datetime import datetime
from typing import Any

from src.providers.svenska_spel.models import (
    SvenskaSpelCouponData,
    SvenskaSpelMatchData,
)


class SvenskaSpelPayloadError(ValueError):
    """Raised when a Svenska Spel payload is invalid."""


class SvenskaSpelPayloadParser:
    """Converts decoded payloads into Svenska Spel provider models."""

    def parse(
        self,
        raw_payload: Any,
    ) -> SvenskaSpelCouponData:
        """Parse one decoded Svenska Spel coupon payload."""

        payload = self._require_object(
            raw_payload,
            label="JSON root",
        )

        game_type = self._required_string(
            payload,
            "game_type",
        )
        coupon_id = self._optional_string(
            payload,
            "coupon_id",
        )
        deadline = self._optional_datetime(
            payload,
            "deadline",
        )

        raw_matches = self._required_list(
            payload,
            "matches",
        )

        matches = tuple(
            self._parse_match(
                raw_match,
                position,
            )
            for position, raw_match in enumerate(
                raw_matches,
                start=1,
            )
        )

        return SvenskaSpelCouponData(
            game_type=game_type,
            coupon_id=coupon_id,
            deadline=deadline,
            matches=matches,
        )

    def _parse_match(
        self,
        raw_match: Any,
        position: int,
    ) -> SvenskaSpelMatchData:
        """Convert one payload match into provider data."""

        label = f"matches[{position}]"

        match_data = self._require_object(
            raw_match,
            label=label,
        )

        match_number = self._required_integer(
            match_data,
            "match_number",
            parent=label,
        )
        home_team = self._required_string(
            match_data,
            "home_team",
            parent=label,
        )
        away_team = self._required_string(
            match_data,
            "away_team",
            parent=label,
        )
        competition = self._optional_string(
            match_data,
            "competition",
            parent=label,
        )
        kickoff = self._optional_datetime(
            match_data,
            "kickoff",
            parent=label,
        )

        return SvenskaSpelMatchData(
            match_number=match_number,
            home_team=home_team,
            away_team=away_team,
            competition=competition,
            kickoff=kickoff,
        )

    @staticmethod
    def _require_object(
        value: Any,
        *,
        label: str,
    ) -> dict[str, Any]:
        """Ensure that a payload value is an object."""

        if not isinstance(value, dict):
            raise SvenskaSpelPayloadError(
                f"{label} must be a JSON object."
            )

        return value

    def _required_string(
        self,
        payload: dict[str, Any],
        key: str,
        *,
        parent: str | None = None,
    ) -> str:
        """Read a required non-empty string field."""

        field_name = self._field_name(
            key,
            parent=parent,
        )

        if key not in payload:
            raise SvenskaSpelPayloadError(
                f"Missing required field: '{field_name}'."
            )

        value = payload[key]

        if not isinstance(value, str):
            raise SvenskaSpelPayloadError(
                f"'{field_name}' must be a string."
            )

        cleaned_value = value.strip()

        if not cleaned_value:
            raise SvenskaSpelPayloadError(
                f"'{field_name}' must not be empty."
            )

        return cleaned_value

    def _optional_string(
        self,
        payload: dict[str, Any],
        key: str,
        *,
        parent: str | None = None,
    ) -> str | None:
        """Read an optional string field."""

        if key not in payload or payload[key] is None:
            return None

        return self._required_string(
            payload,
            key,
            parent=parent,
        )

    def _required_integer(
        self,
        payload: dict[str, Any],
        key: str,
        *,
        parent: str | None = None,
    ) -> int:
        """Read a required integer field."""

        field_name = self._field_name(
            key,
            parent=parent,
        )

        if key not in payload:
            raise SvenskaSpelPayloadError(
                f"Missing required field: '{field_name}'."
            )

        value = payload[key]

        if isinstance(value, bool) or not isinstance(value, int):
            raise SvenskaSpelPayloadError(
                f"'{field_name}' must be an integer."
            )

        return value

    @staticmethod
    def _required_list(
        payload: dict[str, Any],
        key: str,
    ) -> list[Any]:
        """Read a required list field."""

        if key not in payload:
            raise SvenskaSpelPayloadError(
                f"Missing required field: '{key}'."
            )

        value = payload[key]

        if not isinstance(value, list):
            raise SvenskaSpelPayloadError(
                f"'{key}' must be a list."
            )

        return value

    def _optional_datetime(
        self,
        payload: dict[str, Any],
        key: str,
        *,
        parent: str | None = None,
    ) -> datetime | None:
        """Read an optional timezone-aware datetime field."""

        if key not in payload or payload[key] is None:
            return None

        field_name = self._field_name(
            key,
            parent=parent,
        )
        value = payload[key]

        if not isinstance(value, str):
            raise SvenskaSpelPayloadError(
                f"'{field_name}' must be a datetime string."
            )

        normalized_value = value.strip()

        if normalized_value.endswith("Z"):
            normalized_value = (
                normalized_value[:-1] + "+00:00"
            )

        try:
            parsed_datetime = datetime.fromisoformat(
                normalized_value
            )
        except ValueError as error:
            raise SvenskaSpelPayloadError(
                f"'{field_name}' contains an invalid datetime."
            ) from error

        if (
            parsed_datetime.tzinfo is None
            or parsed_datetime.utcoffset() is None
        ):
            raise SvenskaSpelPayloadError(
                f"'{field_name}' must include a timezone."
            )

        return parsed_datetime

    @staticmethod
    def _field_name(
        key: str,
        *,
        parent: str | None,
    ) -> str:
        """Create a readable nested field name."""

        if parent is None:
            return key

        return f"{parent}.{key}"