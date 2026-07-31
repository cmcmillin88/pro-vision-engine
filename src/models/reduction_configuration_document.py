"""Versioned document for practical coupon-reduction configuration."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import ClassVar

from src.models.coupon_analysis_run import CouponAnalysisRun
from src.models.game_type import GameType
from src.models.reduction_condition_set import (
    ReductionConditionSet,
    ReductionConditionType,
)


_MONEY_QUANTUM = Decimal("0.01")


class MarketSnapshotSelection(str, Enum):
    """Selects which imported market snapshot a rule freezes."""

    EARLIER = "earlier"
    LATER = "later"

    @property
    def display_name(self) -> str:
        """Return the Swedish display name."""

        return {
            MarketSnapshotSelection.EARLIER: "Tidigare",
            MarketSnapshotSelection.LATER: "Senare",
        }[self]


@dataclass(frozen=True, slots=True)
class ReductionConfigurationDocument:
    """Links one strict reduction configuration to an analysis run."""

    CURRENT_SCHEMA_VERSION: ClassVar[str] = "p13-reduction-input-v1"

    schema_version: str
    analysis_run: CouponAnalysisRun
    condition_set: ReductionConditionSet
    row_price: Decimal
    target_game_type: GameType
    target_coupon_id: str | None = None
    expected_frame_pattern: str | None = None
    odds_snapshot_selection: MarketSnapshotSelection | None = None
    payout_snapshot_selection: MarketSnapshotSelection | None = None
    source_name: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate the complete configuration document."""

        if not isinstance(
            self.schema_version,
            str,
        ):
            raise TypeError(
                "schema_version must be a string."
            )

        normalized_version = self.schema_version.strip()

        if normalized_version != self.CURRENT_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported reduction-configuration schema version: "
                f"{normalized_version!r}."
            )

        object.__setattr__(
            self,
            "schema_version",
            normalized_version,
        )

        if not isinstance(
            self.analysis_run,
            CouponAnalysisRun,
        ):
            raise TypeError(
                "analysis_run must be a CouponAnalysisRun."
            )

        if not isinstance(
            self.condition_set,
            ReductionConditionSet,
        ):
            raise TypeError(
                "condition_set must be a ReductionConditionSet."
            )

        if not isinstance(
            self.target_game_type,
            GameType,
        ):
            raise TypeError(
                "target_game_type must be a GameType."
            )

        if self.target_game_type is GameType.UNKNOWN:
            raise ValueError(
                "target_game_type must be supported."
            )

        row_price = self._to_money(
            self.row_price,
            field_name="row_price",
        )

        if row_price <= Decimal("0"):
            raise ValueError(
                "row_price must be greater than zero."
            )

        object.__setattr__(
            self,
            "row_price",
            row_price,
        )

        for field_name in (
            "target_coupon_id",
            "expected_frame_pattern",
            "source_name",
        ):
            value = getattr(
                self,
                field_name,
            )

            if value is None:
                continue

            normalized_value = self._normalize_text(
                value,
                field_name=field_name,
            )

            object.__setattr__(
                self,
                field_name,
                normalized_value,
            )

        for field_name in (
            "odds_snapshot_selection",
            "payout_snapshot_selection",
        ):
            value = getattr(
                self,
                field_name,
            )

            if (
                value is not None
                and not isinstance(
                    value,
                    MarketSnapshotSelection,
                )
            ):
                raise TypeError(
                    f"{field_name} must be a "
                    "MarketSnapshotSelection or None."
                )

        self._validate_snapshot_metadata()
        self._validate_target()

    def _validate_snapshot_metadata(self) -> None:
        """Require audit metadata exactly when market rules are active."""

        has_odds = (
            ReductionConditionType.ODDS
            in self.condition_set.condition_types
        )
        has_payout = (
            ReductionConditionType.PAYOUT
            in self.condition_set.condition_types
        )

        if has_odds != (
            self.odds_snapshot_selection is not None
        ):
            raise ValueError(
                "odds_snapshot_selection must be supplied "
                "exactly when an odds rule is active."
            )

        if has_payout != (
            self.payout_snapshot_selection is not None
        ):
            raise ValueError(
                "payout_snapshot_selection must be supplied "
                "exactly when a payout rule is active."
            )

    def _validate_target(self) -> None:
        """Ensure the configuration targets the linked analysis run."""

        if self.target_game_type is not self.analysis_run.game_type:
            raise ValueError(
                "target_game_type does not match the analysis run."
            )

        if (
            self.target_coupon_id is not None
            and self.target_coupon_id != self.analysis_run.coupon_id
        ):
            raise ValueError(
                "target_coupon_id does not match the analysis run."
            )

        if (
            self.expected_frame_pattern is not None
            and self.expected_frame_pattern
            != self.analysis_run.recommendation_pattern
        ):
            raise ValueError(
                "expected_frame_pattern does not match the "
                "analysis run's turquoise frame."
            )

    @property
    def coupon_id(self) -> str | None:
        """Return the linked coupon identifier."""

        return self.analysis_run.coupon_id

    @property
    def game_type(self) -> GameType:
        """Return the linked game type."""

        return self.analysis_run.game_type

    @property
    def frame_pattern(self) -> str:
        """Return the resolved turquoise frame pattern."""

        return self.analysis_run.recommendation_pattern

    @property
    def condition_count(self) -> int:
        """Return the number of active condition groups."""

        return self.condition_set.condition_count

    @property
    def atomic_condition_count(self) -> int:
        """Return the number of independently evaluated conditions."""

        return self.condition_set.atomic_condition_count

    @property
    def condition_pattern(self) -> str:
        """Return the compact resolved condition pattern."""

        return self.condition_set.condition_pattern

    @property
    def frozen_sources(self) -> tuple[str, ...]:
        """Return unique odds and payout sources in condition order."""

        sources: list[str] = []

        if (
            self.condition_set.odds_rule is not None
            and self.condition_set.odds_rule.snapshot.source is not None
        ):
            sources.append(
                self.condition_set.odds_rule.snapshot.source
            )

        if (
            self.condition_set.payout_rule is not None
            and self.condition_set.payout_rule.snapshot.source is not None
        ):
            sources.append(
                self.condition_set.payout_rule.snapshot.source
            )

        return tuple(
            dict.fromkeys(
                sources
            )
        )

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable configuration summary."""

        coupon_text = (
            self.coupon_id
            if self.coupon_id is not None
            else "utan id"
        )

        return (
            f"{self.game_type.display_name} | "
            f"Kupong {coupon_text} | "
            f"Villkor {self.condition_count} | "
            f"Atomvillkor {self.atomic_condition_count} | "
            f"Radpris {self.row_price} kr | "
            f"Kontrakt {self.schema_version}"
        )

    @staticmethod
    def _normalize_text(
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

    @staticmethod
    def _to_money(
        value: object,
        *,
        field_name: str,
    ) -> Decimal:
        """Normalize one monetary value to öre precision."""

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{field_name} must be numeric."
            )

        try:
            decimal_value = Decimal(
                str(value)
            )
        except (
            InvalidOperation,
            ValueError,
        ) as error:
            raise TypeError(
                f"{field_name} must be numeric."
            ) from error

        if not decimal_value.is_finite():
            raise ValueError(
                f"{field_name} must be finite."
            )

        return decimal_value.quantize(
            _MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )