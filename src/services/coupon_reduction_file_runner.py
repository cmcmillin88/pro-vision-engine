"""Practical file runner for complete coupon analysis and reduction."""

from datetime import datetime, timezone
from pathlib import Path

from src.importer.reduction_configuration_json_importer import (
    ReductionConfigurationJsonImporter,
)
from src.models.coupon_analysis_run import CouponAnalysisRun
from src.models.coupon_reduction_run import CouponReductionRun
from src.models.reduction_configuration_document import (
    ReductionConfigurationDocument,
)
from src.services.coupon_analysis_file_runner import (
    CouponAnalysisFileRunner,
)
from src.services.final_reduction_report_engine import (
    FinalReductionReportEngine,
)


class CouponReductionFileRunner:
    """Runs analysis, imports reduction rules and creates final rows."""

    def __init__(
        self,
        analysis_runner: CouponAnalysisFileRunner | None = None,
        configuration_importer: (
            ReductionConfigurationJsonImporter | None
        ) = None,
        report_engine: FinalReductionReportEngine | None = None,
    ) -> None:
        """Create the complete practical reduction runner."""

        if (
            analysis_runner is not None
            and not isinstance(analysis_runner, CouponAnalysisFileRunner)
        ):
            raise TypeError(
                "analysis_runner must be a CouponAnalysisFileRunner or None."
            )

        if (
            configuration_importer is not None
            and not isinstance(
                configuration_importer,
                ReductionConfigurationJsonImporter,
            )
        ):
            raise TypeError(
                "configuration_importer must be a "
                "ReductionConfigurationJsonImporter or None."
            )

        if (
            report_engine is not None
            and not isinstance(report_engine, FinalReductionReportEngine)
        ):
            raise TypeError(
                "report_engine must be a FinalReductionReportEngine or None."
            )

        self._analysis_runner = (
            analysis_runner or CouponAnalysisFileRunner()
        )
        self._configuration_importer = (
            configuration_importer
            or ReductionConfigurationJsonImporter()
        )
        self._report_engine = report_engine or FinalReductionReportEngine()

    def run_files(
        self,
        analysis_path: str | Path,
        reduction_path: str | Path,
        *,
        analyzed_at: datetime | None = None,
        reduced_at: datetime | None = None,
    ) -> CouponReductionRun:
        """Run the complete practical workflow from two JSON files."""

        analysis_run = self._analysis_runner.run_file(
            analysis_path,
            analyzed_at=analyzed_at,
        )
        configuration = self._configuration_importer.from_file(
            reduction_path,
            analysis_run,
        )

        return self.run_configuration(
            configuration,
            reduced_at=reduced_at,
        )

    def run_configuration(
        self,
        configuration: ReductionConfigurationDocument,
        *,
        reduced_at: datetime | None = None,
    ) -> CouponReductionRun:
        """Execute one already imported practical configuration."""

        if not isinstance(
            configuration,
            ReductionConfigurationDocument,
        ):
            raise TypeError(
                "configuration must be a ReductionConfigurationDocument."
            )

        resolved_reduced_at = self._resolve_reduced_at(
            reduced_at,
            configuration.analysis_run,
        )

        report = self._report_engine.analyze(
            configuration.analysis_run.base_system,
            configuration.condition_set,
            row_price=configuration.row_price,
        )

        return CouponReductionRun(
            analysis_run=configuration.analysis_run,
            configuration=configuration,
            reduction_report=report,
            reduced_at=resolved_reduced_at,
        )

    @staticmethod
    def _resolve_reduced_at(
        reduced_at: datetime | None,
        analysis_run: CouponAnalysisRun,
    ) -> datetime:
        """Return a timezone-aware time not earlier than analysis."""

        if reduced_at is None:
            now = datetime.now(timezone.utc)
            return max(now, analysis_run.analyzed_at)

        if not isinstance(reduced_at, datetime):
            raise TypeError("reduced_at must be a datetime or None.")

        if reduced_at.tzinfo is None or reduced_at.utcoffset() is None:
            raise ValueError("reduced_at must be timezone-aware.")

        if reduced_at < analysis_run.analyzed_at:
            raise ValueError(
                "reduced_at must not be earlier than analyzed_at."
            )

        return reduced_at