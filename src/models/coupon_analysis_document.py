"""Versioned document wrapper for practical coupon-analysis input."""

from dataclasses import dataclass
from typing import ClassVar

from src.models.coupon_analysis_input import CouponAnalysisInput
from src.models.game_type import GameType
from src.models.match_analysis_input import MatchAnalysisInput


@dataclass(frozen=True, slots=True)
class CouponAnalysisDocument:
    """Contains one validated, versioned coupon-analysis document."""

    CURRENT_SCHEMA_VERSION: ClassVar[str] = "p13-analysis-input-v1"

    schema_version: str
    analysis_input: CouponAnalysisInput
    source_name: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the complete document wrapper."""

        if not isinstance(
            self.schema_version,
            str,
        ):
            raise TypeError(
                "schema_version must be a string."
            )

        normalized_version = self.schema_version.strip()

        if normalized_version != self.CURRENT_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported coupon-analysis schema version: "
                f"{normalized_version!r}."
            )

        object.__setattr__(
            self,
            "schema_version",
            normalized_version,
        )

        if not isinstance(
            self.analysis_input,
            CouponAnalysisInput,
        ):
            raise TypeError(
                "analysis_input must be a CouponAnalysisInput."
            )

        if self.source_name is not None:
            if not isinstance(
                self.source_name,
                str,
            ):
                raise TypeError(
                    "source_name must be a string or None."
                )

            normalized_source = " ".join(
                self.source_name.split()
            )

            if not normalized_source:
                raise ValueError(
                    "source_name must not be empty."
                )

            object.__setattr__(
                self,
                "source_name",
                normalized_source,
            )

    @property
    def coupon_id(self) -> str | None:
        """Return the imported coupon identifier."""

        return self.analysis_input.coupon_id

    @property
    def game_type(self) -> GameType:
        """Return the imported game type."""

        return self.analysis_input.game_type

    @property
    def matches(self) -> tuple[MatchAnalysisInput, ...]:
        """Return imported matches in coupon order."""

        return self.analysis_input.matches

    @property
    def match_count(self) -> int:
        """Return the number of imported matches."""

        return self.analysis_input.match_count

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable document summary."""

        coupon_text = (
            self.coupon_id
            if self.coupon_id is not None
            else "utan id"
        )

        return (
            f"{self.game_type.display_name} | "
            f"Kupong {coupon_text} | "
            f"Matcher {self.match_count} | "
            f"Kontrakt {self.schema_version}"
        )