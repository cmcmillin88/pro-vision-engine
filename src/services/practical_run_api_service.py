"""In-memory service for practical analysis and reduction API runs."""

from collections.abc import Mapping
from typing import Any

from src.exporters.coupon_analysis_result_json_exporter import (
    CouponAnalysisResultJsonExporter,
)
from src.exporters.coupon_reduction_result_json_exporter import (
    CouponReductionResultJsonExporter,
)
from src.importer.coupon_analysis_json_importer import (
    CouponAnalysisJsonImporter,
)
from src.importer.reduction_configuration_json_importer import (
    ReductionConfigurationJsonImporter,
)
from src.services.coupon_analysis_file_runner import (
    CouponAnalysisFileRunner,
)
from src.services.coupon_reduction_file_runner import (
    CouponReductionFileRunner,
)


class PracticalRunApiService:
    """Runs practical Project 13 workflows without temporary files."""

    def __init__(
        self,
        analysis_importer: CouponAnalysisJsonImporter | None = None,
        analysis_runner: CouponAnalysisFileRunner | None = None,
        reduction_importer: (
            ReductionConfigurationJsonImporter | None
        ) = None,
        reduction_runner: CouponReductionFileRunner | None = None,
        analysis_exporter: (
            CouponAnalysisResultJsonExporter | None
        ) = None,
        reduction_exporter: (
            CouponReductionResultJsonExporter | None
        ) = None,
    ) -> None:
        """Create the in-memory practical workflow service."""

        dependencies = (
            (
                "analysis_importer",
                analysis_importer,
                CouponAnalysisJsonImporter,
            ),
            (
                "analysis_runner",
                analysis_runner,
                CouponAnalysisFileRunner,
            ),
            (
                "reduction_importer",
                reduction_importer,
                ReductionConfigurationJsonImporter,
            ),
            (
                "reduction_runner",
                reduction_runner,
                CouponReductionFileRunner,
            ),
            (
                "analysis_exporter",
                analysis_exporter,
                CouponAnalysisResultJsonExporter,
            ),
            (
                "reduction_exporter",
                reduction_exporter,
                CouponReductionResultJsonExporter,
            ),
        )

        for field_name, value, expected_type in dependencies:
            if value is not None and not isinstance(
                value,
                expected_type,
            ):
                raise TypeError(
                    f"{field_name} must be a "
                    f"{expected_type.__name__} or None."
                )

        self._analysis_importer = (
            analysis_importer
            or CouponAnalysisJsonImporter()
        )
        self._analysis_runner = (
            analysis_runner
            or CouponAnalysisFileRunner()
        )
        self._reduction_importer = (
            reduction_importer
            or ReductionConfigurationJsonImporter()
        )
        self._reduction_runner = (
            reduction_runner
            or CouponReductionFileRunner()
        )
        self._analysis_exporter = (
            analysis_exporter
            or CouponAnalysisResultJsonExporter()
        )
        self._reduction_exporter = (
            reduction_exporter
            or CouponReductionResultJsonExporter()
        )

    def create_analysis_run(
        self,
        analysis_document: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Import, analyze and export one in-memory coupon document."""

        self._validate_mapping(
            analysis_document,
            field_name="analysis_document",
        )

        document = self._analysis_importer.from_dict(
            analysis_document,
            source_name="api",
        )
        analysis_run = self._analysis_runner.run_document(
            document
        )

        return self._analysis_exporter.to_dict(
            analysis_run
        )

    def create_reduction_run(
        self,
        analysis_document: Mapping[str, Any],
        reduction_configuration: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Run analysis and reduction from two in-memory documents."""

        self._validate_mapping(
            analysis_document,
            field_name="analysis_document",
        )
        self._validate_mapping(
            reduction_configuration,
            field_name="reduction_configuration",
        )

        document = self._analysis_importer.from_dict(
            analysis_document,
            source_name="api",
        )
        analysis_run = self._analysis_runner.run_document(
            document
        )
        configuration = self._reduction_importer.from_dict(
            reduction_configuration,
            analysis_run,
            source_name="api",
        )
        reduction_run = self._reduction_runner.run_configuration(
            configuration
        )

        return self._reduction_exporter.to_dict(
            reduction_run
        )

    @staticmethod
    def _validate_mapping(
        value: object,
        *,
        field_name: str,
    ) -> None:
        """Validate one decoded JSON object."""

        if not isinstance(
            value,
            Mapping,
        ):
            raise TypeError(
                f"{field_name} must be a mapping."
            )