"""Result models for transparent estimated-payout reduction."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from src.models.payout_reduction_rule import (
    PayoutReductionRule,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
)
from src.models.reduction_row import ReductionRow


_MONEY_QUANTUM = Decimal("0.01")


def _display_money(
    value: Decimal,
) -> str:
    """Format a monetary value for result summaries."""

    return str(
        value.quantize(
            _MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
    )


@dataclass(frozen=True, slots=True)
class PayoutReductionRowEvaluation:
    """Contains one row's payout-forecast evaluation."""

    row: ReductionRow
    row_share: Decimal
    expected_winning_units: Decimal
    estimated_payout: Decimal
    is_approved: bool

    def __post_init__(self) -> None:
        """Validate one payout-reduction row evaluation."""

        if not isinstance(
            self.row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        for field_name in (
            "row_share",
            "expected_winning_units",
            "estimated_payout",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                Decimal,
            ):
                raise TypeError(
                    f"{field_name} must be a Decimal."
                )

            if not value.is_finite():
                raise ValueError(
                    f"{field_name} must be finite."
                )

            if value < Decimal("0"):
                raise ValueError(
                    f"{field_name} must not be negative."
                )

        if self.row_share > Decimal("1"):
            raise ValueError(
                "row_share must not exceed 1."
            )

        if self.estimated_payout <= Decimal("0"):
            raise ValueError(
                "estimated_payout must be greater than zero."
            )

        if not isinstance(
            self.is_approved,
            bool,
        ):
            raise TypeError(
                "is_approved must be a boolean."
            )


@dataclass(frozen=True, slots=True)
class PayoutReductionResult:
    """Contains the complete result of one payout filter."""

    base_system: BaseReductionSystem
    rule: PayoutReductionRule
    evaluations: tuple[
        PayoutReductionRowEvaluation,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete payout-reduction result."""

        if not isinstance(
            self.base_system,
            BaseReductionSystem,
        ):
            raise TypeError(
                "base_system must be a BaseReductionSystem."
            )

        if not isinstance(
            self.rule,
            PayoutReductionRule,
        ):
            raise TypeError(
                "rule must be a PayoutReductionRule."
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

        snapshot = self.rule.snapshot

        for base_row, evaluation in zip(
            self.base_system.rows,
            self.evaluations,
            strict=True,
        ):
            if not isinstance(
                evaluation,
                PayoutReductionRowEvaluation,
            ):
                raise TypeError(
                    "evaluations may only contain "
                    "PayoutReductionRowEvaluation objects."
                )

            if evaluation.row != base_row:
                raise ValueError(
                    "evaluations must preserve the "
                    "base-system row order."
                )

            expected_share = snapshot.row_share(
                base_row
            )
            expected_units = snapshot.expected_winning_units(
                base_row
            )
            expected_payout = snapshot.estimated_payout(
                base_row
            )

            if evaluation.row_share != expected_share:
                raise ValueError(
                    "Evaluation row_share does not match "
                    "the frozen payout snapshot."
                )

            if (
                evaluation.expected_winning_units
                != expected_units
            ):
                raise ValueError(
                    "Evaluation expected_winning_units does "
                    "not match the frozen payout snapshot."
                )

            if evaluation.estimated_payout != expected_payout:
                raise ValueError(
                    "Evaluation estimated_payout does not "
                    "match the frozen payout snapshot."
                )

            expected_approval = self.rule.contains(
                expected_payout
            )

            if (
                evaluation.is_approved
                is not expected_approval
            ):
                raise ValueError(
                    "Evaluation approval does not match "
                    "the payout interval."
                )

    @property
    def approved_evaluations(
        self,
    ) -> tuple[PayoutReductionRowEvaluation, ...]:
        """Return all surviving evaluations."""

        return tuple(
            evaluation
            for evaluation in self.evaluations
            if evaluation.is_approved
        )

    @property
    def rejected_evaluations(
        self,
    ) -> tuple[PayoutReductionRowEvaluation, ...]:
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
        """Return the number of rows before reduction."""

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
    def estimated_payout_distribution(
        self,
    ) -> tuple[tuple[Decimal, int], ...]:
        """Return estimated payouts and their row counts."""

        counts: dict[Decimal, int] = {}

        for evaluation in self.evaluations:
            counts[
                evaluation.estimated_payout
            ] = (
                counts.get(
                    evaluation.estimated_payout,
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
    def minimum_observed_payout(self) -> Decimal:
        """Return the base system's lowest forecast payout."""

        return self.estimated_payout_distribution[0][0]

    @property
    def maximum_observed_payout(self) -> Decimal:
        """Return the base system's highest forecast payout."""

        return self.estimated_payout_distribution[-1][0]

    def row_count_for_estimated_payout(
        self,
        estimated_payout: Decimal,
    ) -> int:
        """Return rows with one exact forecast payout."""

        if not isinstance(
            estimated_payout,
            Decimal,
        ):
            raise TypeError(
                "estimated_payout must be a Decimal."
            )

        if not estimated_payout.is_finite():
            raise ValueError(
                "estimated_payout must be finite."
            )

        if estimated_payout < Decimal("0"):
            raise ValueError(
                "estimated_payout must not be negative."
            )

        return sum(
            evaluation.estimated_payout
            == estimated_payout
            for evaluation in self.evaluations
        )

    def evaluation_at(
        self,
        row_number: int,
    ) -> PayoutReductionRowEvaluation:
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
            f"Utdelning MIN "
            f"{_display_money(self.rule.min_estimated_payout)} | "
            f"MAX "
            f"{_display_money(self.rule.max_estimated_payout)} | "
            f"Ursprung {self.original_row_count} | "
            f"Kvar {self.approved_count} | "
            f"Bort {self.rejected_count} | "
            f"Reducering {self.reduction_percentage}%"
        )