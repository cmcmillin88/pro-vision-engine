"""Result models for deterministic total-odds reduction."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from src.models.odds_reduction_rule import (
    OddsReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


_DISPLAY_QUANTUM = Decimal("0.01")


def _display_odds(
    value: Decimal,
) -> str:
    """Format odds for result summaries only."""

    return str(
        value.quantize(
            _DISPLAY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
    )


@dataclass(frozen=True, slots=True)
class OddsReductionRowEvaluation:
    """Contains one row's frozen total-odds evaluation."""

    row: ReductionRow
    total_odds: Decimal
    is_approved: bool

    def __post_init__(self) -> None:
        """Validate one odds-reduction row evaluation."""

        if not isinstance(
            self.row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        if not isinstance(
            self.total_odds,
            Decimal,
        ):
            raise TypeError(
                "total_odds must be a Decimal."
            )

        if not self.total_odds.is_finite():
            raise ValueError(
                "total_odds must be finite."
            )

        if self.total_odds <= Decimal("0"):
            raise ValueError(
                "total_odds must be greater than zero."
            )

        if not isinstance(
            self.is_approved,
            bool,
        ):
            raise TypeError(
                "is_approved must be a boolean."
            )


@dataclass(frozen=True, slots=True)
class OddsReductionResult:
    """Contains the complete result of one odds filter."""

    base_system: BaseReductionSystem
    rule: OddsReductionRule
    evaluations: tuple[
        OddsReductionRowEvaluation,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete odds-reduction result."""

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
            OddsReductionRule,
        ):
            raise TypeError(
                "rule must be an OddsReductionRule."
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
                OddsReductionRowEvaluation,
            ):
                raise TypeError(
                    "evaluations may only contain "
                    "OddsReductionRowEvaluation objects."
                )

            if evaluation.row != base_row:
                raise ValueError(
                    "evaluations must preserve the "
                    "base-system row order."
                )

            expected_total = self.rule.total_odds(
                base_row
            )

            if evaluation.total_odds != expected_total:
                raise ValueError(
                    "Evaluation total_odds does not match "
                    "the row and frozen odds snapshot."
                )

            expected_approval = self.rule.contains(
                expected_total
            )

            if (
                evaluation.is_approved
                is not expected_approval
            ):
                raise ValueError(
                    "Evaluation approval does not match "
                    "the total-odds interval."
                )

    @property
    def approved_evaluations(
        self,
    ) -> tuple[
        OddsReductionRowEvaluation,
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
        OddsReductionRowEvaluation,
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
        """Return the number of rows before odds reduction."""

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

    @property
    def total_odds_distribution(
        self,
    ) -> tuple[tuple[Decimal, int], ...]:
        """Return exact total odds and their row counts."""

        counts: dict[Decimal, int] = {}

        for evaluation in self.evaluations:
            counts[
                evaluation.total_odds
            ] = (
                counts.get(
                    evaluation.total_odds,
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
    def minimum_observed_odds(self) -> Decimal:
        """Return the base system's lowest total odds."""

        return self.total_odds_distribution[0][0]

    @property
    def maximum_observed_odds(self) -> Decimal:
        """Return the base system's highest total odds."""

        return self.total_odds_distribution[-1][0]

    def row_count_for_total_odds(
        self,
        total_odds: Decimal,
    ) -> int:
        """Return rows with one exact total-odds value."""

        if not isinstance(
            total_odds,
            Decimal,
        ):
            raise TypeError(
                "total_odds must be a Decimal."
            )

        if not total_odds.is_finite():
            raise ValueError(
                "total_odds must be finite."
            )

        if total_odds <= Decimal("0"):
            raise ValueError(
                "total_odds must be greater than zero."
            )

        return sum(
            evaluation.total_odds == total_odds
            for evaluation in self.evaluations
        )

    def evaluation_at(
        self,
        row_number: int,
    ) -> OddsReductionRowEvaluation:
        """Return one evaluation by one-based row number."""

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

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable result."""

        return (
            f"Odds MIN "
            f"{_display_odds(self.rule.min_total_odds)} | "
            f"MAX < "
            f"{_display_odds(self.rule.max_total_odds)} | "
            f"Ursprung {self.original_row_count} | "
            f"Kvar {self.approved_count} | "
            f"Bort {self.rejected_count} | "
            f"Reducering {self.reduction_percentage}%"
        )