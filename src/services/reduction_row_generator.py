"""Deterministic mathematical row generation for reduction frames."""

from collections.abc import Iterator
from itertools import product

from src.models.final_coupon_analysis import (
    FinalCouponAnalysisReport,
)
from src.models.reduction_capacity import (
    ReductionCapacityAssessment,
    ReductionCapacityPolicy,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
    ReductionFrame,
)
from src.models.reduction_row import ReductionRow
from src.services.reduction_capacity_planner import (
    ReductionCapacityPlanner,
)


class ReductionRowGenerator:
    """Generates rows with exact preflight capacity protection."""

    def __init__(
        self,
        maximum_materialized_rows: int = 100_000,
        warning_row_count: int | None = None,
    ) -> None:
        """Create a row generator with warning and hard limits."""

        if isinstance(
            maximum_materialized_rows,
            bool,
        ) or not isinstance(
            maximum_materialized_rows,
            int,
        ):
            raise TypeError(
                "maximum_materialized_rows must be "
                "an integer."
            )

        if maximum_materialized_rows <= 0:
            raise ValueError(
                "maximum_materialized_rows must be "
                "greater than zero."
            )

        resolved_warning = (
            min(
                25_000,
                maximum_materialized_rows,
            )
            if warning_row_count is None
            else warning_row_count
        )

        policy = ReductionCapacityPolicy(
            warning_row_count=resolved_warning,
            maximum_materialized_rows=(
                maximum_materialized_rows
            ),
        )

        self._capacity_planner = ReductionCapacityPlanner(
            policy
        )

    @property
    def maximum_materialized_rows(self) -> int:
        """Return the configured hard materialization limit."""

        return (
            self.capacity_policy.maximum_materialized_rows
        )

    @property
    def warning_row_count(self) -> int:
        """Return the configured warning threshold."""

        return self.capacity_policy.warning_row_count

    @property
    def capacity_policy(self) -> ReductionCapacityPolicy:
        """Return the complete active capacity policy."""

        return self._capacity_planner.policy

    def assess(
        self,
        frame: ReductionFrame,
    ) -> ReductionCapacityAssessment:
        """Assess exact frame capacity without generating any rows."""

        return self._capacity_planner.assess(
            frame
        )

    def generate(
        self,
        frame: ReductionFrame,
    ) -> BaseReductionSystem:
        """Materialize every row after successful preflight."""

        _, system = self.generate_with_assessment(
            frame
        )

        return system

    def generate_with_assessment(
        self,
        frame: ReductionFrame,
    ) -> tuple[
        ReductionCapacityAssessment,
        BaseReductionSystem,
    ]:
        """Return exact preflight metadata and the materialized system."""

        assessment = (
            self._capacity_planner
            .require_materializable(
                frame
            )
        )

        rows = tuple(
            self.iter_rows(
                frame
            )
        )

        return (
            assessment,
            BaseReductionSystem(
                frame=frame,
                rows=rows,
            ),
        )

    def generate_from_coupon_analysis(
        self,
        coupon_analysis: FinalCouponAnalysisReport,
    ) -> BaseReductionSystem:
        """Build and generate the frame from coupon analysis."""

        frame = ReductionFrame.from_coupon_analysis(
            coupon_analysis
        )

        return self.generate(
            frame
        )

    def iter_rows(
        self,
        frame: ReductionFrame,
    ) -> Iterator[ReductionRow]:
        """Return a lazy deterministic iterator without hard-limit use."""

        self._validate_frame(
            frame
        )

        combinations = product(
            *frame.allowed_outcomes
        )

        return (
            ReductionRow(
                outcomes=tuple(
                    combination
                )
            )
            for combination in combinations
        )

    @staticmethod
    def _validate_frame(
        frame: object,
    ) -> None:
        """Validate one frame dependency."""

        if not isinstance(
            frame,
            ReductionFrame,
        ):
            raise TypeError(
                "ReductionRowGenerator requires "
                "a ReductionFrame."
            )