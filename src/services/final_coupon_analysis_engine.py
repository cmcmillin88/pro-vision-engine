"""Final end-to-end football coupon analysis orchestration."""

from src.models.coupon_analysis_input import (
    CouponAnalysisInput,
)
from src.models.final_coupon_analysis import (
    FinalCouponAnalysisReport,
)
from src.services.final_match_analysis_engine import (
    FinalMatchAnalysisEngine,
)


class FinalCouponAnalysisEngine:
    """Runs final match analysis for an entire coupon."""

    def __init__(
        self,
        match_analysis_engine: (
            FinalMatchAnalysisEngine
            | None
        ) = None,
    ) -> None:
        """Create the complete coupon-analysis engine."""

        if (
            match_analysis_engine is not None
            and not isinstance(
                match_analysis_engine,
                FinalMatchAnalysisEngine,
            )
        ):
            raise TypeError(
                "match_analysis_engine must be a "
                "FinalMatchAnalysisEngine or None."
            )

        self._match_analysis_engine = (
            match_analysis_engine
            or FinalMatchAnalysisEngine()
        )

    def analyze(
        self,
        analysis_input: CouponAnalysisInput,
    ) -> FinalCouponAnalysisReport:
        """Run final analysis for every coupon match."""

        if not isinstance(
            analysis_input,
            CouponAnalysisInput,
        ):
            raise TypeError(
                "FinalCouponAnalysisEngine requires "
                "a CouponAnalysisInput."
            )

        match_reports = tuple(
            self._match_analysis_engine.analyze(
                match_input
            )
            for match_input in analysis_input.matches
        )

        return FinalCouponAnalysisReport(
            analysis_input=analysis_input,
            match_reports=match_reports,
        )