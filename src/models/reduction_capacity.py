"""Capacity policy and assessment models for reduction frames."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from src.models.reduction_frame import ReductionFrame


_PERCENT_QUANTUM = Decimal("0.01")
_HUNDRED = Decimal("100")


class ReductionCapacityLevel(str, Enum):
    """Describes whether a frame is safe to materialize."""

    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"

    @property
    def display_name(self) -> str:
        """Return the Swedish display name."""

        return {
            ReductionCapacityLevel.SAFE: "Säker",
            ReductionCapacityLevel.WARNING: "Varning",
            ReductionCapacityLevel.BLOCKED: "Blockerad",
        }[self]


class ReductionCapacityExceededError(ValueError):
    """Raised when a frame exceeds the materialization policy."""


@dataclass(frozen=True, slots=True)
class ReductionCapacityPolicy:
    """Defines warning and hard limits for materialized rows."""

    warning_row_count: int = 25_000
    maximum_materialized_rows: int = 100_000

    def __post_init__(self) -> None:
        """Validate the complete capacity policy."""

        for field_name in (
            "warning_row_count",
            "maximum_materialized_rows",
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

        if self.warning_row_count > self.maximum_materialized_rows:
            raise ValueError(
                "warning_row_count must not exceed "
                "maximum_materialized_rows."
            )

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable policy description."""

        return (
            f"Varning från {self.warning_row_count} | "
            f"Max {self.maximum_materialized_rows} rader"
        )


@dataclass(frozen=True, slots=True)
class ReductionCapacityAssessment:
    """Contains an exact preflight assessment for one frame."""

    frame: ReductionFrame
    policy: ReductionCapacityPolicy

    def __post_init__(self) -> None:
        """Validate the frame and policy dependencies."""

        if not isinstance(
            self.frame,
            ReductionFrame,
        ):
            raise TypeError(
                "frame must be a ReductionFrame."
            )

        if not isinstance(
            self.policy,
            ReductionCapacityPolicy,
        ):
            raise TypeError(
                "policy must be a ReductionCapacityPolicy."
            )

    @property
    def expected_row_count(self) -> int:
        """Return the exact mathematical frame size."""

        return self.frame.expected_row_count

    @property
    def single_count(self) -> int:
        """Return the number of single-sign frame positions."""

        return self._count_positions_with_sign_count(
            1
        )

    @property
    def double_count(self) -> int:
        """Return the number of double-sign frame positions."""

        return self._count_positions_with_sign_count(
            2
        )

    @property
    def triple_count(self) -> int:
        """Return the number of triple-sign frame positions."""

        return self._count_positions_with_sign_count(
            3
        )

    @property
    def level(self) -> ReductionCapacityLevel:
        """Return the resolved capacity level."""

        if (
            self.expected_row_count
            > self.policy.maximum_materialized_rows
        ):
            return ReductionCapacityLevel.BLOCKED

        if (
            self.expected_row_count
            >= self.policy.warning_row_count
        ):
            return ReductionCapacityLevel.WARNING

        return ReductionCapacityLevel.SAFE

    @property
    def can_materialize(self) -> bool:
        """Return whether full row materialization is permitted."""

        return self.level is not ReductionCapacityLevel.BLOCKED

    @property
    def requires_warning(self) -> bool:
        """Return whether the frame is inside the warning range."""

        return self.level is ReductionCapacityLevel.WARNING

    @property
    def utilization_percentage(self) -> Decimal:
        """Return hard-limit utilization with two decimals."""

        return (
            Decimal(
                self.expected_row_count
            )
            * _HUNDRED
            / Decimal(
                self.policy.maximum_materialized_rows
            )
        ).quantize(
            _PERCENT_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

    @property
    def row_margin(self) -> int:
        """Return signed rows remaining before the hard limit."""

        return (
            self.policy.maximum_materialized_rows
            - self.expected_row_count
        )

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable capacity summary."""

        return (
            f"Kapacitet {self.level.display_name} | "
            f"Rader {self.expected_row_count}/"
            f"{self.policy.maximum_materialized_rows} | "
            f"Singlar {self.single_count} | "
            f"Halvor {self.double_count} | "
            f"Helor {self.triple_count} | "
            f"Utnyttjande {self.utilization_percentage}%"
        )

    def require_materializable(self) -> None:
        """Raise a precise error when the frame is blocked."""

        if self.can_materialize:
            return

        raise ReductionCapacityExceededError(
            "Frame contains "
            f"{self.expected_row_count} rows, which exceeds "
            "the configured materialization limit of "
            f"{self.policy.maximum_materialized_rows}. "
            "Use lazy row iteration or a streaming reduction path "
            "for larger frames."
        )

    def _count_positions_with_sign_count(
        self,
        sign_count: int,
    ) -> int:
        """Count frame positions containing an exact sign count."""

        return sum(
            len(
                allowed
            )
            == sign_count
            for allowed in self.frame.allowed_outcomes
        )