"""Input model for complete football coupon analysis."""

from dataclasses import dataclass

from src.models.game_type import GameType
from src.models.match_analysis_input import MatchAnalysisInput


@dataclass(frozen=True, slots=True)
class CouponAnalysisInput:
    """Contains all match inputs belonging to one coupon."""

    game_type: GameType
    matches: tuple[
        MatchAnalysisInput,
        ...,
    ]
    coupon_id: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the coupon-analysis input."""

        if not isinstance(
            self.game_type,
            GameType,
        ):
            raise TypeError(
                "game_type must be a GameType."
            )

        if self.game_type is GameType.UNKNOWN:
            raise ValueError(
                "Coupon analysis requires a supported "
                "game type."
            )

        if not isinstance(
            self.matches,
            tuple,
        ):
            raise TypeError(
                "matches must be a tuple."
            )

        expected_match_count = (
            self.game_type.expected_match_count
        )

        if expected_match_count is None:
            raise ValueError(
                "The selected game type has no "
                "expected match count."
            )

        if len(self.matches) != expected_match_count:
            raise ValueError(
                f"{self.game_type.display_name} requires "
                f"exactly {expected_match_count} matches."
            )

        for match_input in self.matches:
            if not isinstance(
                match_input,
                MatchAnalysisInput,
            ):
                raise TypeError(
                    "matches may only contain "
                    "MatchAnalysisInput objects."
                )

        references = tuple(
            match_input.match_reference.casefold()
            for match_input in self.matches
            if match_input.match_reference is not None
        )

        if len(set(references)) != len(references):
            raise ValueError(
                "Match references must be unique "
                "within the coupon."
            )

        if self.coupon_id is not None:
            normalized_coupon_id = (
                self._normalize_required_text(
                    self.coupon_id,
                    field_name="coupon_id",
                )
            )

            object.__setattr__(
                self,
                "coupon_id",
                normalized_coupon_id,
            )

    @property
    def match_count(self) -> int:
        """Return the supplied number of matches."""

        return len(
            self.matches
        )

    @property
    def expected_match_count(self) -> int:
        """Return the required number of matches."""

        expected_match_count = (
            self.game_type.expected_match_count
        )

        if expected_match_count is None:
            raise RuntimeError(
                "Supported game type unexpectedly "
                "lacks an expected match count."
            )

        return expected_match_count

    @staticmethod
    def _normalize_required_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """Normalize one required text value."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized_value = " ".join(
            value.split()
        )

        if not normalized_value:
            raise ValueError(
                f"{field_name} must not be empty."
            )

        return normalized_value