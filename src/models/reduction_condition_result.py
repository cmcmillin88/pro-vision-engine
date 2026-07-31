"""Result models for the common reduction-condition engine."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class ReductionMetricEvaluation:
    """Contains one independently evaluated MIN/MAX metric."""

    label: str
    observed_value: int
    minimum_value: int
    maximum_value: int

    def __post_init__(self) -> None:
        """Normalize and validate one metric evaluation."""

        if not isinstance(
            self.label,
            str,
        ):
            raise TypeError(
                "label must be a string."
            )

        normalized_label = self.label.strip()

        if not normalized_label:
            raise ValueError(
                "label must not be empty."
            )

        object.__setattr__(
            self,
            "label",
            normalized_label,
        )

        for field_name in (
            "observed_value",
            "minimum_value",
            "maximum_value",
        ):
            value = getattr(
                self,
                field_name,
            )

            if isinstance(value, bool) or not isinstance(
                value,
                int,
            ):
                raise TypeError(
                    f"{field_name} must be an integer."
                )

            if value < 0:
                raise ValueError(
                    f"{field_name} must not be negative."
                )

        if self.minimum_value > self.maximum_value:
            raise ValueError(
                "minimum_value must not exceed "
                "maximum_value."
            )

    @property
    def is_approved(self) -> bool:
        """Return whether the value satisfies MIN/MAX."""

        return (
            self.minimum_value
            <= self.observed_value
            <= self.maximum_value
        )

    @property
    def summary_text(self) -> str:
        """Return a compact metric description."""

        return (
            f"{self.label} {self.observed_value} "
            f"[{self.minimum_value}/"
            f"{self.maximum_value}]"
        )


@dataclass(frozen=True, slots=True)
class ReductionConditionEvaluation:
    """Contains all metrics for one condition group."""

    condition_type: ReductionConditionType
    metrics: tuple[
        ReductionMetricEvaluation,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate one condition-group evaluation."""

        if not isinstance(
            self.condition_type,
            ReductionConditionType,
        ):
            raise TypeError(
                "condition_type must be a "
                "ReductionConditionType."
            )

        if not isinstance(
            self.metrics,
            tuple,
        ):
            raise TypeError(
                "metrics must be a tuple."
            )

        if not self.metrics:
            raise ValueError(
                "A condition evaluation requires at "
                "least one metric."
            )

        for metric in self.metrics:
            if not isinstance(
                metric,
                ReductionMetricEvaluation,
            ):
                raise TypeError(
                    "metrics may only contain "
                    "ReductionMetricEvaluation objects."
                )

        labels = tuple(
            metric.label.casefold()
            for metric in self.metrics
        )

        if len(
            set(
                labels
            )
        ) != len(
            labels
        ):
            raise ValueError(
                "Metric labels must be unique inside "
                "one condition evaluation."
            )

    @property
    def is_approved(self) -> bool:
        """Return whether every metric approves."""

        return all(
            metric.is_approved
            for metric in self.metrics
        )

    @property
    def summary_text(self) -> str:
        """Return a compact group description."""

        metric_text = ", ".join(
            metric.summary_text
            for metric in self.metrics
        )

        return (
            f"{self.condition_type.display_name}: "
            f"{metric_text}"
        )


@dataclass(frozen=True, slots=True)
class ReductionConditionRowEvaluation:
    """Contains every active condition result for one row."""

    row: ReductionRow
    condition_evaluations: tuple[
        ReductionConditionEvaluation,
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
                "A row evaluation requires at least "
                "one condition evaluation."
            )

        for evaluation in self.condition_evaluations:
            if not isinstance(
                evaluation,
                ReductionConditionEvaluation,
            ):
                raise TypeError(
                    "condition_evaluations may only contain "
                    "ReductionConditionEvaluation objects."
                )

        condition_types = self.condition_types

        if len(
            set(
                condition_types
            )
        ) != len(
            condition_types
        ):
            raise ValueError(
                "A row evaluation may only contain one "
                "evaluation per condition type."
            )

        expected_order = tuple(
            condition_type
            for condition_type
            in ReductionConditionType.ordered()
            if condition_type in condition_types
        )

        if condition_types != expected_order:
            raise ValueError(
                "Condition evaluations must follow the "
                "official condition order."
            )

    @property
    def condition_types(
        self,
    ) -> tuple[ReductionConditionType, ...]:
        """Return condition types in stored order."""

        return tuple(
            evaluation.condition_type
            for evaluation
            in self.condition_evaluations
        )

    @property
    def is_approved(self) -> bool:
        """Return whether every condition approves."""

        return all(
            evaluation.is_approved
            for evaluation
            in self.condition_evaluations
        )

    @property
    def approved_condition_types(
        self,
    ) -> tuple[ReductionConditionType, ...]:
        """Return independently approved groups."""

        return tuple(
            evaluation.condition_type
            for evaluation
            in self.condition_evaluations
            if evaluation.is_approved
        )

    @property
    def rejected_condition_types(
        self,
    ) -> tuple[ReductionConditionType, ...]:
        """Return independently rejected groups."""

        return tuple(
            evaluation.condition_type
            for evaluation
            in self.condition_evaluations
            if not evaluation.is_approved
        )

    def evaluation_for(
        self,
        condition_type: ReductionConditionType,
    ) -> ReductionConditionEvaluation:
        """Return one active condition evaluation."""

        if not isinstance(
            condition_type,
            ReductionConditionType,
        ):
            raise TypeError(
                "condition_type must be a "
                "ReductionConditionType."
            )

        for evaluation in self.condition_evaluations:
            if (
                evaluation.condition_type
                is condition_type
            ):
                return evaluation

        raise KeyError(
            f"No evaluation exists for condition type "
            f"{condition_type.value}."
        )


