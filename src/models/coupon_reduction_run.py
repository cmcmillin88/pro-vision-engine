"""Complete practical result chain for one analyzed and reduced coupon."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import ClassVar

from src.models.coupon_analysis_run import CouponAnalysisRun
from src.models.final_reduction_report import FinalReductionReport
from src.models.game_type import GameType
from src.models.reduction_configuration_document import (
    ReductionConfigurationDocument,
)
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class CouponReductionRun:
    """Links practical analysis, reduction configuration and final report."""

    CURRENT_SCHEMA_VERSION: ClassVar[str] = "p13-reduction-result-v1"

    analysis_run: CouponAnalysisRun
    configuration: ReductionConfigurationDocument
    reduction_report: FinalReductionReport
    reduced_at: datetime
    schema_version: str = CURRENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Normalize and validate the complete practical reduction chain."""

        if not isinstance(self.schema_version, str):
            raise TypeError("schema_version must be a string.")

        normalized_version = self.schema_version.strip()

        if normalized_version != self.CURRENT_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported coupon-reduction result schema version: "
                f"{normalized_version!r}."
            )

        object.__setattr__(self, "schema_version", normalized_version)

        if not isinstance(self.analysis_run, CouponAnalysisRun):
            raise TypeError("analysis_run must be a CouponAnalysisRun.")

        if not isinstance(
            self.configuration,
            ReductionConfigurationDocument,
        ):
            raise TypeError(
                "configuration must be a ReductionConfigurationDocument."
            )

        if not isinstance(self.reduction_report, FinalReductionReport):
            raise TypeError(
                "reduction_report must be a FinalReductionReport."
            )

        if not isinstance(self.reduced_at, datetime):
            raise TypeError("reduced_at must be a datetime.")

        if (
            self.reduced_at.tzinfo is None
            or self.reduced_at.utcoffset() is None
        ):
            raise ValueError("reduced_at must be timezone-aware.")

        if self.reduced_at < self.analysis_run.analyzed_at:
            raise ValueError(
                "reduced_at must not be earlier than analyzed_at."
            )

        if self.configuration.analysis_run != self.analysis_run:
            raise ValueError(
                "configuration must belong to the supplied analysis_run."
            )

        if self.reduction_report.base_system != self.analysis_run.base_system:
            raise ValueError(
                "reduction_report must use the analysis run's base system."
            )

        if (
            self.reduction_report.condition_set
            != self.configuration.condition_set
        ):
            raise ValueError(
                "reduction_report must use the configuration's "
                "condition set."
            )

        if self.reduction_report.row_price != self.configuration.row_price:
            raise ValueError(
                "reduction_report row price must match the configuration."
            )

    @property
    def coupon_id(self) -> str | None:
        """Return the analyzed coupon identifier."""

        return self.analysis_run.coupon_id

    @property
    def game_type(self) -> GameType:
        """Return the analyzed game type."""

        return self.analysis_run.game_type

    @property
    def match_count(self) -> int:
        """Return the coupon match count."""

        return self.analysis_run.match_count

    @property
    def frame_pattern(self) -> str:
        """Return the turquoise frame pattern."""

        return self.analysis_run.recommendation_pattern

    @property
    def condition_pattern(self) -> str:
        """Return the complete practical reduction condition pattern."""

        return self.configuration.condition_pattern

    @property
    def condition_count(self) -> int:
        """Return the number of active condition groups."""

        return self.configuration.condition_count

    @property
    def atomic_condition_count(self) -> int:
        """Return the number of independently checked conditions."""

        return self.configuration.atomic_condition_count

    @property
    def row_price(self) -> Decimal:
        """Return the configured row price."""

        return self.configuration.row_price

    @property
    def original_row_count(self) -> int:
        """Return the complete turquoise base-system size."""

        return self.reduction_report.original_row_count

    @property
    def approved_row_count(self) -> int:
        """Return the final surviving row count."""

        return self.reduction_report.approved_count

    @property
    def rejected_row_count(self) -> int:
        """Return the final removed row count."""

        return self.reduction_report.rejected_count

    @property
    def approved_rows(self) -> tuple[ReductionRow, ...]:
        """Return surviving rows in deterministic order."""

        return self.reduction_report.approved_rows

    @property
    def approved_symbols(self) -> tuple[str, ...]:
        """Return surviving rows as compact symbols."""

        return self.reduction_report.approved_symbols

    @property
    def original_cost(self) -> Decimal:
        """Return the cost of the unreduced frame."""

        cost = self.reduction_report.original_cost

        if cost is None:
            raise RuntimeError("A practical reduction run requires row price.")

        return cost

    @property
    def final_cost(self) -> Decimal:
        """Return the final reduced system cost."""

        cost = self.reduction_report.final_cost

        if cost is None:
            raise RuntimeError("A practical reduction run requires row price.")

        return cost

    @property
    def saved_cost(self) -> Decimal:
        """Return the monetary reduction compared with the full frame."""

        value = self.reduction_report.saved_cost

        if value is None:
            raise RuntimeError("A practical reduction run requires row price.")

        return value

    @property
    def is_empty(self) -> bool:
        """Return whether every turquoise row was removed."""

        return self.reduction_report.is_empty

    @property
    def summary_line(self) -> str:
        """Return a compact practical reduction summary."""

        coupon_text = self.coupon_id if self.coupon_id is not None else "utan id"

        return (
            f"{self.game_type.display_name} | "
            f"Kupong {coupon_text} | "
            f"Villkor {self.condition_count} | "
            f"Ursprung {self.original_row_count} | "
            f"Kvar {self.approved_row_count} | "
            f"Bort {self.rejected_row_count} | "
            f"Kostnad {self.final_cost} kr | "
            f"Resultat {self.schema_version}"
        )