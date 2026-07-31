"""Importer for structured Svenska Spel coupon data."""

from datetime import datetime
from pathlib import Path

from src.models.coupon import Coupon
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.models.match import Match
from src.providers.svenska_spel.client_protocol import SvenskaSpelClient
from src.validators.match_validator import MatchValidator


class SvenskaSpelImportError(ValueError):
    """Raised when Svenska Spel data cannot be imported."""


class SvenskaSpelImporter:
    """Converts Svenska Spel provider data into a Coupon."""

    _game_type_aliases = {
        "topptipset": GameType.TOPPTIPSET,
        "stryktipset": GameType.STRYKTIPSET,
        "europatipset": GameType.EUROPATIPSET,
    }

    def __init__(
        self,
        client: SvenskaSpelClient,
        validator: MatchValidator | None = None,
    ) -> None:
        """Create the importer with a Svenska Spel client."""

        self._client = client
        self._validator = validator or MatchValidator()

    def load_coupon(
        self,
        source_reference: str | Path,
        *,
        game_type: GameType = GameType.UNKNOWN,
        coupon_id: str | None = None,
        deadline: datetime | None = None,
    ) -> Coupon:
        """Load and convert a Svenska Spel coupon."""

        provider_data = self._client.fetch_coupon(
            source_reference
        )

        resolved_game_type = self._resolve_game_type(
            requested_game_type=game_type,
            provider_game_type=provider_data.game_type,
        )

        resolved_coupon_id = (
            coupon_id
            if coupon_id is not None
            else provider_data.coupon_id
        )

        resolved_deadline = (
            deadline
            if deadline is not None
            else provider_data.deadline
        )

        coupon = Coupon(
            game_type=resolved_game_type,
            source=ImportSource.SVENSKA_SPEL,
            coupon_id=resolved_coupon_id,
            deadline=resolved_deadline,
        )

        for match_data in provider_data.matches:
            home_team, away_team = (
                self._validator.validate_teams(
                    match_data.home_team,
                    match_data.away_team,
                    match_data.match_number,
                )
            )

            coupon.add_match(
                Match(
                    match_number=match_data.match_number,
                    home_team=home_team,
                    away_team=away_team,
                    competition=match_data.competition,
                    kickoff=match_data.kickoff,
                )
            )

        return coupon

    def _resolve_game_type(
        self,
        *,
        requested_game_type: GameType,
        provider_game_type: str,
    ) -> GameType:
        """Resolve the requested or provider supplied game type."""

        if requested_game_type is not GameType.UNKNOWN:
            return requested_game_type

        normalized_game_type = self._normalize_game_type(
            provider_game_type
        )

        try:
            return self._game_type_aliases[
                normalized_game_type
            ]
        except KeyError as error:
            raise SvenskaSpelImportError(
                "Unsupported Svenska Spel game type: "
                f"{provider_game_type!r}."
            ) from error

    @staticmethod
    def _normalize_game_type(game_type: str) -> str:
        """Normalize an external game type value."""

        if not isinstance(game_type, str):
            raise SvenskaSpelImportError(
                "Svenska Spel game type must be a string."
            )

        return (
            game_type
            .strip()
            .casefold()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )