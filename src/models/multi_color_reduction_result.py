"""Result models for multiple simultaneous color rules."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from src.models.color_reduction_rule import (
    ColorReductionRule,
    ReductionColor,
)
from src.models.color_reduction_rule_set import (
    ColorReductionRuleSet,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class ColorRuleRowEvaluation:
    """Contains one color rule's result for one row."""

    rule: ColorReductionRule
    hit_count: int

    def __post_init__(self) -> None:
        """Validate one independent color evaluation."""

        if not isinstance(
            self.rule,
            ColorReductionRule,
        ):
            raise TypeError(
                "rule must be a ColorReductionRule."
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

        if (
            self.hit_count
            > self.rule.maximum_possible_hits
        ):
            raise ValueError(
                "hit_count must not exceed the rule's "
                "maximum possible hits."
            )

    @property
    def color(self) -> ReductionColor:
        """Return the evaluated color."""

        return self.rule.color

    @property
    def is_approved(self) -> bool:
        """Return whether this color satisfies MIN/MAX."""

        return (
            self.rule.min_hits
            <= self.hit_count
            <= self.rule.max_hits
        )


@dataclass(frozen=True, slots=True)
class MultiColorReductionRowEvaluation:
    """Contains every color's independent result for one row."""

    row: ReductionRow
    rule_evaluations: tuple[
        ColorRuleRowEvaluation,
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
            self.rule_evaluations,
            tuple,
        ):
            raise TypeError(
                "rule_evaluations must be a tuple."
            )

        if len(self.rule_evaluations) < 2:
            raise ValueError(
                "A multi-color row evaluation requires "
                "at least two color evaluations."
            )

        for evaluation in self.rule_evaluations:
            if not isinstance(
                evaluation,
                ColorRuleRowEvaluation,
            ):
                raise TypeError(
                    "rule_evaluations may only contain "
                    "ColorRuleRowEvaluation objects."
                )

        colors = tuple(
            evaluation.color
            for evaluation in self.rule_evaluations
        )

        if len(
            set(
                colors
            )
        ) != len(
            colors
        ):
            raise ValueError(
                "A row evaluation may only contain "
                "one evaluation per color."
            )

        for evaluation in self.rule_evaluations:
            expected_hit_count = (
                evaluation.rule.hit_count(
                    self.row
                )
            )

            if (
                evaluation.hit_count
                != expected_hit_count
            ):
                raise ValueError(
                    "Evaluation hit_count does not match "
                    "the row and color rule."
                )

    @property
    def colors(self) -> tuple[ReductionColor, ...]:
        """Return evaluated colors in stored order."""

        return tuple(
            evaluation.color
            for evaluation in self.rule_evaluations
        )

    @property
    def is_approved(self) -> bool:
        """Return whether every color approves the row."""

        return all(
            evaluation.is_approved
            for evaluation in self.rule_evaluations
        )

    @property
    def approved_colors(
        self,
    ) -> tuple[ReductionColor, ...]:
        """Return colors whose own MIN/MAX is satisfied."""

        return tuple(
            evaluation.color
            for evaluation in self.rule_evaluations
            if evaluation.is_approved
        )

    @property
    def rejected_colors(
        self,
    ) -> tuple[ReductionColor, ...]:
        """Return colors whose own MIN/MAX is not satisfied."""

        return tuple(
            evaluation.color
            for evaluation in self.rule_evaluations
            if not evaluation.is_approved
        )

    def evaluation_for_color(
        self,
        color: ReductionColor,
    ) -> ColorRuleRowEvaluation:
        """Return one color's evaluation."""

        if not isinstance(
            color,
            ReductionColor,
        ):
            raise TypeError(
                "color must be a ReductionColor."
            )

        for evaluation in self.rule_evaluations:
            if evaluation.color is color:
                return evaluation

        raise KeyError(
            f"No evaluation exists for color {color.value}."
        )

    def hit_count_for(
        self,
        color: ReductionColor,
    ) -> int:
        """Return one color's hit count."""

        return self.evaluation_for_color(
            color
        ).hit_count

    def is_color_approved(
        self,
        color: ReductionColor,
    ) -> bool:
        """Return one color's independent approval state."""

        return self.evaluation_for_color(
            color
        ).is_approved


@dataclass(frozen=True, slots=True)
class MultiColorReductionResult:
    """Contains the complete result of all color filters."""

    base_system: BaseReductionSystem
    rule_set: ColorReductionRuleSet
    evaluations: tuple[
        MultiColorReductionRowEvaluation,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete multi-color result."""

        if not isinstance(
            self.base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "base_system must be a "
                "BaseReductionSystem."
            )

        if not isinstance(
            self.rule_set,
            ColorReductionRuleSet,
        ):
            raise TypeError(
                "rule_set must be a "
                "ColorReductionRuleSet."
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
                MultiColorReductionRowEvaluation,
            ):
                raise TypeError(
                    "evaluations may only contain "
                    "MultiColorReductionRowEvaluation "
                    "objects."
                )

            if evaluation.row != base_row:
                raise ValueError(
                    "evaluations must preserve the "
                    "base-system row order."
                )

            if (
                evaluation.colors
                != self.rule_set.colors
            ):
                raise ValueError(
                    "Every row evaluation must follow "
                    "the rule set's color order."
                )

    @property
    def approved_evaluations(
        self,
    ) -> tuple[
        MultiColorReductionRowEvaluation,
        ...,
    ]:
        """Return rows approved by every color."""

        return tuple(
            evaluation
            for evaluation in self.evaluations
            if evaluation.is_approved
        )

    @property
    def rejected_evaluations(
        self,
    ) -> tuple[
        MultiColorReductionRowEvaluation,
        ...,
    ]:
        """Return rows rejected by at least one color."""

        return tuple(
            evaluation
            for evaluation in self.evaluations
            if not evaluation.is_approved
        )

    @property
    def approved_rows(
        self,
    ) -> tuple[ReductionRow, ...]:
        """Return all jointly surviving rows."""

        return tuple(
            evaluation.row
            for evaluation in self.approved_evaluations
        )

    @property
    def rejected_rows(
        self,
    ) -> tuple[ReductionRow, ...]:
        """Return rows rejected by the combined rules."""

        return tuple(
            evaluation.row
            for evaluation in self.rejected_evaluations
        )

    @property
    def original_row_count(self) -> int:
        """Return the original mathematical row count."""

        return self.base_system.row_count

    @property
    def approved_count(self) -> int:
        """Return the jointly surviving row count."""

        return len(
            self.approved_rows
        )

    @property
    def rejected_count(self) -> int:
        """Return the jointly removed row count."""

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
        """Return whether no row survives all colors."""

        return self.approved_count == 0

    def evaluation_at(
        self,
        row_number: int,
    ) -> MultiColorReductionRowEvaluation:
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

    def approved_count_for_color(
        self,
        color: ReductionColor,
    ) -> int:
        """Return rows approved by one color independently."""

        return sum(
            evaluation.is_color_approved(
                color
            )
            for evaluation in self.evaluations
        )

    def rejected_count_for_color(
        self,
        color: ReductionColor,
    ) -> int:
        """Return rows rejected by one color independently."""

        return (
            self.original_row_count
            - self.approved_count_for_color(
                color
            )
        )

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable result."""

        return (
            f"Färger {self.rule_set.condition_pattern} | "
            f"Ursprung {self.original_row_count} | "
            f"Kvar {self.approved_count} | "
            f"Bort {self.rejected_count} | "
            f"Reducering "
            f"{self.reduction_percentage}%"
        )