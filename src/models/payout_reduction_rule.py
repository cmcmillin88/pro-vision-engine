"""Models for transparent estimated-payout reduction rules."""

from dataclasses import dataclass
from datetime import datetime
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
    localcontext,
)

from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)


_MONEY_QUANTUM = Decimal("0.01")
_HUNDRED = Decimal("100")
_ONE = Decimal("1")
_CALCULATION_PRECISION = 50
_METHOD_VERSION = "p13-public-share-v1"


def _to_decimal(
    value: object,
    *,
    field_name: str,
) -> Decimal:
    """Convert one numeric value to a finite Decimal."""

    if isinstance(value, bool):
        raise TypeError(
            f"{field_name} must be numeric."
        )

    try:
        decimal_value = Decimal(
            str(value)
        )
    except (InvalidOperation, ValueError) as error:
        raise TypeError(
            f"{field_name} must be numeric."
        ) from error

    if not decimal_value.is_finite():
        raise ValueError(
            f"{field_name} must be finite."
        )

    return decimal_value


def _to_money(
    value: object,
    *,
    field_name: str,
) -> Decimal:
    """Normalize one monetary value to Swedish öre precision."""

    return _to_decimal(
        value,
        field_name=field_name,
    ).quantize(
        _MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


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
class PayoutReductionSnapshot:
    """Freezes public shares and pool inputs at one forecast time.

    The forecast is intentionally transparent and versioned. It is not
    presented as Reducering.se's unpublished internal formula.
    """

    captured_at: datetime
    match_percentages: tuple[
        ThreeWayPercentages,
        ...,
    ]
    turnover: Decimal
    top_prize_pool: Decimal
    base_unit_stake: Decimal = Decimal("1.00")
    source: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the complete forecast snapshot."""

        if not isinstance(
            self.captured_at,
            datetime,
        ):
            raise TypeError(
                "captured_at must be a datetime."
            )

        if (
            self.captured_at.tzinfo is None
            or self.captured_at.utcoffset() is None
        ):
            raise ValueError(
                "captured_at must be timezone-aware."
            )

        if not isinstance(
            self.match_percentages,
            tuple,
        ):
            raise TypeError(
                "match_percentages must be a tuple."
            )

        if not self.match_percentages:
            raise ValueError(
                "A payout snapshot requires at least "
                "one match."
            )

        for percentages in self.match_percentages:
            if not isinstance(
                percentages,
                ThreeWayPercentages,
            ):
                raise TypeError(
                    "match_percentages may only contain "
                    "ThreeWayPercentages objects."
                )

        turnover = _to_money(
            self.turnover,
            field_name="turnover",
        )
        top_prize_pool = _to_money(
            self.top_prize_pool,
            field_name="top_prize_pool",
        )
        base_unit_stake = _to_money(
            self.base_unit_stake,
            field_name="base_unit_stake",
        )

        if turnover <= Decimal("0"):
            raise ValueError(
                "turnover must be greater than zero."
            )

        if top_prize_pool <= Decimal("0"):
            raise ValueError(
                "top_prize_pool must be greater than zero."
            )

        if base_unit_stake <= Decimal("0"):
            raise ValueError(
                "base_unit_stake must be greater than zero."
            )

        object.__setattr__(
            self,
            "turnover",
            turnover,
        )
        object.__setattr__(
            self,
            "top_prize_pool",
            top_prize_pool,
        )
        object.__setattr__(
            self,
            "base_unit_stake",
            base_unit_stake,
        )

        if self.source is not None:
            if not isinstance(
                self.source,
                str,
            ):
                raise TypeError(
                    "source must be a string or None."
                )

            normalized_source = self.source.strip()

            if not normalized_source:
                raise ValueError(
                    "source must not be empty."
                )

            object.__setattr__(
                self,
                "source",
                normalized_source,
            )

    @property
    def method_version(self) -> str:
        """Return the fixed transparent forecast-method version."""

        return _METHOD_VERSION

    @property
    def match_count(self) -> int:
        """Return the number of frozen matches."""

        return len(
            self.match_percentages
        )

    @property
    def pool_units(self) -> Decimal:
        """Return turnover expressed as base-stake units."""

        with localcontext() as context:
            context.prec = _CALCULATION_PRECISION

            return (
                self.turnover
                / self.base_unit_stake
            )

    def percentage_for(
        self,
        match_number: int,
        outcome: Outcome,
    ) -> Decimal:
        """Return one frozen public percentage."""

        if isinstance(match_number, bool) or not isinstance(
            match_number,
            int,
        ):
            raise TypeError(
                "match_number must be an integer."
            )

        if not (
            1
            <= match_number
            <= self.match_count
        ):
            raise IndexError(
                "match_number is outside the snapshot."
            )

        if not isinstance(
            outcome,
            Outcome,
        ):
            raise TypeError(
                "outcome must be an Outcome."
            )

        return self.match_percentages[
            match_number - 1
        ].for_outcome(
            outcome
        )

    def row_share(
        self,
        row: ReductionRow,
    ) -> Decimal:
        """Multiply selected public shares without display rounding."""

        self._validate_row(
            row
        )

        with localcontext() as context:
            context.prec = _CALCULATION_PRECISION

            share = Decimal("1")

            for match_number, outcome in enumerate(
                row.outcomes,
                start=1,
            ):
                share *= (
                    self.percentage_for(
                        match_number,
                        outcome,
                    )
                    / _HUNDRED
                )

        return share

    def expected_winning_units(
        self,
        row: ReductionRow,
    ) -> Decimal:
        """Estimate pool units carrying the complete row."""

        with localcontext() as context:
            context.prec = _CALCULATION_PRECISION

            return (
                self.pool_units
                * self.row_share(
                    row
                )
            )

    def estimated_payout(
        self,
        row: ReductionRow,
    ) -> Decimal:
        """Estimate top-tier payout and cap it at the prize pool.

        Formula:
        prize pool / max(1, estimated winning pool units).
        The monetary forecast is rounded to öre with ROUND_HALF_UP.
        """

        expected_units = self.expected_winning_units(
            row
        )

        divisor = max(
            _ONE,
            expected_units,
        )

        with localcontext() as context:
            context.prec = _CALCULATION_PRECISION

            payout = (
                self.top_prize_pool
                / divisor
            )

        return payout.quantize(
            _MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

    def _validate_row(
        self,
        row: object,
    ) -> None:
        """Validate one complete row against the snapshot."""

        if not isinstance(
            row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        if row.match_count != self.match_count:
            raise ValueError(
                "The row and payout snapshot must contain "
                "the same number of matches."
            )


@dataclass(frozen=True, slots=True)
class PayoutReductionRule:
    """Keeps rows inside an inclusive estimated-payout interval."""

    snapshot: PayoutReductionSnapshot
    min_estimated_payout: Decimal
    max_estimated_payout: Decimal

    def __post_init__(self) -> None:
        """Normalize and validate the payout interval."""

        if not isinstance(
            self.snapshot,
            PayoutReductionSnapshot,
        ):
            raise TypeError(
                "snapshot must be a PayoutReductionSnapshot."
            )

        minimum = _to_money(
            self.min_estimated_payout,
            field_name="min_estimated_payout",
        )
        maximum = _to_money(
            self.max_estimated_payout,
            field_name="max_estimated_payout",
        )

        if minimum < Decimal("0"):
            raise ValueError(
                "min_estimated_payout must not be negative."
            )

        if maximum <= minimum:
            raise ValueError(
                "max_estimated_payout must be greater than "
                "min_estimated_payout."
            )

        object.__setattr__(
            self,
            "min_estimated_payout",
            minimum,
        )
        object.__setattr__(
            self,
            "max_estimated_payout",
            maximum,
        )

    @property
    def minimum_inclusive(self) -> bool:
        """Return the fixed lower-bound policy."""

        return True

    @property
    def maximum_inclusive(self) -> bool:
        """Return the fixed upper-bound policy."""

        return True

    @property
    def condition_text(self) -> str:
        """Return the explicit inclusive payout interval."""

        return (
            f"{_format_money(self.min_estimated_payout)} "
            f"<= utdelning <= "
            f"{_format_money(self.max_estimated_payout)}"
        )

    def estimated_payout(
        self,
        row: ReductionRow,
    ) -> Decimal:
        """Return one row's frozen estimated payout."""

        return self.snapshot.estimated_payout(
            row
        )

    def contains(
        self,
        estimated_payout: Decimal,
    ) -> bool:
        """Return whether a payout satisfies inclusive MIN/MAX."""

        resolved_payout = _to_money(
            estimated_payout,
            field_name="estimated_payout",
        )

        if resolved_payout < Decimal("0"):
            raise ValueError(
                "estimated_payout must not be negative."
            )

        return (
            self.min_estimated_payout
            <= resolved_payout
            <= self.max_estimated_payout
        )

    def is_approved(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether one row satisfies the payout interval."""

        return self.contains(
            self.estimated_payout(
                row
            )
        )