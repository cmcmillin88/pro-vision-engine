"""Orchestrates the complete final reduction report."""

from collections import Counter
from decimal import Decimal

from src.models.final_reduction_report import (
    FinalReductionReport,
    ReductionConditionImpact,
    ReductionRejectionPattern,
)
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.services.reduction_condition_engine import (
    ReductionConditionEngine,
)


class FinalReductionReportEngine:
    """Builds one complete diagnostic and export-ready report."""

    def __init__(
        self,
        condition_engine: ReductionConditionEngine | None = None,
    ) -> None:
        """Store the reusable common condition engine."""

        if (
            condition_engine is not None
            and not isinstance(
                condition_engine,
                ReductionConditionEngine,
            )
        ):
            raise TypeError(
                "condition_engine must be a "
                "ReductionConditionEngine or None."
            )

        self._condition_engine = (
            condition_engine
            if condition_engine is not None
            else ReductionConditionEngine()
        )

    def analyze(
        self,
        base_system: BaseReductionSystem,
        condition_set: ReductionConditionSet,
        *,
        row_price: Decimal | str | int | float | None = None,
    ) -> FinalReductionReport:
        """Apply all conditions and build the complete final report."""

        if not isinstance(
            base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "FinalReductionReportEngine requires a "
                "BaseReductionSystem."
            )

        if not isinstance(
            condition_set,
            ReductionConditionSet,
        ):
            raise TypeError(
                "FinalReductionReportEngine requires a "
                "ReductionConditionSet."
            )

        condition_result = self._condition_engine.apply(
            base_system,
            condition_set,
        )

        impacts = tuple(
            self._build_condition_impact(
                condition_result,
                condition_type,
            )
            for condition_type in condition_set.condition_types
        )

        rejection_patterns = self._build_rejection_patterns(
            condition_result
        )

        return FinalReductionReport(
            condition_result=condition_result,
            condition_impacts=impacts,
            rejection_patterns=rejection_patterns,
            row_price=row_price,
        )

    @staticmethod
    def _build_condition_impact(
        condition_result,
        condition_type: ReductionConditionType,
    ) -> ReductionConditionImpact:
        """Build one condition's independent and exclusive impact."""

        approved_count = (
            condition_result.approved_count_for_condition(
                condition_type
            )
        )
        rejected_count = (
            condition_result.original_row_count
            - approved_count
        )
        exclusive_count = sum(
            evaluation.rejected_condition_types
            == (
                condition_type,
            )
            for evaluation in condition_result.evaluations
        )

        return ReductionConditionImpact(
            condition_type=condition_type,
            original_row_count=(
                condition_result.original_row_count
            ),
            independently_approved_count=approved_count,
            independently_rejected_count=rejected_count,
            exclusive_rejection_count=exclusive_count,
        )

    @staticmethod
    def _build_rejection_patterns(
        condition_result,
    ) -> tuple[ReductionRejectionPattern, ...]:
        """Group rejected rows by exact failed-condition signature."""

        counts = Counter(
            evaluation.rejected_condition_types
            for evaluation in condition_result.rejected_evaluations
        )
        condition_index = {
            condition_type: index
            for index, condition_type in enumerate(
                ReductionConditionType.ordered()
            )
        }

        ordered_items = sorted(
            counts.items(),
            key=lambda item: (
                -item[1],
                tuple(
                    condition_index[condition_type]
                    for condition_type in item[0]
                ),
            ),
        )

        return tuple(
            ReductionRejectionPattern(
                condition_types=condition_types,
                row_count=row_count,
                total_rejected_row_count=(
                    condition_result.rejected_count
                ),
            )
            for condition_types, row_count in ordered_items
        )