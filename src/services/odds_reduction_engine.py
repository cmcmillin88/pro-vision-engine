"""Engine for deterministic frozen total-odds reduction."""

from src.models.odds_reduction_result import (
    OddsReductionResult,
    OddsReductionRowEvaluation,
)
from src.models.odds_reduction_rule import (
    OddsReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)


class OddsReductionEngine:
    """Filters base-system rows by frozen total odds."""

    def apply(
        self,
        base_system: BaseReductionSystem,
        rule: OddsReductionRule,
    ) -> OddsReductionResult:
        """Evaluate every base row against [MIN, MAX)."""

        if not isinstance(
            base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "OddsReductionEngine requires a "
                "BaseReductionSystem."
            )

        if not isinstance(
            rule,
            OddsReductionRule,
        ):
            raise TypeError(
                "OddsReductionEngine requires an "
                "OddsReductionRule."
            )

        if (
            rule.snapshot.match_count
            != base_system.frame.match_count
        ):
            raise ValueError(
                "The odds snapshot must contain exactly "
                "one complete 1-X-2 market per frame match."
            )

        evaluations = tuple(
            self._evaluate_row(
                row,
                rule,
            )
            for row in base_system.rows
        )

        return OddsReductionResult(
            base_system=base_system,
            rule=rule,
            evaluations=evaluations,
        )

    @staticmethod
    def _evaluate_row(
        row,
        rule: OddsReductionRule,
    ) -> OddsReductionRowEvaluation:
        """Evaluate one row against the frozen interval."""

        total_odds = rule.total_odds(
            row
        )

        return OddsReductionRowEvaluation(
            row=row,
            total_odds=total_odds,
            is_approved=rule.contains(
                total_odds
            ),
        )