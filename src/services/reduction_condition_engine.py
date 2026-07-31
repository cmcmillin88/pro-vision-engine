"""Common engine for deterministic reduction conditions."""

from src.models.reduction_condition_result import (
    ReductionConditionEvaluation,
    ReductionConditionResult,
    ReductionConditionRowEvaluation,
    ReductionMetricEvaluation,
)
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


class ReductionConditionEngine:
    """Applies active conditions using common AND logic."""

    def apply(
        self,
        base_system: BaseReductionSystem,
        condition_set: ReductionConditionSet,
    ) -> ReductionConditionResult:
        """Evaluate every condition against every row."""

        if not isinstance(
            base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "ReductionConditionEngine requires a "
                "BaseReductionSystem."
            )

        if not isinstance(
            condition_set,
            ReductionConditionSet,
        ):
            raise TypeError(
                "ReductionConditionEngine requires a "
                "ReductionConditionSet."
            )

        self._validate_conditions_against_frame(
            base_system,
            condition_set,
        )

        evaluations = tuple(
            self._evaluate_row(
                row,
                condition_set,
            )
            for row in base_system.rows
        )

        return ReductionConditionResult(
            base_system=base_system,
            condition_set=condition_set,
            evaluations=evaluations,
        )

    @classmethod
    def _evaluate_row(
        cls,
        row: ReductionRow,
        condition_set: ReductionConditionSet,
    ) -> ReductionConditionRowEvaluation:
        """Evaluate all active conditions for one row."""

        evaluations: list[
            ReductionConditionEvaluation
        ] = []

        if condition_set.color_rules:
            evaluations.append(
                cls._evaluate_colors(
                    row,
                    condition_set,
                )
            )

        if condition_set.one_x_two_rule is not None:
            evaluations.append(
                cls._evaluate_one_x_two(
                    row,
                    condition_set,
                )
            )

        if condition_set.point_rule is not None:
            evaluations.append(
                cls._evaluate_points(
                    row,
                    condition_set,
                )
            )

        if condition_set.odds_rule is not None:
            evaluations.append(
                cls._evaluate_odds(
                    row,
                    condition_set,
                )
            )

        if condition_set.payout_rule is not None:
            evaluations.append(
                cls._evaluate_payout(
                    row,
                    condition_set,
                )
            )

        return ReductionConditionRowEvaluation(
            row=row,
            condition_evaluations=tuple(
                evaluations
            ),
        )

    @staticmethod
    def _evaluate_colors(
        row: ReductionRow,
        condition_set: ReductionConditionSet,
    ) -> ReductionConditionEvaluation:
        """Evaluate each active color independently."""

        metrics = tuple(
            ReductionMetricEvaluation(
                label=rule.color.display_name,
                observed_value=rule.hit_count(
                    row
                ),
                minimum_value=rule.min_hits,
                maximum_value=rule.max_hits,
            )
            for rule in condition_set.color_rules
        )

        return ReductionConditionEvaluation(
            condition_type=ReductionConditionType.COLOR,
            metrics=metrics,
        )

    @staticmethod
    def _evaluate_one_x_two(
        row: ReductionRow,
        condition_set: ReductionConditionSet,
    ) -> ReductionConditionEvaluation:
        """Evaluate active 1-X-2 count conditions."""

        rule = condition_set.one_x_two_rule

        if rule is None:
            raise RuntimeError(
                "No 1X2 rule is active."
            )

        metrics = tuple(
            ReductionMetricEvaluation(
                label=condition.outcome.value,
                observed_value=condition.count_in(
                    row
                ),
                minimum_value=condition.min_count,
                maximum_value=condition.max_count,
            )
            for condition in rule.conditions
        )

        return ReductionConditionEvaluation(
            condition_type=(
                ReductionConditionType.ONE_X_TWO
            ),
            metrics=metrics,
        )

    @staticmethod
    def _evaluate_points(
        row: ReductionRow,
        condition_set: ReductionConditionSet,
    ) -> ReductionConditionEvaluation:
        """Evaluate the row's total selected-cell points."""

        rule = condition_set.point_rule

        if rule is None:
            raise RuntimeError(
                "No point rule is active."
            )

        metric = ReductionMetricEvaluation(
            label="Poäng",
            observed_value=rule.row_points(
                row
            ),
            minimum_value=rule.min_points,
            maximum_value=rule.max_points,
        )

        return ReductionConditionEvaluation(
            condition_type=ReductionConditionType.POINT,
            metrics=(
                metric,
            ),
        )

    @staticmethod
    def _evaluate_odds(
        row: ReductionRow,
        condition_set: ReductionConditionSet,
    ) -> ReductionConditionEvaluation:
        """Evaluate frozen total odds with an exclusive MAX."""

        rule = condition_set.odds_rule

        if rule is None:
            raise RuntimeError(
                "No odds rule is active."
            )

        metric = ReductionMetricEvaluation(
            label="Totalodds",
            observed_value=rule.total_odds(
                row
            ),
            minimum_value=rule.min_total_odds,
            maximum_value=rule.max_total_odds,
            maximum_inclusive=False,
        )

        return ReductionConditionEvaluation(
            condition_type=ReductionConditionType.ODDS,
            metrics=(
                metric,
            ),
        )

    @staticmethod
    def _evaluate_payout(
        row: ReductionRow,
        condition_set: ReductionConditionSet,
    ) -> ReductionConditionEvaluation:
        """Evaluate the frozen transparent payout forecast."""

        rule = condition_set.payout_rule

        if rule is None:
            raise RuntimeError(
                "No payout rule is active."
            )

        metric = ReductionMetricEvaluation(
            label="Utdelning",
            observed_value=rule.estimated_payout(
                row
            ),
            minimum_value=rule.min_estimated_payout,
            maximum_value=rule.max_estimated_payout,
        )

        return ReductionConditionEvaluation(
            condition_type=ReductionConditionType.PAYOUT,
            metrics=(
                metric,
            ),
        )

    @classmethod
    def _validate_conditions_against_frame(
        cls,
        base_system: BaseReductionSystem,
        condition_set: ReductionConditionSet,
    ) -> None:
        """Validate all conditions against the frame."""

        frame = base_system.frame

        for rule in condition_set.color_rules:
            for cell in rule.cells:
                if cell.match_number > frame.match_count:
                    raise ValueError(
                        "A color cell references a match "
                        "outside the reduction frame."
                    )

                if (
                    cell.outcome
                    not in frame.allowed_for_match(
                        cell.match_number
                    )
                ):
                    raise ValueError(
                        "A color cell references an outcome "
                        "outside the turquoise reduction "
                        "frame."
                    )

        if condition_set.one_x_two_rule is not None:
            for condition in (
                condition_set.one_x_two_rule.conditions
            ):
                if (
                    condition.max_count
                    > frame.match_count
                ):
                    raise ValueError(
                        "A 1X2 condition maximum exceeds "
                        "the reduction frame's match count."
                    )

        if condition_set.point_rule is not None:
            for assignment in (
                condition_set.point_rule.assignments
            ):
                if (
                    assignment.match_number
                    > frame.match_count
                ):
                    raise ValueError(
                        "A point assignment references a "
                        "match outside the reduction frame."
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

        if condition_set.odds_rule is not None:
            if (
                condition_set.odds_rule.snapshot.match_count
                != frame.match_count
            ):
                raise ValueError(
                    "The odds snapshot must contain exactly "
                    "one complete 1-X-2 market per frame match."
                )
        if condition_set.payout_rule is not None:
            if (
                condition_set.payout_rule.snapshot.match_count
                != frame.match_count
            ):
                raise ValueError(
                    "The payout snapshot must contain exactly "
                    "one complete public distribution per "
                    "frame match."
                )