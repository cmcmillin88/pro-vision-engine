"""Engine for applying one color-based MIN/MAX condition."""

from src.models.color_reduction_result import (
    ColorReductionResult,
    ColorReductionRowEvaluation,
)
from src.models.color_reduction_rule import (
    ColorReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
    ReductionFrame,
)
from src.models.reduction_row import ReductionRow


class ColorReductionEngine:
    """Filters a base system with one independent color rule."""

    def apply(
        self,
        base_system: BaseReductionSystem,
        rule: ColorReductionRule,
    ) -> ColorReductionResult:
        """Apply one color rule to every base-system row."""

        if not isinstance(
            base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "ColorReductionEngine requires a "
                "BaseReductionSystem."
            )

        if not isinstance(
            rule,
            ColorReductionRule,
        ):
            raise TypeError(
                "ColorReductionEngine requires a "
                "ColorReductionRule."
            )

        self._validate_rule_against_frame(
            rule,
            base_system.frame,
        )

        evaluations = tuple(
            self._evaluate_row(
                row,
                rule,
            )
            for row in base_system.rows
        )

        return ColorReductionResult(
            base_system=base_system,
            rule=rule,
            evaluations=evaluations,
        )

    @staticmethod
    def _evaluate_row(
        row: ReductionRow,
        rule: ColorReductionRule,
    ) -> ColorReductionRowEvaluation:
        """Evaluate one row against inclusive MIN/MAX."""

        hit_count = rule.hit_count(
            row
        )

        return ColorReductionRowEvaluation(
            row=row,
            hit_count=hit_count,
            is_approved=(
                rule.min_hits
                <= hit_count
                <= rule.max_hits
            ),
        )

    @staticmethod
    def _validate_rule_against_frame(
        rule: ColorReductionRule,
        frame: ReductionFrame,
    ) -> None:
        """Ensure every colored cell exists in the frame."""

        for cell in rule.cells:
            if cell.match_number > frame.match_count:
                raise ValueError(
                    "A colored cell references a match "
                    "outside the reduction frame."
                )

            if (
                cell.outcome
                not in frame.allowed_for_match(
                    cell.match_number
                )
            ):
                raise ValueError(
                    "Every colored outcome must already "
                    "exist in the turquoise reduction frame."
                )