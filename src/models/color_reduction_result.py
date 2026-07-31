"""Result models for one applied color reduction rule."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from src.models.color_reduction_rule import (
    ColorReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class ColorReductionRowEvaluation:
    """Contains one row's color-hit evaluation."""

    row: ReductionRow
    hit_count: int
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
            self.hit_count,
            bool,
        ) or not isinstance(
            self.hit_count,
            int,
        ):
            raise TypeError(
                "hit_count must be an integer."
            )

        if self.hit_count < 0:
            raise ValueError(
                "hit_count must not be negative."
            )

        if not isinstance(
            self.is_approved,
            bool,
        ):
            raise TypeError(
                "is_approved must be a boolean."
            )


@dataclass(frozen=True, slots=True)
class ColorReductionResult:
    """Contains the complete result of one color filter."""

    base_system: BaseReductionSystem
    rule: ColorReductionRule
    evaluations: tuple[
        ColorReductionRowEvaluation,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete color-reduction result."""

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
            ColorReductionRule,
        ):
            raise TypeError(
                "rule must be a ColorReductionRule."
            )

        if not isinstance(
            self.evaluations,
            tuple,
        ):
            raise TypeError(
                "evaluations must be a tuple."
            )

        if (
            len(self.evaluations)
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
                ColorReductionRowEvaluation,
            ):
                raise TypeError(
                    "evaluations may only contain "
                    "ColorReductionRowEvaluation objects."
                )

            if evaluation.row != base_row:
                raise ValueError(
                    "evaluations must preserve the "
                    "base-system row order."
                )

            expected_hit_count = self.rule.hit_count(
                base_row
            )

            if evaluation.hit_count != expected_hit_count:
                raise ValueError(
                    "Evaluation hit_count does not match "
                    "the color rule."
                )

            expected_approval = (
                self.rule.min_hits
                <= expected_hit_count
                <= self.rule.max_hits
            )

            if evaluation.is_approved is not expected_approval:
                raise ValueError(
                    "Evaluation approval does not match "
                    "the inclusive MIN/MAX condition."
                )

    @property
    def approved_evaluations(
        self,
    ) -> tuple[
        ColorReductionRowEvaluation,
        ...,
    ]:
        """Return all approved row evaluations."""

        return tuple(
            evaluation
            for evaluation in self.evaluations
            if evaluation.is_approved
        )

    @property
    def rejected_evaluations(
        self,
    ) -> tuple[
        ColorReductionRowEvaluation,
        ...,
    ]:
        """Return all rejected row evaluations."""

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
        """Return the row count before color reduction."""

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
            Decimal(self.approved_count)
            * Decimal("100")
            / Decimal(self.original_row_count)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def reduction_percentage(self) -> Decimal:
        """Return the percentage of rows removed."""

        return (
            Decimal(self.rejected_count)
            * Decimal("100")
            / Decimal(self.original_row_count)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def is_empty(self) -> bool:
        """Return whether every row was removed."""

        return self.approved_count == 0

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable result."""

        return (
            f"Färg {self.rule.color.display_name} | "
            f"MIN {self.rule.min_hits} | "
            f"MAX {self.rule.max_hits} | "
            f"Ursprung {self.original_row_count} | "
            f"Kvar {self.approved_count} | "
            f"Bort {self.rejected_count} | "
            f"Reducering "
            f"{self.reduction_percentage}%"
        )