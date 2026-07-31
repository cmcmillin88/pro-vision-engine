"""Engine for deterministic point reduction."""

from src.models.point_reduction_result import (
    PointReductionResult,
    PointReductionRowEvaluation,
)
from src.models.point_reduction_rule import (
    PointReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


class PointReductionEngine:
    """Filters rows by the selected cells' total points."""

    def apply(
        self,
        base_system: BaseReductionSystem,
        rule: PointReductionRule,
    ) -> PointReductionResult:
        """Apply the inclusive point interval to every row."""

        if not isinstance(
            base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "PointReductionEngine requires a "
                "BaseReductionSystem."
            )

        if not isinstance(
            rule,
            PointReductionRule,
        ):
            raise TypeError(
                "PointReductionEngine requires a "
                "PointReductionRule."
            )

        self._validate_rule_against_frame(
            base_system,
            rule,
        )

        evaluations = tuple(
            self._evaluate_row(
                row,
                rule,
            )
            for row in base_system.rows
        )

        return PointReductionResult(
            base_system=base_system,
            rule=rule,
            evaluations=evaluations,
        )

    @staticmethod
    def _evaluate_row(
        row: ReductionRow,
        rule: PointReductionRule,
    ) -> PointReductionRowEvaluation:
        """Evaluate one complete system row."""

        total_points = rule.row_points(
            row
        )

        return PointReductionRowEvaluation(
            row=row,
            total_points=total_points,
            is_approved=(
                rule.min_points
                <= total_points
                <= rule.max_points
            ),
        )

    @staticmethod
    def _validate_rule_against_frame(
        base_system: BaseReductionSystem,
        rule: PointReductionRule,
    ) -> None:
        """Ensure all assigned cells exist in the frame."""

        frame = base_system.frame

        for assignment in rule.assignments:
            if (
                assignment.match_number
                > frame.match_count
            ):
                raise ValueError(
                    "A point assignment references a match "
                    "outside the reduction frame."
                )

            if (
                assignment.outcome
                not in frame.allowed_for_match(
                    assignment.match_number
                )
            ):
                raise ValueError(
                    "A point assignment references an "
                    "outcome outside the turquoise "
                    "reduction frame."
                )