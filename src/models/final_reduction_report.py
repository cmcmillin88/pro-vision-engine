"""Final export-ready report models for complete reduction systems."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from src.models.reduction_condition_result import (
    ReductionConditionResult,
)
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)
from src.models.reduction_frame import (
    BaseReductionSystem,
    ReductionFrame,
)
from src.models.reduction_row import ReductionRow


_PERCENT_QUANTUM = Decimal("0.01")
_MONEY_QUANTUM = Decimal("0.01")
_HUNDRED = Decimal("100")
_REPORT_VERSION = "p13-reduction-report-v1"


def _percentage(
    numerator: int,
    denominator: int,
) -> Decimal:
    """Return a two-decimal percentage using ROUND_HALF_UP."""

    if denominator <= 0:
        raise ValueError(
            "percentage denominator must be greater than zero."
        )

    return (
        Decimal(numerator)
        * _HUNDRED
        / Decimal(denominator)
    ).quantize(
        _PERCENT_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _normalize_row_price(
    value: object,
) -> Decimal:
    """Normalize one positive row price to öre precision."""

    if isinstance(value, bool):
        raise TypeError(
            "row_price must be numeric or None."
        )

    try:
        resolved = Decimal(
            str(value)
        )
    except (InvalidOperation, ValueError) as error:
        raise TypeError(
            "row_price must be numeric or None."
        ) from error

    if not resolved.is_finite():
        raise ValueError(
            "row_price must be finite."
        )

    resolved = resolved.quantize(
        _MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )

    if resolved <= Decimal("0"):
        raise ValueError(
            "row_price must be greater than zero."
        )

    return resolved


def _format_money(
    value: Decimal,
) -> str:
    """Format one monetary value with two decimals."""

    return str(
        value.quantize(
            _MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
    )


@dataclass(frozen=True, slots=True)
class ReductionConditionImpact:
    """Summarizes one condition group's independent effect."""

    condition_type: ReductionConditionType
    original_row_count: int
    independently_approved_count: int
    independently_rejected_count: int
    exclusive_rejection_count: int

    def __post_init__(self) -> None:
        """Validate one complete condition-impact summary."""

        if not isinstance(
            self.condition_type,
            ReductionConditionType,
        ):
            raise TypeError(
                "condition_type must be a ReductionConditionType."
            )

        for field_name in (
            "original_row_count",
            "independently_approved_count",
            "independently_rejected_count",
            "exclusive_rejection_count",
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

        if self.original_row_count <= 0:
            raise ValueError(
                "original_row_count must be greater than zero."
            )

        if (
            self.independently_approved_count
            + self.independently_rejected_count
            != self.original_row_count
        ):
            raise ValueError(
                "Independent approved and rejected counts must "
                "equal original_row_count."
            )

        if (
            self.exclusive_rejection_count
            > self.independently_rejected_count
        ):
            raise ValueError(
                "exclusive_rejection_count must not exceed "
                "independently_rejected_count."
            )

    @property
    def display_name(self) -> str:
        """Return the Swedish condition name."""

        return self.condition_type.display_name

    @property
    def retained_percentage(self) -> Decimal:
        """Return rows independently retained by this condition."""

        return _percentage(
            self.independently_approved_count,
            self.original_row_count,
        )

    @property
    def reduction_percentage(self) -> Decimal:
        """Return rows independently rejected by this condition."""

        return _percentage(
            self.independently_rejected_count,
            self.original_row_count,
        )

    @property
    def summary_line(self) -> str:
        """Return a compact impact description."""

        return (
            f"{self.display_name} | "
            f"Kvar {self.independently_approved_count} | "
            f"Bort {self.independently_rejected_count} | "
            f"Ensamt avgörande {self.exclusive_rejection_count} | "
            f"Reducering {self.reduction_percentage}%"
        )


@dataclass(frozen=True, slots=True)
class ReductionRejectionPattern:
    """Groups rows rejected by the same exact condition combination."""

    condition_types: tuple[
        ReductionConditionType,
        ...,
    ]
    row_count: int
    total_rejected_row_count: int

    def __post_init__(self) -> None:
        """Validate one deterministic rejection-pattern group."""

        if not isinstance(
            self.condition_types,
            tuple,
        ):
            raise TypeError(
                "condition_types must be a tuple."
            )

        if not self.condition_types:
            raise ValueError(
                "A rejection pattern requires at least one condition."
            )

        for condition_type in self.condition_types:
            if not isinstance(
                condition_type,
                ReductionConditionType,
            ):
                raise TypeError(
                    "condition_types may only contain "
                    "ReductionConditionType values."
                )

        if len(
            set(
                self.condition_types
            )
        ) != len(
            self.condition_types
        ):
            raise ValueError(
                "condition_types must not contain duplicates."
            )

        expected_order = tuple(
            condition_type
            for condition_type in ReductionConditionType.ordered()
            if condition_type in self.condition_types
        )

        if self.condition_types != expected_order:
            raise ValueError(
                "condition_types must follow official condition order."
            )

        for field_name in (
            "row_count",
            "total_rejected_row_count",
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

            if value <= 0:
                raise ValueError(
                    f"{field_name} must be greater than zero."
                )

        if self.row_count > self.total_rejected_row_count:
            raise ValueError(
                "row_count must not exceed total_rejected_row_count."
            )

    @property
    def pattern(self) -> str:
        """Return the condition combination as readable text."""

        return " + ".join(
            condition_type.display_name
            for condition_type in self.condition_types
        )

    @property
    def percentage_of_rejected(self) -> Decimal:
        """Return this pattern's share of all rejected rows."""

        return _percentage(
            self.row_count,
            self.total_rejected_row_count,
        )

    @property
    def summary_line(self) -> str:
        """Return a compact rejection-pattern description."""

        return (
            f"{self.pattern} | "
            f"Rader {self.row_count} | "
            f"Andel av borttagna {self.percentage_of_rejected}%"
        )


@dataclass(frozen=True, slots=True)
class FinalReductionReport:
    """Contains the complete export-ready result of one reduction run."""

    condition_result: ReductionConditionResult
    condition_impacts: tuple[
        ReductionConditionImpact,
        ...,
    ]
    rejection_patterns: tuple[
        ReductionRejectionPattern,
        ...,
    ]
    row_price: Decimal | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the complete final report."""

        if not isinstance(
            self.condition_result,
            ReductionConditionResult,
        ):
            raise TypeError(
                "condition_result must be a ReductionConditionResult."
            )

        if not isinstance(
            self.condition_impacts,
            tuple,
        ):
            raise TypeError(
                "condition_impacts must be a tuple."
            )

        if not isinstance(
            self.rejection_patterns,
            tuple,
        ):
            raise TypeError(
                "rejection_patterns must be a tuple."
            )

        if self.row_price is not None:
            object.__setattr__(
                self,
                "row_price",
                _normalize_row_price(
                    self.row_price
                ),
            )

        expected_types = self.condition_set.condition_types
        impact_types = tuple(
            impact.condition_type
            for impact in self.condition_impacts
        )

        if impact_types != expected_types:
            raise ValueError(
                "condition_impacts must contain every active "
                "condition in official order."
            )

        for impact in self.condition_impacts:
            if not isinstance(
                impact,
                ReductionConditionImpact,
            ):
                raise TypeError(
                    "condition_impacts may only contain "
                    "ReductionConditionImpact objects."
                )

            if impact.original_row_count != self.original_row_count:
                raise ValueError(
                    "Every condition impact must use the report's "
                    "original row count."
                )

            expected_approved = (
                self.condition_result.approved_count_for_condition(
                    impact.condition_type
                )
            )
            expected_exclusive = sum(
                evaluation.rejected_condition_types
                == (
                    impact.condition_type,
                )
                for evaluation in self.condition_result.evaluations
            )

            if (
                impact.independently_approved_count
                != expected_approved
            ):
                raise ValueError(
                    "Condition impact approved count does not match "
                    "the underlying condition result."
                )

            if (
                impact.exclusive_rejection_count
                != expected_exclusive
            ):
                raise ValueError(
                    "Condition impact exclusive rejection count does "
                    "not match the underlying condition result."
                )

        expected_pattern_counts = Counter(
            evaluation.rejected_condition_types
            for evaluation in self.condition_result.rejected_evaluations
        )

        supplied_pattern_counts: Counter[
            tuple[ReductionConditionType, ...]
        ] = Counter()

        for pattern in self.rejection_patterns:
            if not isinstance(
                pattern,
                ReductionRejectionPattern,
            ):
                raise TypeError(
                    "rejection_patterns may only contain "
                    "ReductionRejectionPattern objects."
                )

            if (
                pattern.total_rejected_row_count
                != self.rejected_count
            ):
                raise ValueError(
                    "Every rejection pattern must use the report's "
                    "total rejected row count."
                )

            supplied_pattern_counts[
                pattern.condition_types
            ] += pattern.row_count

        if supplied_pattern_counts != expected_pattern_counts:
            raise ValueError(
                "rejection_patterns must exactly describe every "
                "rejected row."
            )

    @property
    def report_version(self) -> str:
        """Return the fixed report-contract version."""

        return _REPORT_VERSION

    @property
    def base_system(self) -> BaseReductionSystem:
        """Return the complete unreduced system."""

        return self.condition_result.base_system

    @property
    def frame(self) -> ReductionFrame:
        """Return the turquoise reduction frame."""

        return self.base_system.frame

    @property
    def condition_set(self) -> ReductionConditionSet:
        """Return all active reduction conditions."""

        return self.condition_result.condition_set

    @property
    def game_type(self):
        """Return the coupon's game type."""

        return self.frame.game_type

    @property
    def game_type_name(self) -> str:
        """Return the game type with human-readable capitalization."""

        return self.game_type.value.capitalize()

    @property
    def coupon_id(self) -> str | None:
        """Return the optional coupon identifier."""

        return self.frame.coupon_id

    @property
    def frame_pattern(self) -> str:
        """Return the complete turquoise frame pattern."""

        return "|".join(
            "".join(
                outcome.value
                for outcome in allowed
            )
            for allowed in self.frame.allowed_outcomes
        )

    @property
    def condition_pattern(self) -> str:
        """Return all active reduction conditions as text."""

        return self.condition_set.condition_pattern

    @property
    def active_condition_types(
        self,
    ) -> tuple[ReductionConditionType, ...]:
        """Return active groups in official order."""

        return self.condition_set.condition_types

    @property
    def condition_count(self) -> int:
        """Return the number of active condition groups."""

        return self.condition_set.condition_count

    @property
    def atomic_condition_count(self) -> int:
        """Return the number of independently checked conditions."""

        return self.condition_set.atomic_condition_count

    @property
    def original_row_count(self) -> int:
        """Return the full frame row count."""

        return self.condition_result.original_row_count

    @property
    def approved_count(self) -> int:
        """Return the final surviving row count."""

        return self.condition_result.approved_count

    @property
    def rejected_count(self) -> int:
        """Return the final removed row count."""

        return self.condition_result.rejected_count

    @property
    def retained_percentage(self) -> Decimal:
        """Return the final retained percentage."""

        return self.condition_result.retained_percentage

    @property
    def reduction_percentage(self) -> Decimal:
        """Return the final reduction percentage."""

        return self.condition_result.reduction_percentage

    @property
    def is_empty(self) -> bool:
        """Return whether the reduction removed every row."""

        return self.condition_result.is_empty

    @property
    def approved_rows(self) -> tuple[ReductionRow, ...]:
        """Return surviving rows in deterministic order."""

        return self.condition_result.approved_rows

    @property
    def rejected_rows(self) -> tuple[ReductionRow, ...]:
        """Return removed rows in deterministic order."""

        return self.condition_result.rejected_rows

    @property
    def approved_symbols(self) -> tuple[str, ...]:
        """Return surviving rows as compact symbols."""

        return tuple(
            row.symbols
            for row in self.approved_rows
        )

    @property
    def original_cost(self) -> Decimal | None:
        """Return the unreduced system cost when row price is known."""

        if self.row_price is None:
            return None

        return (
            self.row_price
            * Decimal(
                self.original_row_count
            )
        ).quantize(
            _MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

    @property
    def final_cost(self) -> Decimal | None:
        """Return the reduced system cost when row price is known."""

        if self.row_price is None:
            return None

        return (
            self.row_price
            * Decimal(
                self.approved_count
            )
        ).quantize(
            _MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

    @property
    def saved_cost(self) -> Decimal | None:
        """Return the removed cost when row price is known."""

        if self.original_cost is None or self.final_cost is None:
            return None

        return (
            self.original_cost
            - self.final_cost
        ).quantize(
            _MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

    @property
    def strictest_condition(self) -> ReductionConditionImpact:
        """Return the condition retaining the fewest rows alone."""

        return min(
            self.condition_impacts,
            key=lambda impact: (
                impact.independently_approved_count,
                self.active_condition_types.index(
                    impact.condition_type
                ),
            ),
        )

    @property
    def combination_removed_count(self) -> int:
        """Return extra rows removed beyond the strictest condition."""

        return (
            self.strictest_condition.independently_approved_count
            - self.approved_count
        )

    @property
    def exclusive_rejection_total(self) -> int:
        """Return rows rejected by exactly one condition group."""

        return sum(
            impact.exclusive_rejection_count
            for impact in self.condition_impacts
        )

    @property
    def uses_frozen_odds(self) -> bool:
        """Return whether total-odds reduction is active."""

        return self.condition_set.odds_rule is not None

    @property
    def uses_estimated_payout(self) -> bool:
        """Return whether transparent payout estimation is active."""

        return self.condition_set.payout_rule is not None

    @property
    def snapshot_times(self) -> tuple[datetime, ...]:
        """Return active market snapshot times in condition order."""

        values: list[datetime] = []

        if self.condition_set.odds_rule is not None:
            values.append(
                self.condition_set.odds_rule.snapshot.captured_at
            )

        if self.condition_set.payout_rule is not None:
            values.append(
                self.condition_set.payout_rule.snapshot.captured_at
            )

        return tuple(
            values
        )

    @property
    def frozen_sources(self) -> tuple[str, ...]:
        """Return non-empty frozen data-source names."""

        values: list[str] = []

        if (
            self.condition_set.odds_rule is not None
            and self.condition_set.odds_rule.snapshot.source is not None
        ):
            values.append(
                self.condition_set.odds_rule.snapshot.source
            )

        if (
            self.condition_set.payout_rule is not None
            and self.condition_set.payout_rule.snapshot.source is not None
        ):
            values.append(
                self.condition_set.payout_rule.snapshot.source
            )

        return tuple(
            values
        )

    @property
    def payout_method_version(self) -> str | None:
        """Return the payout model version when active."""

        if self.condition_set.payout_rule is None:
            return None

        return (
            self.condition_set
            .payout_rule
            .snapshot
            .method_version
        )

    def condition_impact_for(
        self,
        condition_type: ReductionConditionType,
    ) -> ReductionConditionImpact:
        """Return the final impact summary for one active group."""

        if not isinstance(
            condition_type,
            ReductionConditionType,
        ):
            raise TypeError(
                "condition_type must be a ReductionConditionType."
            )

        for impact in self.condition_impacts:
            if impact.condition_type is condition_type:
                return impact

        raise KeyError(
            f"Condition type {condition_type.value} is not active."
        )

    @property
    def summary_line(self) -> str:
        """Return the primary human-readable report summary."""

        cost_text = ""

        if self.final_cost is not None:
            cost_text = (
                f" | Kostnad {_format_money(self.final_cost)} kr"
            )

        return (
            f"{self.game_type_name} | "
            f"Villkor {self.condition_count} | "
            f"Ursprung {self.original_row_count} | "
            f"Kvar {self.approved_count} | "
            f"Bort {self.rejected_count} | "
            f"Reducering {self.reduction_percentage}%"
            f"{cost_text}"
        )

    @property
    def analysis_line(self) -> str:
        """Return a compact diagnostic reduction summary."""

        return (
            f"Striktast {self.strictest_condition.display_name} "
            f"({self.strictest_condition.independently_approved_count}/"
            f"{self.original_row_count}) | "
            f"Kombinationseffekt {self.combination_removed_count} | "
            f"Ensamt avgörande {self.exclusive_rejection_total}"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe, versioned report representation."""

        cost_data: dict[str, str] | None = None

        if self.row_price is not None:
            assert self.original_cost is not None
            assert self.final_cost is not None
            assert self.saved_cost is not None

            cost_data = {
                "row_price": _format_money(
                    self.row_price
                ),
                "original_cost": _format_money(
                    self.original_cost
                ),
                "final_cost": _format_money(
                    self.final_cost
                ),
                "saved_cost": _format_money(
                    self.saved_cost
                ),
                "currency": "SEK",
            }

        snapshots: list[dict[str, str | None]] = []

        if self.condition_set.odds_rule is not None:
            odds_snapshot = self.condition_set.odds_rule.snapshot
            snapshots.append(
                {
                    "type": "odds",
                    "captured_at": (
                        odds_snapshot.captured_at.isoformat()
                    ),
                    "source": odds_snapshot.source,
                    "method_version": None,
                }
            )

        if self.condition_set.payout_rule is not None:
            payout_snapshot = self.condition_set.payout_rule.snapshot
            snapshots.append(
                {
                    "type": "payout",
                    "captured_at": (
                        payout_snapshot.captured_at.isoformat()
                    ),
                    "source": payout_snapshot.source,
                    "method_version": (
                        payout_snapshot.method_version
                    ),
                }
            )

        return {
            "version": self.report_version,
            "game_type": self.game_type.value,
            "coupon_id": self.coupon_id,
            "frame_pattern": self.frame_pattern,
            "condition_pattern": self.condition_pattern,
            "condition_count": self.condition_count,
            "atomic_condition_count": self.atomic_condition_count,
            "counts": {
                "original": self.original_row_count,
                "approved": self.approved_count,
                "rejected": self.rejected_count,
            },
            "percentages": {
                "retained": str(
                    self.retained_percentage
                ),
                "reduced": str(
                    self.reduction_percentage
                ),
            },
            "costs": cost_data,
            "strictest_condition": (
                self.strictest_condition.condition_type.value
            ),
            "combination_removed_count": (
                self.combination_removed_count
            ),
            "exclusive_rejection_total": (
                self.exclusive_rejection_total
            ),
            "condition_impacts": [
                {
                    "condition_type": (
                        impact.condition_type.value
                    ),
                    "approved": (
                        impact.independently_approved_count
                    ),
                    "rejected": (
                        impact.independently_rejected_count
                    ),
                    "exclusive_rejections": (
                        impact.exclusive_rejection_count
                    ),
                    "reduction_percentage": str(
                        impact.reduction_percentage
                    ),
                }
                for impact in self.condition_impacts
            ],
            "rejection_patterns": [
                {
                    "condition_types": [
                        condition_type.value
                        for condition_type
                        in pattern.condition_types
                    ],
                    "row_count": pattern.row_count,
                    "percentage_of_rejected": str(
                        pattern.percentage_of_rejected
                    ),
                }
                for pattern in self.rejection_patterns
            ],
            "approved_rows": list(
                self.approved_symbols
            ),
            "snapshots": snapshots,
            "uses_frozen_odds": self.uses_frozen_odds,
            "uses_estimated_payout": (
                self.uses_estimated_payout
            ),
        }