"""Strict JSON importer for practical real-coupon analysis input."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from src.models.coupon_analysis_document import (
    CouponAnalysisDocument,
)
from src.models.coupon_analysis_input import (
    CouponAnalysisInput,
)
from src.models.game_type import GameType
from src.models.market_snapshot import MarketSnapshot
from src.models.match_analysis_input import MatchAnalysisInput
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)


class CouponAnalysisJsonImporter:
    """Imports one strict versioned JSON document into domain models."""

    schema_version = CouponAnalysisDocument.CURRENT_SCHEMA_VERSION

    _top_level_fields = {
        "schema_version",
        "coupon",
        "matches",
    }
    _coupon_fields = {
        "id",
        "game_type",
    }
    _match_fields = {
        "number",
        "reference",
        "home_team",
        "away_team",
        "home_performances",
        "away_performances",
        "market",
    }
    _market_fields = {
        "earlier",
        "later",
    }
    _snapshot_fields = {
        "captured_at",
        "source_name",
        "odds",
        "public_percentages",
    }
    _distribution_fields = {
        "1",
        "X",
        "2",
    }
    _performance_fields = {
        "opponent",
        "played_at",
        "venue",
        "goals_for",
        "goals_against",
        "xg_for",
        "xg_against",
        "shots_for",
        "shots_against",
        "shots_on_target_for",
        "shots_on_target_against",
        "possession_percentage",
        "competition",
    }

    def from_file(
        self,
        path: str | Path,
    ) -> CouponAnalysisDocument:
        """Load and import one UTF-8 JSON file."""

        resolved_path = Path(
            path
        )

        if not resolved_path.is_file():
            raise FileNotFoundError(
                f"Coupon-analysis JSON file not found: "
                f"{resolved_path}"
            )

        json_text = resolved_path.read_text(
            encoding="utf-8-sig"
        )

        return self.from_json(
            json_text,
            source_name=str(
                resolved_path
            ),
        )

    def from_json(
        self,
        json_text: str,
        *,
        source_name: str | None = None,
    ) -> CouponAnalysisDocument:
        """Parse and import one JSON string."""

        if not isinstance(
            json_text,
            str,
        ):
            raise TypeError(
                "json_text must be a string."
            )

        if not json_text.strip():
            raise ValueError(
                "json_text must not be empty."
            )

        try:
            payload = json.loads(
                json_text
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                "Invalid coupon-analysis JSON: "
                f"{error.msg} at line {error.lineno}, "
                f"column {error.colno}."
            ) from error

        return self.from_dict(
            payload,
            source_name=source_name,
        )

    def from_dict(
        self,
        payload: Mapping[str, Any],
        *,
        source_name: str | None = None,
    ) -> CouponAnalysisDocument:
        """Import one already decoded JSON-compatible mapping."""

        root = self._require_mapping(
            payload,
            path="$",
        )
        self._reject_unknown_fields(
            root,
            self._top_level_fields,
            path="$",
        )
        self._require_fields(
            root,
            self._top_level_fields,
            path="$",
        )

        schema_version = self._require_text(
            root["schema_version"],
            path="$.schema_version",
        )

        coupon_data = self._require_mapping(
            root["coupon"],
            path="$.coupon",
        )
        self._reject_unknown_fields(
            coupon_data,
            self._coupon_fields,
            path="$.coupon",
        )
        self._require_fields(
            coupon_data,
            {
                "game_type",
            },
            path="$.coupon",
        )

        game_type = self._parse_game_type(
            coupon_data["game_type"],
            path="$.coupon.game_type",
        )
        coupon_id = self._optional_text(
            coupon_data.get(
                "id"
            ),
            path="$.coupon.id",
        )

        matches_data = self._require_sequence(
            root["matches"],
            path="$.matches",
        )

        expected_match_count = (
            game_type.expected_match_count
        )

        if expected_match_count is None:
            raise ValueError(
                "$.coupon.game_type: selected game type "
                "has no expected match count."
            )

        if len(matches_data) != expected_match_count:
            raise ValueError(
                "$.matches: "
                f"{game_type.display_name} requires exactly "
                f"{expected_match_count} matches, received "
                f"{len(matches_data)}."
            )

        matches: list[MatchAnalysisInput] = []
        actual_numbers: list[int] = []

        for index, match_data in enumerate(
            matches_data,
            start=1,
        ):
            match, match_number = self._parse_match(
                match_data,
                path=f"$.matches[{index - 1}]",
            )
            matches.append(
                match
            )
            actual_numbers.append(
                match_number
            )

        expected_numbers = list(
            range(
                1,
                expected_match_count + 1,
            )
        )

        if actual_numbers != expected_numbers:
            raise ValueError(
                "$.matches: match numbers must be in "
                f"strict coupon order {expected_numbers}, "
                f"received {actual_numbers}."
            )

        analysis_input = CouponAnalysisInput(
            game_type=game_type,
            matches=tuple(
                matches
            ),
            coupon_id=coupon_id,
        )

        return CouponAnalysisDocument(
            schema_version=schema_version,
            analysis_input=analysis_input,
            source_name=source_name,
        )

    def _parse_match(
        self,
        value: object,
        *,
        path: str,
    ) -> tuple[MatchAnalysisInput, int]:
        """Parse one complete match input."""

        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._match_fields,
            path=path,
        )
        self._require_fields(
            data,
            {
                "number",
                "home_team",
                "away_team",
                "home_performances",
                "away_performances",
                "market",
            },
            path=path,
        )

        match_number = self._require_integer(
            data["number"],
            path=f"{path}.number",
            minimum=1,
        )
        home_team = self._require_text(
            data["home_team"],
            path=f"{path}.home_team",
        )
        away_team = self._require_text(
            data["away_team"],
            path=f"{path}.away_team",
        )
        reference = self._optional_text(
            data.get(
                "reference"
            ),
            path=f"{path}.reference",
        )

        home_performances = self._parse_performances(
            data["home_performances"],
            team_name=home_team,
            path=f"{path}.home_performances",
        )
        away_performances = self._parse_performances(
            data["away_performances"],
            team_name=away_team,
            path=f"{path}.away_performances",
        )

        market_data = self._require_mapping(
            data["market"],
            path=f"{path}.market",
        )
        self._reject_unknown_fields(
            market_data,
            self._market_fields,
            path=f"{path}.market",
        )
        self._require_fields(
            market_data,
            self._market_fields,
            path=f"{path}.market",
        )

        earlier_snapshot = self._parse_market_snapshot(
            market_data["earlier"],
            path=f"{path}.market.earlier",
        )
        later_snapshot = self._parse_market_snapshot(
            market_data["later"],
            path=f"{path}.market.later",
        )

        if (
            earlier_snapshot.captured_at
            > later_snapshot.captured_at
        ):
            raise ValueError(
                f"{path}.market: earlier snapshot must not "
                "be captured after the later snapshot."
            )

        return (
            MatchAnalysisInput(
                home_team_name=home_team,
                away_team_name=away_team,
                home_performances=home_performances,
                away_performances=away_performances,
                earlier_market_snapshot=earlier_snapshot,
                later_market_snapshot=later_snapshot,
                match_reference=reference,
            ),
            match_number,
        )

    def _parse_performances(
        self,
        value: object,
        *,
        team_name: str,
        path: str,
    ) -> tuple[TeamMatchPerformance, ...]:
        """Parse one team's non-empty performance history."""

        items = self._require_sequence(
            value,
            path=path,
        )

        if not items:
            raise ValueError(
                f"{path}: at least one performance is required."
            )

        return tuple(
            self._parse_performance(
                item,
                team_name=team_name,
                path=f"{path}[{index}]",
            )
            for index, item in enumerate(
                items
            )
        )

    def _parse_performance(
        self,
        value: object,
        *,
        team_name: str,
        path: str,
    ) -> TeamMatchPerformance:
        """Parse one team performance without repeated team name."""

        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._performance_fields,
            path=path,
        )
        required_fields = (
            self._performance_fields
            - {
                "possession_percentage",
                "competition",
            }
        )
        self._require_fields(
            data,
            required_fields,
            path=path,
        )

        venue_text = self._require_text(
            data["venue"],
            path=f"{path}.venue",
        ).lower()

        try:
            venue = MatchVenue(
                venue_text
            )
        except ValueError as error:
            allowed = ", ".join(
                venue.value
                for venue in MatchVenue
            )
            raise ValueError(
                f"{path}.venue: expected one of {allowed}."
            ) from error

        return TeamMatchPerformance(
            team_name=team_name,
            opponent_name=self._require_text(
                data["opponent"],
                path=f"{path}.opponent",
            ),
            played_at=self._parse_datetime(
                data["played_at"],
                path=f"{path}.played_at",
            ),
            venue=venue,
            goals_for=self._require_integer(
                data["goals_for"],
                path=f"{path}.goals_for",
                minimum=0,
            ),
            goals_against=self._require_integer(
                data["goals_against"],
                path=f"{path}.goals_against",
                minimum=0,
            ),
            expected_goals_for=self._require_numeric(
                data["xg_for"],
                path=f"{path}.xg_for",
            ),
            expected_goals_against=self._require_numeric(
                data["xg_against"],
                path=f"{path}.xg_against",
            ),
            shots_for=self._require_integer(
                data["shots_for"],
                path=f"{path}.shots_for",
                minimum=0,
            ),
            shots_against=self._require_integer(
                data["shots_against"],
                path=f"{path}.shots_against",
                minimum=0,
            ),
            shots_on_target_for=self._require_integer(
                data["shots_on_target_for"],
                path=f"{path}.shots_on_target_for",
                minimum=0,
            ),
            shots_on_target_against=self._require_integer(
                data["shots_on_target_against"],
                path=f"{path}.shots_on_target_against",
                minimum=0,
            ),
            possession_percentage=self._optional_numeric(
                data.get(
                    "possession_percentage"
                ),
                path=f"{path}.possession_percentage",
            ),
            competition=self._optional_text(
                data.get(
                    "competition"
                ),
                path=f"{path}.competition",
            ),
        )

    def _parse_market_snapshot(
        self,
        value: object,
        *,
        path: str,
    ) -> MarketSnapshot:
        """Parse one complete market snapshot."""

        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._snapshot_fields,
            path=path,
        )
        self._require_fields(
            data,
            self._snapshot_fields,
            path=path,
        )

        odds_values = self._parse_distribution(
            data["odds"],
            path=f"{path}.odds",
        )
        public_values = self._parse_distribution(
            data["public_percentages"],
            path=f"{path}.public_percentages",
        )

        return MarketSnapshot(
            captured_at=self._parse_datetime(
                data["captured_at"],
                path=f"{path}.captured_at",
            ),
            source_name=self._require_text(
                data["source_name"],
                path=f"{path}.source_name",
            ),
            odds=ThreeWayOdds(
                home=odds_values["1"],
                draw=odds_values["X"],
                away=odds_values["2"],
            ),
            public_percentages=ThreeWayPercentages(
                home=public_values["1"],
                draw=public_values["X"],
                away=public_values["2"],
            ),
        )

    def _parse_distribution(
        self,
        value: object,
        *,
        path: str,
    ) -> dict[str, int | float | str]:
        """Parse an exact 1-X-2 numeric distribution."""

        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._distribution_fields,
            path=path,
        )
        self._require_fields(
            data,
            self._distribution_fields,
            path=path,
        )

        return {
            symbol: self._require_numeric(
                data[symbol],
                path=f"{path}.{symbol}",
            )
            for symbol in (
                "1",
                "X",
                "2",
            )
        }

    @staticmethod
    def _parse_game_type(
        value: object,
        *,
        path: str,
    ) -> GameType:
        """Parse one supported football-pool game type."""

        game_type_text = CouponAnalysisJsonImporter._require_text(
            value,
            path=path,
        ).lower()

        try:
            game_type = GameType(
                game_type_text
            )
        except ValueError as error:
            allowed = ", ".join(
                game_type.value
                for game_type in GameType
                if game_type is not GameType.UNKNOWN
            )
            raise ValueError(
                f"{path}: expected one of {allowed}."
            ) from error

        if game_type is GameType.UNKNOWN:
            raise ValueError(
                f"{path}: unknown is not a supported "
                "analysis game type."
            )

        return game_type

    @staticmethod
    def _parse_datetime(
        value: object,
        *,
        path: str,
    ) -> datetime:
        """Parse one timezone-aware ISO 8601 datetime."""

        text = CouponAnalysisJsonImporter._require_text(
            value,
            path=path,
        )

        normalized_text = (
            f"{text[:-1]}+00:00"
            if text.endswith(
                (
                    "Z",
                    "z",
                )
            )
            else text
        )

        try:
            parsed = datetime.fromisoformat(
                normalized_text
            )
        except ValueError as error:
            raise ValueError(
                f"{path}: expected an ISO 8601 datetime."
            ) from error

        if (
            parsed.tzinfo is None
            or parsed.utcoffset() is None
        ):
            raise ValueError(
                f"{path}: datetime must include a timezone."
            )

        return parsed

    @staticmethod
    def _require_mapping(
        value: object,
        *,
        path: str,
    ) -> Mapping[str, Any]:
        """Require one JSON object-like mapping."""

        if not isinstance(
            value,
            Mapping,
        ):
            raise TypeError(
                f"{path}: expected an object."
            )

        for key in value:
            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    f"{path}: object keys must be strings."
                )

        return value

    @staticmethod
    def _require_sequence(
        value: object,
        *,
        path: str,
    ) -> Sequence[Any]:
        """Require one JSON array-like sequence."""

        if isinstance(
            value,
            (
                str,
                bytes,
                bytearray,
            ),
        ) or not isinstance(
            value,
            Sequence,
        ):
            raise TypeError(
                f"{path}: expected an array."
            )

        return value

    @staticmethod
    def _require_text(
        value: object,
        *,
        path: str,
    ) -> str:
        """Require and normalize one non-empty string."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{path}: expected a string."
            )

        normalized = " ".join(
            value.split()
        )

        if not normalized:
            raise ValueError(
                f"{path}: string must not be empty."
            )

        return normalized

    @staticmethod
    def _optional_text(
        value: object,
        *,
        path: str,
    ) -> str | None:
        """Parse one optional text field."""

        if value is None:
            return None

        return CouponAnalysisJsonImporter._require_text(
            value,
            path=path,
        )

    @staticmethod
    def _require_integer(
        value: object,
        *,
        path: str,
        minimum: int,
    ) -> int:
        """Require one integer with a lower bound."""

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            int,
        ):
            raise TypeError(
                f"{path}: expected an integer."
            )

        if value < minimum:
            raise ValueError(
                f"{path}: value must be at least {minimum}."
            )

        return value

    @staticmethod
    def _require_numeric(
        value: object,
        *,
        path: str,
    ) -> int | float | str:
        """Require a JSON numeric value or numeric string."""

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (
                int,
                float,
                str,
            ),
        ):
            raise TypeError(
                f"{path}: expected a number or numeric string."
            )

        if isinstance(
            value,
            str,
        ) and not value.strip():
            raise ValueError(
                f"{path}: numeric string must not be empty."
            )

        try:
            decimal_value = Decimal(
                str(value)
            )
        except (
            InvalidOperation,
            ValueError,
        ) as error:
            raise ValueError(
                f"{path}: expected a valid numeric value."
            ) from error

        if not decimal_value.is_finite():
            raise ValueError(
                f"{path}: numeric value must be finite."
            )

        return value

    @staticmethod
    def _optional_numeric(
        value: object,
        *,
        path: str,
    ) -> int | float | str | None:
        """Parse one optional numeric value."""

        if value is None:
            return None

        return CouponAnalysisJsonImporter._require_numeric(
            value,
            path=path,
        )

    @staticmethod
    def _require_fields(
        data: Mapping[str, Any],
        required_fields: set[str],
        *,
        path: str,
    ) -> None:
        """Require an exact group of mandatory object fields."""

        missing_fields = sorted(
            required_fields
            - set(
                data
            )
        )

        if missing_fields:
            raise ValueError(
                f"{path}: missing required field(s): "
                f"{', '.join(missing_fields)}."
            )

    @staticmethod
    def _reject_unknown_fields(
        data: Mapping[str, Any],
        allowed_fields: set[str],
        *,
        path: str,
    ) -> None:
        """Reject misspelled or unsupported object fields."""

        unknown_fields = sorted(
            set(
                data
            )
            - allowed_fields
        )

        if unknown_fields:
            raise ValueError(
                f"{path}: unknown field(s): "
                f"{', '.join(unknown_fields)}."
            )