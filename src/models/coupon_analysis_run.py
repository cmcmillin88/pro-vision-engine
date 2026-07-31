"""Complete result chain for one practical coupon-analysis run."""

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from src.models.coupon_analysis_document import (
    CouponAnalysisDocument,
)
from src.models.final_coupon_analysis import (
    FinalCouponAnalysisReport,
)
from src.models.game_type import GameType
from src.models.reduction_frame import (
    BaseReductionSystem,
    ReductionFrame,
)


@dataclass(frozen=True, slots=True)
class CouponAnalysisRun:
    """Links imported input, final analysis and turquoise base system."""

    CURRENT_SCHEMA_VERSION: ClassVar[str] = "p13-analysis-result-v1"

    input_document: CouponAnalysisDocument
    analysis_report: FinalCouponAnalysisReport
    reduction_frame: ReductionFrame
    base_system: BaseReductionSystem
    analyzed_at: datetime
    schema_version: str = CURRENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate the complete practical analysis chain."""

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
                "Unsupported coupon-analysis result schema version: "
                f"{normalized_version!r}."
            )

        object.__setattr__(
            self,
            "schema_version",
            normalized_version,
        )

        if not isinstance(
            self.input_document,
            CouponAnalysisDocument,
        ):
            raise TypeError(
                "input_document must be a CouponAnalysisDocument."
            )

        if not isinstance(
            self.analysis_report,
            FinalCouponAnalysisReport,
        ):
            raise TypeError(
                "analysis_report must be a FinalCouponAnalysisReport."
            )

        if not isinstance(
            self.reduction_frame,
            ReductionFrame,
        ):
            raise TypeError(
                "reduction_frame must be a ReductionFrame."
            )

        if not isinstance(
            self.base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "base_system must be a BaseReductionSystem."
            )

        if not isinstance(
            self.analyzed_at,
            datetime,
        ):
            raise TypeError(
                "analyzed_at must be a datetime."
            )

        if (
            self.analyzed_at.tzinfo is None
            or self.analyzed_at.utcoffset() is None
        ):
            raise ValueError(
                "analyzed_at must be timezone-aware."
            )

        if (
            self.analysis_report.analysis_input
            != self.input_document.analysis_input
        ):
            raise ValueError(
                "analysis_report must originate from the "
                "input_document analysis input."
            )

        expected_frame = ReductionFrame.from_coupon_analysis(
            self.analysis_report
        )

        if self.reduction_frame != expected_frame:
            raise ValueError(
                "reduction_frame must match the final coupon "
                "recommendations exactly."
            )

        if self.base_system.frame != self.reduction_frame:
            raise ValueError(
                "base_system must belong to reduction_frame."
            )

        if (
            self.base_system.row_count
            != self.analysis_report.base_row_count
        ):
            raise ValueError(
                "base_system row count must equal the final "
                "coupon analysis base-row count."
            )

    @property
    def coupon_id(self) -> str | None:
        """Return the optional coupon identifier."""

        return self.analysis_report.coupon_id

    @property
    def game_type(self) -> GameType:
        """Return the analyzed game type."""

        return self.analysis_report.game_type

    @property
    def match_count(self) -> int:
        """Return the analyzed match count."""

        return self.analysis_report.match_count

    @property
    def recommendation_pattern(self) -> str:
        """Return the final turquoise frame pattern."""

        return self.reduction_frame.recommendation_pattern

    @property
    def base_row_count(self) -> int:
        """Return the complete turquoise base-system size."""

        return self.base_system.row_count

    @property
    def source_name(self) -> str | None:
        """Return the practical input source when available."""

        return self.input_document.source_name

    @property
    def summary_line(self) -> str:
        """Return a compact practical run summary."""

        coupon_text = (
            self.coupon_id
            if self.coupon_id is not None
            else "utan id"
        )

        return (
            f"{self.game_type.display_name} | "
            f"Kupong {coupon_text} | "
            f"Matcher {self.match_count} | "
            f"Ram {self.recommendation_pattern} | "
            f"Rader {self.base_row_count} | "
            f"Resultat {self.schema_version}"
        )