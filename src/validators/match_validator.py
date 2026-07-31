"""Validation rules for imported football matches."""

import re


class MatchValidator:
    """Validates match text, team names and match numbers."""

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

        if not line.strip():
            raise ValueError("Match line must not be empty.")

        match_result = self._match_pattern.fullmatch(line)

        if match_result is None:
            raise ValueError(
                f"Invalid match format: {line!r}. "
                "Expected 'Home Team - Away Team'."
            )

        home_team = match_result.group(1)
        away_team = match_result.group(2)

        return self.validate_teams(
            home_team,
            away_team,
            match_number,
        )

    def validate_teams(
        self,
        home_team: str,
        away_team: str,
        match_number: int,
    ) -> tuple[str, str]:
        """Validate two structured team names."""

        self._validate_team_type(
            home_team,
            label="Home team",
        )
        self._validate_team_type(
            away_team,
            label="Away team",
        )
        self._validate_match_number(match_number)

        cleaned_home_team = home_team.strip()
        cleaned_away_team = away_team.strip()

        if not cleaned_home_team:
            raise ValueError("Home team must not be empty.")

        if not cleaned_away_team:
            raise ValueError("Away team must not be empty.")

        return cleaned_home_team, cleaned_away_team

    @staticmethod
    def _validate_line_type(line: str) -> None:
        """Ensure that the match row is text."""

        if not isinstance(line, str):
            raise TypeError("Match line must be a string.")

    @staticmethod
    def _validate_team_type(
        team_name: str,
        *,
        label: str,
    ) -> None:
        """Ensure that a team name is text."""

        if not isinstance(team_name, str):
            raise TypeError(f"{label} must be a string.")

    @staticmethod
    def _validate_match_number(match_number: int) -> None:
        """Ensure that the match number is a positive integer."""

        if isinstance(match_number, bool) or not isinstance(match_number, int):
            raise TypeError("Match number must be an integer.")

        if match_number < 1:
            raise ValueError("Match number must be greater than zero.")