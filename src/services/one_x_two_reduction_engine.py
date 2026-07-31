"""Engine for total 1-X-2 outcome-count reduction."""

from src.models.one_x_two_reduction_result import (
    OneXTwoReductionResult,
    OneXTwoReductionRowEvaluation,
    OutcomeCountRowEvaluation,
)
from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


class OneXTwoReductionEngine:
    """Filters rows by total counts of 1, X and 2."""

    def apply(
        self,
        base_system: BaseReductionSystem,
        rule: OneXTwoReductionRule,
    ) -> OneXTwoReductionResult:
        """Apply every active count condition to every row."""

        if not isinstance(
            base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "OneXTwoReductionEngine requires a "
                "BaseReductionSystem."
            )

        if not isinstance(
            rule,
            OneXTwoReductionRule,
        ):
            raise TypeError(
                "OneXTwoReductionEngine requires a "
                "OneXTwoReductionRule."
            )

        self._validate_rule_against_system(
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

        return OneXTwoReductionResult(
            base_system=base_system,
            rule=rule,
            evaluations=evaluations,
        )

    @staticmethod
    def _evaluate_row(
        row: ReductionRow,
        rule: OneXTwoReductionRule,
    ) -> OneXTwoReductionRowEvaluation:
        """Evaluate one complete row."""

        condition_evaluations = tuple(
            OutcomeCountRowEvaluation(
                condition=condition,
                count=condition.count_in(
                    row
                ),
            )
            for condition in rule.conditions
        )

        return OneXTwoReductionRowEvaluation(
            row=row,
            condition_evaluations=condition_evaluations,
        )

    @staticmethod
    def _validate_rule_against_system(
        base_system: BaseReductionSystem,
        rule: OneXTwoReductionRule,
    ) -> None:
        """Validate count bounds against coupon length."""

        match_count = base_system.frame.match_count

        for condition in rule.conditions:
            if condition.max_count > match_count:
                raise ValueError(
                    "A 1X2 condition's MIN/MAX bounds "
                    "must not exceed the frame's "
                    "match count."
                )