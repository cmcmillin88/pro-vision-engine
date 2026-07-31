"""Reduction frame and complete unreduced system models."""

from __future__ import annotations

from dataclasses import dataclass
from math import prod

from src.models.final_coupon_analysis import (
    FinalCouponAnalysisReport,
)
from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class ReductionFrame:
    """Defines all allowed outcomes in the mathematical frame."""

    game_type: GameType
    allowed_outcomes: tuple[
        tuple[
            Outcome,
            ...,
        ],
        ...,
    ]
    coupon_id: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the complete frame."""

        if not isinstance(
            self.game_type,
            GameType,
        ):
            raise TypeError(
                "game_type must be a GameType."
            )

        if self.game_type is GameType.UNKNOWN:
            raise ValueError(
                "A reduction frame requires a "
                "supported game type."
            )

        if not isinstance(
            self.allowed_outcomes,
            tuple,
        ):
            raise TypeError(
                "allowed_outcomes must be a tuple."
            )

        expected_match_count = (
            self.game_type.expected_match_count
        )

        if expected_match_count is None:
            raise ValueError(
                "The selected game type has no "
                "expected match count."
            )

        if (
            len(
                self.allowed_outcomes
            )
            != expected_match_count
        ):
            raise ValueError(
                f"{self.game_type.display_name} requires "
                f"exactly {expected_match_count} "
                "frame positions."
            )

        for allowed in self.allowed_outcomes:
            self._validate_allowed_outcomes(
                allowed
            )

        if self.coupon_id is not None:
            normalized_coupon_id = (
                self._normalize_required_text(
                    self.coupon_id,
                    field_name="coupon_id",
                )
            )

            object.__setattr__(
                self,
                "coupon_id",
                normalized_coupon_id,
            )

    @classmethod
    def from_coupon_analysis(
        cls,
        coupon_analysis: FinalCouponAnalysisReport,
    ) -> "ReductionFrame":
        """Create a frame from final coupon recommendations."""

        if not isinstance(
            coupon_analysis,
            FinalCouponAnalysisReport,
        ):
            raise TypeError(
                "coupon_analysis must be a "
                "FinalCouponAnalysisReport."
            )

        return cls(
            game_type=coupon_analysis.game_type,
            allowed_outcomes=tuple(
                match_report.recommended_outcomes
                for match_report in (
                    coupon_analysis.match_reports
                )
            ),
            coupon_id=coupon_analysis.coupon_id,
        )

    @property
    def match_count(self) -> int:
        """Return the number of frame positions."""

        return len(
            self.allowed_outcomes
        )

    @property
    def expected_row_count(self) -> int:
        """Return the full mathematical frame size."""

        return prod(
            len(
                allowed
            )
            for allowed in self.allowed_outcomes
        )

    @property
    def recommendation_pattern(self) -> str:
        """Return the frame as ordered compact signs."""

        return "|".join(
            "".join(
                outcome.value
                for outcome in allowed
            )
            for allowed in self.allowed_outcomes
        )

    def allowed_for_match(
        self,
        match_number: int,
    ) -> tuple[Outcome, ...]:
        """Return allowed outcomes for one match."""

        self._validate_match_number(
            match_number
        )

        return self.allowed_outcomes[
            match_number - 1
        ]

    def sign_count_for_match(
        self,
        match_number: int,
    ) -> int:
        """Return the number of signs at one position."""

        return len(
            self.allowed_for_match(
                match_number
            )
        )

    def contains(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether a row belongs to the frame."""

        if not isinstance(
            row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        if row.match_count != self.match_count:
            return False

        return all(
            outcome in allowed
            for outcome, allowed in zip(
                row.outcomes,
                self.allowed_outcomes,
                strict=True,
            )
        )

    @staticmethod
    def _validate_allowed_outcomes(
        allowed: object,
    ) -> None:
        """Validate one frame position."""

        if not isinstance(
            allowed,
            tuple,
        ):
            raise TypeError(
                "Every frame position must be a tuple."
            )

        if not allowed:
            raise ValueError(
                "Every frame position must contain "
                "at least one outcome."
            )

        if len(allowed) > len(
            Outcome.ordered()
        ):
            raise ValueError(
                "A frame position may contain at most "
                "three outcomes."
            )

        for outcome in allowed:
            if not isinstance(
                outcome,
                Outcome,
            ):
                raise TypeError(
                    "Frame positions may only contain "
                    "Outcome values."
                )

        if len(
            set(
                allowed
            )
        ) != len(
            allowed
        ):
            raise ValueError(
                "A frame position must not contain "
                "duplicate outcomes."
            )

        expected_order = tuple(
            outcome
            for outcome in Outcome.ordered()
            if outcome in allowed
        )

        if allowed != expected_order:
            raise ValueError(
                "Frame outcomes must follow official "
                "1-X-2 order."
            )

    def _validate_match_number(
        self,
        match_number: int,
    ) -> None:
        """Validate one one-based match number."""

        if isinstance(
            match_number,
            bool,
        ) or not isinstance(
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
                "match_number is outside the frame."
            )

    @staticmethod
    def _normalize_required_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """Normalize one required text value."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized_value = " ".join(
            value.split()
        )

        if not normalized_value:
            raise ValueError(
                f"{field_name} must not be empty."
            )

        return normalized_value


@dataclass(frozen=True, slots=True)
class BaseReductionSystem:
    """Contains every mathematical row in one frame."""

    frame: ReductionFrame
    rows: tuple[
        ReductionRow,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete unreduced system."""

        if not isinstance(
            self.frame,
            ReductionFrame,
        ):
            raise TypeError(
                "frame must be a ReductionFrame."
            )

        if not isinstance(
            self.rows,
            tuple,
        ):
            raise TypeError(
                "rows must be a tuple."
            )

        for row in self.rows:
            if not isinstance(
                row,
                ReductionRow,
            ):
                raise TypeError(
                    "rows may only contain "
                    "ReductionRow objects."
                )

        if (
            len(
                self.rows
            )
            != self.frame.expected_row_count
        ):
            raise ValueError(
                "The base system must contain exactly "
                "the frame's expected number of rows."
            )

        if len(
            set(
                self.rows
            )
        ) != len(
            self.rows
        ):
            raise ValueError(
                "The base system must not contain "
                "duplicate rows."
            )

        if not all(
            self.frame.contains(
                row
            )
            for row in self.rows
        ):
            raise ValueError(
                "Every system row must belong "
                "to the frame."
            )

    @property
    def row_count(self) -> int:
        """Return the number of generated rows."""

        return len(
            self.rows
        )

    @property
    def is_complete_frame(self) -> bool:
        """Return whether the full frame is represented."""

        return (
            self.row_count
            == self.frame.expected_row_count
        )

    @property
    def first_row(self) -> ReductionRow:
        """Return the first deterministic row."""

        return self.rows[0]

    @property
    def last_row(self) -> ReductionRow:
        """Return the final deterministic row."""

        return self.rows[-1]

    def row_at(
        self,
        row_number: int,
    ) -> ReductionRow:
        """Return one row by one-based row number."""

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
            <= self.row_count
        ):
            raise IndexError(
                "row_number is outside the system."
            )

        return self.rows[
            row_number - 1
        ]

    def contains(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether the system contains one row."""

        if not isinstance(
            row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        return row in self.rows