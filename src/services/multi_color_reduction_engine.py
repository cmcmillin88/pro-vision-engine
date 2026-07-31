"""Engine for multiple simultaneous color-reduction rules."""

from src.models.color_reduction_result import (
    ColorReductionResult,
)
from src.models.color_reduction_rule import (
    ColorReductionRule,
)
from src.models.color_reduction_rule_set import (
    ColorReductionRuleSet,
)
from src.models.multi_color_reduction_result import (
    ColorRuleRowEvaluation,
    MultiColorReductionResult,
    MultiColorReductionRowEvaluation,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.services.color_reduction_engine import (
    ColorReductionEngine,
)


class MultiColorReductionEngine:
    """Applies independent color rules with combined AND logic."""

    def __init__(
        self,
        single_color_engine: ColorReductionEngine | None = None,
    ) -> None:
        """Create the combined engine."""

        if single_color_engine is None:
            single_color_engine = ColorReductionEngine()

        if not isinstance(
            single_color_engine,
            ColorReductionEngine,
        ):
            raise TypeError(
                "single_color_engine must be a "
                "ColorReductionEngine."
            )

        self._single_color_engine = single_color_engine

    def apply(
        self,
        base_system: BaseReductionSystem,
        rule_set: ColorReductionRuleSet,
    ) -> MultiColorReductionResult:
        """Apply every color independently and combine with AND."""

        if not isinstance(
            base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "MultiColorReductionEngine requires a "
                "BaseReductionSystem."
            )

        if not isinstance(
            rule_set,
            ColorReductionRuleSet,
        ):
            raise TypeError(
                "MultiColorReductionEngine requires a "
                "ColorReductionRuleSet."
            )

        single_color_results = tuple(
            self._single_color_engine.apply(
                base_system,
                rule,
            )
            for rule in rule_set.rules
        )

        evaluations = tuple(
            self._combine_row_evaluations(
                row_index,
                single_color_results,
            )
            for row_index in range(
                base_system.row_count
            )
        )

        return MultiColorReductionResult(
            base_system=base_system,
            rule_set=rule_set,
            evaluations=evaluations,
        )

    def apply_rules(
        self,
        base_system: BaseReductionSystem,
        rules: tuple[
            ColorReductionRule,
            ...,
        ],
    ) -> MultiColorReductionResult:
        """Create a rule set and apply it in one call."""

        return self.apply(
            base_system,
            ColorReductionRuleSet(
                rules=rules
            ),
        )

    @staticmethod
    def _combine_row_evaluations(
        row_index: int,
        single_color_results: tuple[
            ColorReductionResult,
            ...,
        ],
    ) -> MultiColorReductionRowEvaluation:
        """Combine independent results for one base row."""

        first_result = single_color_results[0]
        row = first_result.evaluations[
            row_index
        ].row

        rule_evaluations = tuple(
            ColorRuleRowEvaluation(
                rule=result.rule,
                hit_count=result.evaluations[
                    row_index
                ].hit_count,
            )
            for result in single_color_results
        )

        return MultiColorReductionRowEvaluation(
            row=row,
            rule_evaluations=rule_evaluations,
        )