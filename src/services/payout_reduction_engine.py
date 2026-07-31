"""Engine for transparent estimated-payout reduction."""

from src.models.payout_reduction_result import (
    PayoutReductionResult,
    PayoutReductionRowEvaluation,
)
from src.models.payout_reduction_rule import (
    PayoutReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


class PayoutReductionEngine:
    """Filters base-system rows by frozen payout forecasts."""

    def apply(
        self,
        base_system: BaseReductionSystem,
        rule: PayoutReductionRule,
    ) -> PayoutReductionResult:
        """Evaluate every base row against inclusive MIN/MAX."""

        if not isinstance(
            base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "PayoutReductionEngine requires a "
                "BaseReductionSystem."
            )

        if not isinstance(
            rule,
            PayoutReductionRule,
        ):
            raise TypeError(
                "PayoutReductionEngine requires a "
                "PayoutReductionRule."
            )

        if (
            rule.snapshot.match_count
            != base_system.frame.match_count
        ):
            raise ValueError(
                "The payout snapshot must contain exactly "
                "one complete public distribution per "
                "frame match."
            )

        evaluations = tuple(
            self._evaluate_row(
                row,
                rule,
            )
            for row in base_system.rows
        )

        return PayoutReductionResult(
            base_system=base_system,
            rule=rule,
            evaluations=evaluations,
        )

    @staticmethod
    def _evaluate_row(
        row: ReductionRow,
        rule: PayoutReductionRule,
    ) -> PayoutReductionRowEvaluation:
        """Evaluate one row against the frozen forecast."""

        snapshot = rule.snapshot
        row_share = snapshot.row_share(
            row
        )
        expected_units = snapshot.expected_winning_units(
            row
        )
        estimated_payout = snapshot.estimated_payout(
            row
        )

        return PayoutReductionRowEvaluation(
            row=row,
            row_share=row_share,
            expected_winning_units=expected_units,
            estimated_payout=estimated_payout,
            is_approved=rule.contains(
                estimated_payout
            ),
        )