"""Validation rules for imported football matches."""

import re


class MatchValidator:
    """Validates match text and match numbers."""

    _match_pattern = re.compile(
        r"^\s*(.*?)\s+-\s*(.*?)\s*$"
    )

    def validate_and_split(
        self,
        line: str,
        match_number: int,
    ) -> tuple[str, str]:
        """Validate a match row and return the two team names."""

        self._validate_line_type(line)
        self._validate_match_number(match_number)

        if not line.strip():
            raise ValueError("Match line must not be empty.")

        match_result = self._match_pattern.fullmatch(line)

        if match_result is None:
            raise ValueError(
                f"Invalid match format: {line!r}. "
                "Expected 'Home Team - Away Team'."
            )

        home_team = match_result.group(1).strip()
        away_team = match_result.group(2).strip()

        if not home_team:
            raise ValueError("Home team must not be empty.")

        if not away_team:
            raise ValueError("Away team must not be empty.")

        return home_team, away_team

    @staticmethod
    def _validate_line_type(line: str) -> None:
        """Ensure that the match row is text."""

        if not isinstance(line, str):
            raise TypeError("Match line must be a string.")

    @staticmethod
    def _validate_match_number(match_number: int) -> None:
        """Ensure that the match number is a positive integer."""

        if isinstance(match_number, bool) or not isinstance(match_number, int):
            raise TypeError("Match number must be an integer.")

        if match_number < 1:
            raise ValueError("Match number must be greater than zero.")