"""Text importer for Pro Vision Engine."""

from pathlib import Path

from src.models.coupon import Coupon
from src.models.match import Match


class TextImporter:
    """Converts text into Match and Coupon objects."""

    def parse_line(self, line: str, match_number: int) -> Match:
        """Convert one text row into a Match object."""

        cleaned_line = line.strip()
        teams = cleaned_line.split(" - ", maxsplit=1)

        if len(teams) != 2:
            raise ValueError(
                f"Invalid match format: {line!r}. "
                "Expected 'Home Team - Away Team'."
            )

        home_team, away_team = (team.strip() for team in teams)

        if not home_team or not away_team:
            raise ValueError(f"Home and away teams must not be empty: {line!r}")

        return Match(
            match_number=match_number,
            home_team=home_team,
            away_team=away_team,
        )

    def load_coupon(self, filename: str | Path) -> Coupon:
        """Load all matches from a text file into a Coupon."""

        path = Path(filename)
        coupon = Coupon()

        with path.open(encoding="utf-8") as file:
            for line in file:
                cleaned_line = line.strip()

                if not cleaned_line:
                    continue

                match_number = len(coupon) + 1
                match = self.parse_line(cleaned_line, match_number)
                coupon.add_match(match)

        return coupon