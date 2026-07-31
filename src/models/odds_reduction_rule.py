"""Models for deterministic total-odds reduction rules."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow
from src.models.three_way_odds import ThreeWayOdds


_DISPLAY_QUANTUM = Decimal("0.01")


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


def _format_odds(
    value: Decimal,
) -> str:
    """Format total odds for human-readable output only."""

    return str(
        value.quantize(
            _DISPLAY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
    )


@dataclass(frozen=True, slots=True)
class OddsReductionSnapshot:
    """Freezes complete 1-X-2 odds at one reduction time."""

    captured_at: datetime
    match_odds: tuple[
        ThreeWayOdds,
        ...,
    ]
    source: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the complete odds snapshot."""

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
            self.match_odds,
            tuple,
        ):
            raise TypeError(
                "match_odds must be a tuple."
            )

        if not self.match_odds:
            raise ValueError(
                "An odds snapshot requires at least "
                "one match."
            )

        for odds in self.match_odds:
            if not isinstance(
                odds,
                ThreeWayOdds,
            ):
                raise TypeError(
                    "match_odds may only contain "
                    "ThreeWayOdds objects."
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
    def match_count(self) -> int:
        """Return the number of frozen matches."""

        return len(
            self.match_odds
        )

    def odds_for(
        self,
        match_number: int,
        outcome: Outcome,
    ) -> Decimal:
        """Return frozen odds for one match-outcome cell."""

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

        return self.match_odds[
            match_number - 1
        ].for_outcome(
            outcome
        )

    def total_odds(
        self,
        row: ReductionRow,
    ) -> Decimal:
        """Multiply selected decimal odds without intermediate rounding."""

        if not isinstance(
            row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        if row.match_count != self.match_count:
            raise ValueError(
                "The row and odds snapshot must contain "
                "the same number of matches."
            )

        selected_odds = tuple(
            self.odds_for(
                match_number,
                outcome,
            )
            for match_number, outcome in enumerate(
                row.outcomes,
                start=1,
            )
        )

        required_precision = (
            sum(
                max(
                    1,
                    len(
                        odds.as_tuple().digits
                    ),
                )
                for odds in selected_odds
            )
            + 2
        )

        with localcontext() as context:
            context.prec = required_precision

            total = Decimal("1")

            for odds in selected_odds:
                total *= odds

        return total


@dataclass(frozen=True, slots=True)
class OddsReductionRule:
    """Keeps rows inside a frozen total-odds interval."""

    snapshot: OddsReductionSnapshot
    min_total_odds: Decimal
    max_total_odds: Decimal

    def __post_init__(self) -> None:
        """Normalize and validate the total-odds interval."""

        if not isinstance(
            self.snapshot,
            OddsReductionSnapshot,
        ):
            raise TypeError(
                "snapshot must be an OddsReductionSnapshot."
            )

        minimum = _to_decimal(
            self.min_total_odds,
            field_name="min_total_odds",
        )
        maximum = _to_decimal(
            self.max_total_odds,
            field_name="max_total_odds",
        )

        if minimum < Decimal("1"):
            raise ValueError(
                "min_total_odds must be at least 1."
            )

        if maximum <= minimum:
            raise ValueError(
                "max_total_odds must be greater than "
                "min_total_odds."
            )

        object.__setattr__(
            self,
            "min_total_odds",
            minimum,
        )
        object.__setattr__(
            self,
            "max_total_odds",
            maximum,
        )

    @property
    def minimum_inclusive(self) -> bool:
        """Return the fixed lower-bound policy."""

        return True

    @property
    def maximum_inclusive(self) -> bool:
        """Return the fixed upper-bound policy."""

        return False

    @property
    def condition_text(self) -> str:
        """Return the explicit half-open total-odds interval."""

        return (
            f"{_format_odds(self.min_total_odds)} "
            f"<= odds < "
            f"{_format_odds(self.max_total_odds)}"
        )

    def total_odds(
        self,
        row: ReductionRow,
    ) -> Decimal:
        """Return one row's frozen total odds."""

        return self.snapshot.total_odds(
            row
        )

    def contains(
        self,
        total_odds: Decimal,
    ) -> bool:
        """Return whether total odds satisfy [MIN, MAX)."""

        resolved_total = _to_decimal(
            total_odds,
            field_name="total_odds",
        )

        if resolved_total <= Decimal("0"):
            raise ValueError(
                "total_odds must be greater than zero."
            )

        return (
            self.min_total_odds
            <= resolved_total
            < self.max_total_odds
        )

    def is_approved(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether one row satisfies the odds interval."""

        return self.contains(
            self.total_odds(
                row
            )
        )