"""
Text importer for Pro Vision Engine.
"""

from src.models.match import Match


class TextImporter:
    """Converts text rows into Match objects."""

    def parse_line(self, line: str, match_number: int) -> Match:
        """
        Parse one line in the format:
        Home Team - Away Team
        """

        home, away = [team.strip() for team in line.split("-", maxsplit=1)]

        return Match(
            match_number=match_number,
            home_team=home,
            away_team=away,
        )