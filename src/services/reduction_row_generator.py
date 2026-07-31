"""Deterministic mathematical row generation for reduction frames."""

from collections.abc import Iterator
from itertools import product

from src.models.final_coupon_analysis import (
    FinalCouponAnalysisReport,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
    ReductionFrame,
)
from src.models.reduction_row import ReductionRow


class ReductionRowGenerator:
    """Generates every mathematical row in a frame."""

    def __init__(
        self,
        maximum_materialized_rows: int = 100_000,
    ) -> None:
        """Create a row generator with a memory guardrail."""

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

        self._maximum_materialized_rows = (
            maximum_materialized_rows
        )

    @property
    def maximum_materialized_rows(self) -> int:
        """Return the configured materialization limit."""

        return self._maximum_materialized_rows

    def generate(
        self,
        frame: ReductionFrame,
    ) -> BaseReductionSystem:
        """Materialize every row in one frame."""

        self._validate_frame(
            frame
        )

        if (
            frame.expected_row_count
            > self._maximum_materialized_rows
        ):
            raise ValueError(
                "Frame contains "
                f"{frame.expected_row_count} rows, "
                "which exceeds the configured "
                "materialization limit of "
                f"{self._maximum_materialized_rows}."
            )

        rows = tuple(
            self.iter_rows(
                frame
            )
        )

        return BaseReductionSystem(
            frame=frame,
            rows=rows,
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
        """Return a lazy deterministic iterator over frame rows."""

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