@dataclass(frozen=True, slots=True)
class ReductionConditionResult:
    """Contains the complete common-condition result."""

    base_system: BaseReductionSystem
    condition_set: ReductionConditionSet
    evaluations: tuple[
        ReductionConditionRowEvaluation,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete combined result."""

        if not isinstance(
            self.base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "base_system must be a "
                "BaseReductionSystem."
            )

        if not isinstance(
            self.condition_set,
            ReductionConditionSet,
        ):
            raise TypeError(
                "condition_set must be a "
                "ReductionConditionSet."
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
                ReductionConditionRowEvaluation,
            ):
                raise TypeError(
                    "evaluations may only contain "
                    "ReductionConditionRowEvaluation "
                    "objects."
                )

            if evaluation.row != base_row:
                raise ValueError(
                    "evaluations must preserve the "
                    "base-system row order."
                )

            if (
                evaluation.condition_types
                != self.condition_set.condition_types
            ):
                raise ValueError(
                    "Every row evaluation must follow the "
                    "condition set's active condition types."
                )

            if (
                evaluation.is_approved
                is not self.condition_set.is_approved(
                    base_row
                )
            ):
                raise ValueError(
                    "Row approval does not match the "
                    "complete condition set."
                )

    @property
    def approved_evaluations(
        self,
    ) -> tuple[
        ReductionConditionRowEvaluation,
        ...,
    ]:
        """Return all surviving evaluations."""

        return tuple(
            evaluation
            for evaluation in self.evaluations
            if evaluation.is_approved
        )

    @property
    def rejected_evaluations(
        self,
    ) -> tuple[
        ReductionConditionRowEvaluation,
        ...,
    ]:
        """Return all removed evaluations."""

        return tuple(
            evaluation
            for evaluation in self.evaluations
            if not evaluation.is_approved
        )

    @property
    def approved_rows(
        self,
    ) -> tuple[ReductionRow, ...]:
        """Return surviving rows in original order."""

        return tuple(
            evaluation.row
            for evaluation
            in self.approved_evaluations
        )

    @property
    def rejected_rows(
        self,
    ) -> tuple[ReductionRow, ...]:
        """Return removed rows in original order."""

        return tuple(
            evaluation.row
            for evaluation
            in self.rejected_evaluations
        )

    @property
    def original_row_count(self) -> int:
        """Return the original number of rows."""

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
        """Return the percentage of surviving rows."""

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
    ) -> ReductionConditionRowEvaluation:
        """Return an evaluation by one-based row number."""

        if isinstance(row_number, bool) or not isinstance(
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

    def approved_count_for_condition(
        self,
        condition_type: ReductionConditionType,
    ) -> int:
        """Return rows approved by one group alone."""

        if not isinstance(
            condition_type,
            ReductionConditionType,
        ):
            raise TypeError(
                "condition_type must be a "
                "ReductionConditionType."
            )

        if (
            condition_type
            not in self.condition_set.condition_types
        ):
            raise KeyError(
                f"Condition type {condition_type.value} "
                "is not active."
            )

        return sum(
            evaluation.evaluation_for(
                condition_type
            ).is_approved
            for evaluation in self.evaluations
        )

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable result."""

        return (
            f"Villkor "
            f"{self.condition_set.condition_count} | "
            f"Ursprung {self.original_row_count} | "
            f"Kvar {self.approved_count} | "
            f"Bort {self.rejected_count} | "
            f"Reducering {self.reduction_percentage}%"
        )