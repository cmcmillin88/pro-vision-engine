"""Practical JSON-file runner for complete coupon analysis."""

from datetime import datetime, timezone
from pathlib import Path

from src.importer.coupon_analysis_json_importer import (
    CouponAnalysisJsonImporter,
)
from src.models.coupon_analysis_document import (
    CouponAnalysisDocument,
)
from src.models.coupon_analysis_run import CouponAnalysisRun
from src.models.reduction_frame import ReductionFrame
from src.services.final_coupon_analysis_engine import (
    FinalCouponAnalysisEngine,
)
from src.services.reduction_row_generator import (
    ReductionRowGenerator,
)


class CouponAnalysisFileRunner:
    """Imports, analyzes, assesses and builds the turquoise system."""

    def __init__(
        self,
        importer: CouponAnalysisJsonImporter | None = None,
        analysis_engine: FinalCouponAnalysisEngine | None = None,
        row_generator: ReductionRowGenerator | None = None,
    ) -> None:
        """Create the practical analysis runner."""

        if (
            importer is not None
            and not isinstance(
                importer,
                CouponAnalysisJsonImporter,
            )
        ):
            raise TypeError(
                "importer must be a CouponAnalysisJsonImporter or None."
            )

        if (
            analysis_engine is not None
            and not isinstance(
                analysis_engine,
                FinalCouponAnalysisEngine,
            )
        ):
            raise TypeError(
                "analysis_engine must be a "
                "FinalCouponAnalysisEngine or None."
            )

        if (
            row_generator is not None
            and not isinstance(
                row_generator,
                ReductionRowGenerator,
            )
        ):
            raise TypeError(
                "row_generator must be a ReductionRowGenerator or None."
            )

        self._importer = importer or CouponAnalysisJsonImporter()
        self._analysis_engine = (
            analysis_engine
            or FinalCouponAnalysisEngine()
        )
        self._row_generator = (
            row_generator
            or ReductionRowGenerator()
        )

    @property
    def row_generator(self) -> ReductionRowGenerator:
        """Return the configured capacity-aware row generator."""

        return self._row_generator

    def run_file(
        self,
        path: str | Path,
        *,
        analyzed_at: datetime | None = None,
    ) -> CouponAnalysisRun:
        """Run complete analysis from one practical JSON file."""

        document = self._importer.from_file(
            path
        )

        return self.run_document(
            document,
            analyzed_at=analyzed_at,
        )

    def run_document(
        self,
        document: CouponAnalysisDocument,
        *,
        analyzed_at: datetime | None = None,
    ) -> CouponAnalysisRun:
        """Run complete analysis from one imported document."""

        if not isinstance(
            document,
            CouponAnalysisDocument,
        ):
            raise TypeError(
                "document must be a CouponAnalysisDocument."
            )

        resolved_analyzed_at = self._resolve_analyzed_at(
            analyzed_at
        )

        analysis_report = self._analysis_engine.analyze(
            document.analysis_input
        )
        reduction_frame = ReductionFrame.from_coupon_analysis(
            analysis_report
        )
        capacity_assessment, base_system = (
            self._row_generator.generate_with_assessment(
                reduction_frame
            )
        )

        return CouponAnalysisRun(
            input_document=document,
            analysis_report=analysis_report,
            reduction_frame=reduction_frame,
            capacity_assessment=capacity_assessment,
            base_system=base_system,
            analyzed_at=resolved_analyzed_at,
        )

    @staticmethod
    def _resolve_analyzed_at(
        analyzed_at: datetime | None,
    ) -> datetime:
        """Return a validated timezone-aware analysis timestamp."""

        if analyzed_at is None:
            return datetime.now(
                timezone.utc
            )

        if not isinstance(
            analyzed_at,
            datetime,
        ):
            raise TypeError(
                "analyzed_at must be a datetime or None."
            )

        if (
            analyzed_at.tzinfo is None
            or analyzed_at.utcoffset() is None
        ):
            raise ValueError(
                "analyzed_at must be timezone-aware."
            )

        return analyzed_at