"""Configuration for the complete statistical analysis pipeline."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StatisticalAnalysisSettings:
    """Contains form-window and competition settings."""

    home_match_limit: int | None = 5
    away_match_limit: int | None = 5
    competition: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate all statistical settings."""

        for field_name in (
            "home_match_limit",
            "away_match_limit",
        ):
            self._validate_limit(
                getattr(
                    self,
                    field_name,
                ),
                field_name=field_name,
            )

        if self.competition is None:
            return

        if not isinstance(
            self.competition,
            str,
        ):
            raise TypeError(
                "competition must be a string or None."
            )

        normalized_competition = " ".join(
            self.competition.split()
        )

        if not normalized_competition:
            raise ValueError(
                "competition must not be empty."
            )

        object.__setattr__(
            self,
            "competition",
            normalized_competition,
        )

    @staticmethod
    def _validate_limit(
        value: int | None,
        *,
        field_name: str,
    ) -> None:
        """Validate one optional recent-match limit."""

        if value is None:
            return

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            int,
        ):
            raise TypeError(
                f"{field_name} must be "
                "an integer or None."
            )

        if value <= 0:
            raise ValueError(
                f"{field_name} must be "
                "greater than zero."
            )