"""Result models for total 1-X-2 outcome-count reduction."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
    OutcomeCountCondition,
)
from src.models.outcome import Outcome
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class OutcomeCountRowEvaluation:
    """Contains one outcome count for one row."""

    condition: OutcomeCountCondition
    count: int

    def __post_init__(self) -> None:
        """Validate one condition evaluation."""

        if not isinstance(
            self.condition,
            OutcomeCountCondition,
        ):
            raise TypeError(
                "condition must be an "
                "OutcomeCountCondition."
            )

        if isinstance(
            self.count,
            bool,
        ) or not isinstance(
            self.count,
            int,
        ):
            raise TypeError(
                "count must be an integer."
            )

        if self.count < 0:
            raise ValueError(
                "count must not be negative."
            )

    @property
    def outcome(self) -> Outcome:
        """Return the evaluated outcome."""

        return self.condition.outcome

    @property
    def is_approved(self) -> bool:
        """Return whether the count is inside MIN/MAX."""

        return (
            self.condition.min_count
            <= self.count
            <= self.condition.max_count
        )


@dataclass(frozen=True, slots=True)
class OneXTwoReductionRowEvaluation:
    """Contains all active 1X2 evaluations for one row."""

    row: ReductionRow
    condition_evaluations: tuple[
        OutcomeCountRowEvaluation,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete row evaluation."""

        if not isinstance(
            self.row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        if not isinstance(
            self.condition_evaluations,
            tuple,
        ):
            raise TypeError(
                "condition_evaluations must be a tuple."
            )

        if not self.condition_evaluations:
            raise ValueError(
                "At least one condition evaluation "
                "is required."
            )

        for evaluation in self.condition_evaluations:
            if not isinstance(
                evaluation,
                OutcomeCountRowEvaluation,
            ):
                raise TypeError(
                    "condition_evaluations may only contain "
                    "OutcomeCountRowEvaluation objects."
                )

        outcomes = tuple(
            evaluation.outcome
            for evaluation in self.condition_evaluations
        )

        if len(
            set(
                outcomes
            )
        ) != len(
            outcomes
        ):
            raise ValueError(
                "A row evaluation may only contain "
                "one evaluation per outcome."
            )

        expected_order = tuple(
            outcome
            for outcome in Outcome.ordered()
            if outcome in outcomes
        )

        if outcomes != expected_order:
            raise ValueError(
                "Condition evaluations must follow "
                "official 1-X-2 order."
            )

        for evaluation in self.condition_evaluations:
            expected_count = (
                evaluation.condition.count_in(
                    self.row
                )
            )

            if evaluation.count != expected_count:
                raise ValueError(
                    "Evaluation count does not match "
                    "the row and condition."
                )

    @property
    def outcomes(self) -> tuple[Outcome, ...]:
        """Return evaluated outcomes in stored order."""

        return tuple(
            evaluation.outcome
            for evaluation in self.condition_evaluations
        )

    @property
    def conditions(
        self,
    ) -> tuple[OutcomeCountCondition, ...]:
        """Return evaluated conditions in stored order."""

        return tuple(
            evaluation.condition
            for evaluation in self.condition_evaluations
        )

    @property
    def is_approved(self) -> bool:
        """Return whether every active condition approves."""

        return all(
            evaluation.is_approved
            for evaluation in self.condition_evaluations
        )

    @property
    def approved_outcomes(
        self,
    ) -> tuple[Outcome, ...]:
        """Return independently approved outcomes."""

        return tuple(
            evaluation.outcome
            for evaluation in self.condition_evaluations
            if evaluation.is_approved
        )

    @property
    def rejected_outcomes(
        self,
    ) -> tuple[Outcome, ...]:
        """Return independently rejected outcomes."""

        return tuple(
            evaluation.outcome
            for evaluation in self.condition_evaluations
            if not evaluation.is_approved
        )

    def evaluation_for_outcome(
        self,
        outcome: Outcome,
    ) -> OutcomeCountRowEvaluation:
        """Return one active outcome evaluation."""

        if not isinstance(
            outcome,
            Outcome,
        ):
            raise TypeError(
                "outcome must be an Outcome."
            )

        for evaluation in self.condition_evaluations:
            if evaluation.outcome is outcome:
                return evaluation

        raise KeyError(
            f"No evaluation exists for outcome "
            f"{outcome.value}."
        )

    def count_for(
        self,
        outcome: Outcome,
    ) -> int:
        """Return the total count for one active outcome."""

        return self.evaluation_for_outcome(
            outcome
        ).count

    def is_outcome_approved(
        self,
        outcome: Outcome,
    ) -> bool:
        """Return one outcome condition's approval state."""

        return self.evaluation_for_outcome(
            outcome
        ).is_approved


@dataclass(frozen=True, slots=True)
class OneXTwoReductionResult:
    """Contains the complete 1X2 reduction result."""

    base_system: BaseReductionSystem
    rule: OneXTwoReductionRule
    evaluations: tuple[
        OneXTwoReductionRowEvaluation,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete reduction result."""

        if not isinstance(
            self.base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "base_system must be a "
                "BaseReductionSystem."
            )

        if not isinstance(
            self.rule,
            OneXTwoReductionRule,
        ):
            raise TypeError(
                "rule must be a OneXTwoReductionRule."
            )

        if not isinstance(
            self.evaluations,
            tuple,
        ):
            raise TypeError(
                "evaluations must be a tuple."
            )

        if (
            len(
                self.evaluations
            )
            != self.base_system.row_count
        ):
            raise ValueError(
                "evaluations must contain one entry "
                "for every base-system row."
            )

        for base_row, evaluation in zip(
            self.base_system.rows,
            self.evaluations,
            strict=True,
        ):
            if not isinstance(
                evaluation,
                OneXTwoReductionRowEvaluation,
            ):
                raise TypeError(
                    "evaluations may only contain "
                    "OneXTwoReductionRowEvaluation objects."
                )

            if evaluation.row != base_row:
                raise ValueError(
                    "evaluations must preserve the "
                    "base-system row order."
                )

            if evaluation.conditions != self.rule.conditions:
                raise ValueError(
                    "Every row evaluation must use the "
                    "rule's condition order."
                )

    @property
    def approved_evaluations(
        self,
    ) -> tuple[
        OneXTwoReductionRowEvaluation,
        ...,
    ]:
        """Return rows approved by every active condition."""

        return tuple(
            evaluation
            for evaluation in self.evaluations
            if evaluation.is_approved
        )

    @property
    def rejected_evaluations(
        self,
    ) -> tuple[
        OneXTwoReductionRowEvaluation,
        ...,
    ]:
        """Return rows rejected by at least one condition."""

        return tuple(
            evaluation
            for evaluation in self.evaluations
            if not evaluation.is_approved
        )

    @property
    def approved_rows(
        self,
    ) -> tuple[ReductionRow, ...]:
        """Return all surviving rows."""

        return tuple(
            evaluation.row
            for evaluation in self.approved_evaluations
        )

    @property
    def rejected_rows(
        self,
    ) -> tuple[ReductionRow, ...]:
        """Return all removed rows."""

        return tuple(
            evaluation.row
            for evaluation in self.rejected_evaluations
        )

    @property
    def original_row_count(self) -> int:
        """Return the row count before reduction."""

        return self.base_system.row_count

    @property
    def approved_count(self) -> int:
        """Return the number of surviving rows."""

        return len(
            self.approved_rows
        )

    @property
    def rejected_count(self) -> int:
        """Return the number of removed rows."""

        return len(
            self.rejected_rows
        )

    @property
    def retained_percentage(self) -> Decimal:
        """Return the percentage of rows that survive."""

        return (
            Decimal(
                self.approved_count
            )
            * Decimal("100")
            / Decimal(
                self.original_row_count
            )
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def reduction_percentage(self) -> Decimal:
        """Return the percentage of removed rows."""

        return (
            Decimal(
                self.rejected_count
            )
            * Decimal("100")
            / Decimal(
                self.original_row_count
            )
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def is_empty(self) -> bool:
        """Return whether no row survives."""

        return self.approved_count == 0

    def evaluation_at(
        self,
        row_number: int,
    ) -> OneXTwoReductionRowEvaluation:
        """Return one evaluation by one-based row number."""

        if isinstance(
            row_number,
            bool,
        ) or not isinstance(
            row_number,
            int,
        ):
            raise TypeError(
                "row_number must be an integer."
            )

        if not (
            1
            <= row_number
            <= self.original_row_count
        ):
            raise IndexError(
                "row_number is outside the result."
            )

        return self.evaluations[
            row_number - 1
        ]

    def approved_count_for_outcome(
        self,
        outcome: Outcome,
    ) -> int:
        """Return rows approved by one condition alone."""

        self.rule.condition_for(
            outcome
        )

        return sum(
            evaluation.is_outcome_approved(
                outcome
            )
            for evaluation in self.evaluations
        )

    def rejected_count_for_outcome(
        self,
        outcome: Outcome,
    ) -> int:
        """Return rows rejected by one condition alone."""

        return (
            self.original_row_count
            - self.approved_count_for_outcome(
                outcome
            )
        )

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable result."""

        return (
            f"1X2 {self.rule.condition_pattern} | "
            f"Ursprung {self.original_row_count} | "
            f"Kvar {self.approved_count} | "
            f"Bort {self.rejected_count} | "
            f"Reducering "
            f"{self.reduction_percentage}%"
        )