"""Models for total 1-X-2 outcome-count reduction rules."""

from dataclasses import dataclass

from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class OutcomeCountCondition:
    """Defines inclusive MIN/MAX for one outcome."""

    outcome: Outcome
    min_count: int
    max_count: int

    def __post_init__(self) -> None:
        """Validate one outcome-count condition."""

        if not isinstance(
            self.outcome,
            Outcome,
        ):
            raise TypeError(
                "outcome must be an Outcome."
            )

        for field_name in (
            "min_count",
            "max_count",
        ):
            value = getattr(
                self,
                field_name,
            )

            if isinstance(
                value,
                bool,
            ) or not isinstance(
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

        if self.min_count > self.max_count:
            raise ValueError(
                "min_count must not exceed max_count."
            )

    @property
    def condition_text(self) -> str:
        """Return compact outcome and interval text."""

        return (
            f"{self.outcome.value} "
            f"{self.min_count}/{self.max_count}"
        )

    def count_in(
        self,
        row: ReductionRow,
    ) -> int:
        """Count this outcome across one complete row."""

        if not isinstance(
            row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        return row.count(
            self.outcome
        )

    def is_approved(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether the row satisfies this interval."""

        count = self.count_in(
            row
        )

        return (
            self.min_count
            <= count
            <= self.max_count
        )


@dataclass(frozen=True, slots=True)
class OneXTwoReductionRule:
    """Contains active total-count conditions for 1, X and 2."""

    conditions: tuple[
        OutcomeCountCondition,
        ...,
    ]

    def __post_init__(self) -> None:
        """Normalize and validate all active conditions."""

        if not isinstance(
            self.conditions,
            tuple,
        ):
            raise TypeError(
                "conditions must be a tuple."
            )

        if not self.conditions:
            raise ValueError(
                "A 1X2 reduction rule requires at "
                "least one active condition."
            )

        if len(
            self.conditions
        ) > len(
            Outcome.ordered()
        ):
            raise ValueError(
                "A 1X2 reduction rule may contain "
                "at most three conditions."
            )

        for condition in self.conditions:
            if not isinstance(
                condition,
                OutcomeCountCondition,
            ):
                raise TypeError(
                    "conditions may only contain "
                    "OutcomeCountCondition objects."
                )

        outcomes = tuple(
            condition.outcome
            for condition in self.conditions
        )

        if len(
            set(
                outcomes
            )
        ) != len(
            outcomes
        ):
            raise ValueError(
                "Each outcome may only appear once "
                "in a 1X2 reduction rule."
            )

        official_index = {
            outcome: index
            for index, outcome in enumerate(
                Outcome.ordered()
            )
        }

        ordered_conditions = tuple(
            sorted(
                self.conditions,
                key=lambda condition: official_index[
                    condition.outcome
                ],
            )
        )

        object.__setattr__(
            self,
            "conditions",
            ordered_conditions,
        )

    @property
    def condition_count(self) -> int:
        """Return the number of active conditions."""

        return len(
            self.conditions
        )

    @property
    def outcomes(self) -> tuple[Outcome, ...]:
        """Return constrained outcomes in official order."""

        return tuple(
            condition.outcome
            for condition in self.conditions
        )

    @property
    def condition_pattern(self) -> str:
        """Return all active intervals as compact text."""

        return " | ".join(
            condition.condition_text
            for condition in self.conditions
        )

    def condition_for(
        self,
        outcome: Outcome,
    ) -> OutcomeCountCondition:
        """Return the active condition for one outcome."""

        if not isinstance(
            outcome,
            Outcome,
        ):
            raise TypeError(
                "outcome must be an Outcome."
            )

        for condition in self.conditions:
            if condition.outcome is outcome:
                return condition

        raise KeyError(
            f"No active condition exists for "
            f"outcome {outcome.value}."
        )

    def count_values(
        self,
        row: ReductionRow,
    ) -> tuple[int, ...]:
        """Return counts for every active outcome."""

        self._validate_row(
            row
        )

        return tuple(
            condition.count_in(
                row
            )
            for condition in self.conditions
        )

    def approval_states(
        self,
        row: ReductionRow,
    ) -> tuple[bool, ...]:
        """Return each active condition's approval state."""

        self._validate_row(
            row
        )

        return tuple(
            condition.is_approved(
                row
            )
            for condition in self.conditions
        )

    def is_approved(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether every active condition approves."""

        return all(
            self.approval_states(
                row
            )
        )

    @staticmethod
    def _validate_row(
        row: object,
    ) -> None:
        """Validate one reduction row."""

        if not isinstance(
            row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )