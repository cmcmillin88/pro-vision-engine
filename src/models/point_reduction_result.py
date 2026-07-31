"""Result models for deterministic point reduction."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from src.models.point_reduction_rule import (
    PointReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class PointReductionRowEvaluation:
    """Contains one row's total point evaluation."""

    row: ReductionRow
    total_points: int
    is_approved: bool

    def __post_init__(self) -> None:
        """Validate one row evaluation."""

        if not isinstance(
            self.row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        if isinstance(
            self.total_points,
            bool,
        ) or not isinstance(
            self.total_points,
            int,
        ):
            raise TypeError(
                "total_points must be an integer."
            )

        if self.total_points < 0:
            raise ValueError(
                "total_points must not be negative."
            )

        if not isinstance(
            self.is_approved,
            bool,
        ):
            raise TypeError(
                "is_approved must be a boolean."
            )


@dataclass(frozen=True, slots=True)
class PointReductionResult:
    """Contains the complete result of one point filter."""

    base_system: BaseReductionSystem
    rule: PointReductionRule
    evaluations: tuple[
        PointReductionRowEvaluation,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete point-reduction result."""

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
            PointReductionRule,
        ):
            raise TypeError(
                "rule must be a PointReductionRule."
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
                PointReductionRowEvaluation,
            ):
                raise TypeError(
                    "evaluations may only contain "
                    "PointReductionRowEvaluation objects."
                )

            if evaluation.row != base_row:
                raise ValueError(
                    "evaluations must preserve the "
                    "base-system row order."
                )

            expected_points = self.rule.row_points(
                base_row
            )

            if (
                evaluation.total_points
                != expected_points
            ):
                raise ValueError(
                    "Evaluation total_points does not "
                    "match the row and point rule."
                )

            expected_approval = (
                self.rule.min_points
                <= expected_points
                <= self.rule.max_points
            )

            if (
                evaluation.is_approved
                is not expected_approval
            ):
                raise ValueError(
                    "Evaluation approval does not match "
                    "the inclusive point interval."
                )

    @property
    def approved_evaluations(
        self,
    ) -> tuple[
        PointReductionRowEvaluation,
        ...,
    ]:
        """Return all surviving row evaluations."""

        return tuple(
            evaluation
            for evaluation in self.evaluations
            if evaluation.is_approved
        )

    @property
    def rejected_evaluations(
        self,
    ) -> tuple[
        PointReductionRowEvaluation,
        ...,
    ]:
        """Return all removed row evaluations."""

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
            for evaluation in self.approved_evaluations
        )

    @property
    def rejected_rows(
        self,
    ) -> tuple[ReductionRow, ...]:
        """Return removed rows in original order."""

        return tuple(
            evaluation.row
            for evaluation in self.rejected_evaluations
        )

    @property
    def original_row_count(self) -> int:
        """Return the row count before point reduction."""

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
        """Return the percentage of rows removed."""

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

    @property
    def point_distribution(
        self,
    ) -> tuple[tuple[int, int], ...]:
        """Return sorted point totals and their row counts."""

        counts: dict[int, int] = {}

        for evaluation in self.evaluations:
            counts[
                evaluation.total_points
            ] = (
                counts.get(
                    evaluation.total_points,
                    0,
                )
                + 1
            )

        return tuple(
            sorted(
                counts.items()
            )
        )

    @property
    def minimum_observed_points(self) -> int:
        """Return the lowest total in the base system."""

        return self.point_distribution[0][0]

    @property
    def maximum_observed_points(self) -> int:
        """Return the highest total in the base system."""

        return self.point_distribution[-1][0]

    def row_count_for_points(
        self,
        total_points: int,
    ) -> int:
        """Return the number of rows with one exact total."""

        if isinstance(
            total_points,
            bool,
        ) or not isinstance(
            total_points,
            int,
        ):
            raise TypeError(
                "total_points must be an integer."
            )

        if total_points < 0:
            raise ValueError(
                "total_points must not be negative."
            )

        return sum(
            evaluation.total_points
            == total_points
            for evaluation in self.evaluations
        )

    def evaluation_at(
        self,
        row_number: int,
    ) -> PointReductionRowEvaluation:
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

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable result."""

        return (
            f"Poäng MIN {self.rule.min_points} | "
            f"MAX {self.rule.max_points} | "
            f"Ursprung {self.original_row_count} | "
            f"Kvar {self.approved_count} | "
            f"Bort {self.rejected_count} | "
            f"Reducering "
            f"{self.reduction_percentage}%"
        )