"""Text importer for Pro Vision Engine."""

from datetime import datetime
from pathlib import Path

from src.models.coupon import Coupon
from src.models.game_type import GameType
from src.models.import_source import ImportSource
from src.models.match import Match
from src.validators.match_validator import MatchValidator


class TextImporter:
    """Converts text into Match and Coupon objects."""

    def __init__(
        self,
        validator: MatchValidator | None = None,
    ) -> None:
        """Create an importer with a match validator."""

        self.validator = validator or MatchValidator()

    def parse_line(self, line: str, match_number: int) -> Match:
        """Convert one validated text row into a Match object."""

        home_team, away_team = self.validator.validate_and_split(
            line,
            match_number,
        )

        return Match(
            match_number=match_number,
            home_team=home_team,
            away_team=away_team,
        )

    def load_coupon(
        self,
        source_reference: str | Path,
        *,
        game_type: GameType = GameType.UNKNOWN,
        coupon_id: str | None = None,
        deadline: datetime | None = None,
    ) -> Coupon:
        """Load all matches from a text file into a Coupon."""

        path = Path(source_reference)

        coupon = Coupon(
            game_type=game_type,
            source=ImportSource.TEXT_FILE,
            coupon_id=coupon_id,
            deadline=deadline,
        )

        with path.open(encoding="utf-8") as file:
            for line in file:
                cleaned_line = line.strip()

                if not cleaned_line:
                    continue

                match_number = len(coupon) + 1
                match = self.parse_line(
                    cleaned_line,
                    match_number,
                )
                coupon.add_match(match)

        return coupon