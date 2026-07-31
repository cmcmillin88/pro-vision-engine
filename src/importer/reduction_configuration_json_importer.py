"""Strict JSON importer for practical reduction configuration."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from src.models.color_reduction_rule import (
    ColoredOutcomeCell,
    ColorReductionRule,
    ReductionColor,
)
from src.models.color_reduction_rule_set import (
    ColorReductionRuleSet,
)
from src.models.coupon_analysis_run import CouponAnalysisRun
from src.models.game_type import GameType
from src.models.odds_reduction_rule import (
    OddsReductionRule,
    OddsReductionSnapshot,
)
from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
    OutcomeCountCondition,
)
from src.models.outcome import Outcome
from src.models.payout_reduction_rule import (
    PayoutReductionRule,
    PayoutReductionSnapshot,
)
from src.models.point_reduction_rule import (
    PointAssignment,
    PointReductionRule,
)
from src.models.reduction_condition_set import (
    ReductionConditionSet,
)
from src.models.reduction_configuration_document import (
    MarketSnapshotSelection,
    ReductionConfigurationDocument,
)


class ReductionConfigurationJsonImporter:
    """Imports one versioned reduction configuration for an analysis run."""

    schema_version = ReductionConfigurationDocument.CURRENT_SCHEMA_VERSION

    _top_level_fields = {
        "schema_version",
        "target",
        "row_price",
        "conditions",
    }
    _target_fields = {
        "coupon_id",
        "game_type",
        "frame_pattern",
    }
    _condition_fields = {
        "colors",
        "one_x_two",
        "points",
        "odds",
        "payout",
    }
    _color_fields = {
        "color",
        "cells",
        "min",
        "max",
    }
    _cell_fields = {
        "match",
        "outcome",
    }
    _point_fields = {
        "assignments",
        "min",
        "max",
    }
    _assignment_fields = {
        "match",
        "outcome",
        "points",
    }
    _range_fields = {
        "min",
        "max",
    }
    _market_rule_fields = {
        "market_snapshot",
        "min",
        "max",
    }
    _payout_fields = {
        "market_snapshot",
        "turnover",
        "top_prize_pool",
        "base_unit_stake",
        "min",
        "max",
    }

    def from_file(
        self,
        path: str | Path,
        analysis_run: CouponAnalysisRun,
    ) -> ReductionConfigurationDocument:
        """Load one UTF-8 configuration file."""

        resolved_path = Path(
            path
        )

        if not resolved_path.is_file():
            raise FileNotFoundError(
                "Reduction-configuration JSON file not found: "
                f"{resolved_path}"
            )

        json_text = resolved_path.read_text(
            encoding="utf-8-sig"
        )

        return self.from_json(
            json_text,
            analysis_run,
            source_name=str(
                resolved_path
            ),
        )

    def from_json(
        self,
        json_text: str,
        analysis_run: CouponAnalysisRun,
        *,
        source_name: str | None = None,
    ) -> ReductionConfigurationDocument:
        """Parse one reduction-configuration JSON string."""

        if not isinstance(
            json_text,
            str,
        ):
            raise TypeError(
                "json_text must be a string."
            )

        if not json_text.strip():
            raise ValueError(
                "json_text must not be empty."
            )

        try:
            payload = json.loads(
                json_text
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                "Invalid reduction-configuration JSON: "
                f"{error.msg} at line {error.lineno}, "
                f"column {error.colno}."
            ) from error

        return self.from_dict(
            payload,
            analysis_run,
            source_name=source_name,
        )

    def from_dict(
        self,
        payload: Mapping[str, Any],
        analysis_run: CouponAnalysisRun,
        *,
        source_name: str | None = None,
    ) -> ReductionConfigurationDocument:
        """Import one decoded configuration mapping."""

        self._require_analysis_run(
            analysis_run
        )

        root = self._require_mapping(
            payload,
            path="$",
        )
        self._reject_unknown_fields(
            root,
            self._top_level_fields,
            path="$",
        )
        self._require_fields(
            root,
            self._top_level_fields,
            path="$",
        )

        schema_version = self._require_text(
            root["schema_version"],
            path="$.schema_version",
        )
        row_price = self._require_numeric(
            root["row_price"],
            path="$.row_price",
        )

        target = self._parse_target(
            root["target"],
            analysis_run,
        )
        conditions = self._parse_conditions(
            root["conditions"],
            analysis_run,
        )

        return ReductionConfigurationDocument(
            schema_version=schema_version,
            analysis_run=analysis_run,
            condition_set=conditions["condition_set"],
            row_price=row_price,
            target_game_type=target["game_type"],
            target_coupon_id=target["coupon_id"],
            expected_frame_pattern=target["frame_pattern"],
            odds_snapshot_selection=conditions[
                "odds_snapshot_selection"
            ],
            payout_snapshot_selection=conditions[
                "payout_snapshot_selection"
            ],
            source_name=source_name,
        )

    def _parse_target(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
    ) -> dict[str, Any]:
        """Parse and verify the target coupon metadata."""

        data = self._require_mapping(
            value,
            path="$.target",
        )
        self._reject_unknown_fields(
            data,
            self._target_fields,
            path="$.target",
        )
        self._require_fields(
            data,
            {
                "game_type",
            },
            path="$.target",
        )

        game_type_text = self._require_text(
            data["game_type"],
            path="$.target.game_type",
        ).lower()

        try:
            game_type = GameType(
                game_type_text
            )
        except ValueError as error:
            supported = ", ".join(
                game_type.value
                for game_type in GameType
                if game_type is not GameType.UNKNOWN
            )
            raise ValueError(
                "$.target.game_type: expected one of "
                f"{supported}."
            ) from error

        if game_type is GameType.UNKNOWN:
            raise ValueError(
                "$.target.game_type: unknown is not supported."
            )

        coupon_id = self._optional_text(
            data.get(
                "coupon_id"
            ),
            path="$.target.coupon_id",
        )
        frame_pattern = self._optional_text(
            data.get(
                "frame_pattern"
            ),
            path="$.target.frame_pattern",
        )

        if game_type is not analysis_run.game_type:
            raise ValueError(
                "$.target.game_type does not match the "
                "analyzed coupon."
            )

        if (
            coupon_id is not None
            and coupon_id != analysis_run.coupon_id
        ):
            raise ValueError(
                "$.target.coupon_id does not match the "
                "analyzed coupon."
            )

        if (
            frame_pattern is not None
            and frame_pattern
            != analysis_run.recommendation_pattern
        ):
            raise ValueError(
                "$.target.frame_pattern does not match the "
                "current turquoise frame."
            )

        return {
            "game_type": game_type,
            "coupon_id": coupon_id,
            "frame_pattern": frame_pattern,
        }

    def _parse_conditions(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
    ) -> dict[str, Any]:
        """Parse all active condition groups."""

        data = self._require_mapping(
            value,
            path="$.conditions",
        )
        self._reject_unknown_fields(
            data,
            self._condition_fields,
            path="$.conditions",
        )

        if not data:
            raise ValueError(
                "$.conditions: at least one condition group is required."
            )

        color_rule = None
        color_rule_set = None
        one_x_two_rule = None
        point_rule = None
        odds_rule = None
        payout_rule = None
        odds_selection = None
        payout_selection = None

        if "colors" in data:
            color_rules = self._parse_colors(
                data["colors"],
                analysis_run,
            )

            if len(color_rules) == 1:
                color_rule = color_rules[0]
            else:
                color_rule_set = ColorReductionRuleSet(
                    rules=color_rules
                )

        if "one_x_two" in data:
            one_x_two_rule = self._parse_one_x_two(
                data["one_x_two"],
                analysis_run,
            )

        if "points" in data:
            point_rule = self._parse_points(
                data["points"],
                analysis_run,
            )

        if "odds" in data:
            odds_rule, odds_selection = self._parse_odds(
                data["odds"],
                analysis_run,
            )

        if "payout" in data:
            payout_rule, payout_selection = self._parse_payout(
                data["payout"],
                analysis_run,
            )

        return {
            "condition_set": ReductionConditionSet(
                color_rule=color_rule,
                color_rule_set=color_rule_set,
                one_x_two_rule=one_x_two_rule,
                point_rule=point_rule,
                odds_rule=odds_rule,
                payout_rule=payout_rule,
            ),
            "odds_snapshot_selection": odds_selection,
            "payout_snapshot_selection": payout_selection,
        }

    def _parse_colors(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
    ) -> tuple[ColorReductionRule, ...]:
        """Parse one or more unique color rules."""

        items = self._require_sequence(
            value,
            path="$.conditions.colors",
        )

        if not items:
            raise ValueError(
                "$.conditions.colors: at least one color rule is required."
            )

        rules = tuple(
            self._parse_color_rule(
                item,
                analysis_run,
                path=f"$.conditions.colors[{index}]",
            )
            for index, item in enumerate(
                items
            )
        )

        colors = tuple(
            rule.color
            for rule in rules
        )

        if len(
            set(
                colors
            )
        ) != len(
            colors
        ):
            raise ValueError(
                "$.conditions.colors: each color may only "
                "appear once."
            )

        return rules

    def _parse_color_rule(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
        *,
        path: str,
    ) -> ColorReductionRule:
        """Parse one color MIN/MAX rule."""

        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._color_fields,
            path=path,
        )
        self._require_fields(
            data,
            self._color_fields,
            path=path,
        )

        color_text = self._require_text(
            data["color"],
            path=f"{path}.color",
        ).lower()

        try:
            color = ReductionColor(
                color_text
            )
        except ValueError as error:
            allowed = ", ".join(
                color.value
                for color in ReductionColor
            )
            raise ValueError(
                f"{path}.color: expected one of {allowed}."
            ) from error

        cells_data = self._require_sequence(
            data["cells"],
            path=f"{path}.cells",
        )

        if not cells_data:
            raise ValueError(
                f"{path}.cells: at least one cell is required."
            )

        cells = tuple(
            self._parse_cell(
                item,
                analysis_run,
                path=f"{path}.cells[{index}]",
            )
            for index, item in enumerate(
                cells_data
            )
        )

        return ColorReductionRule(
            color=color,
            cells=cells,
            min_hits=self._require_integer(
                data["min"],
                path=f"{path}.min",
                minimum=0,
            ),
            max_hits=self._require_integer(
                data["max"],
                path=f"{path}.max",
                minimum=0,
            ),
        )

    def _parse_cell(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
        *,
        path: str,
    ) -> ColoredOutcomeCell:
        """Parse and validate one frame-bound colored cell."""

        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._cell_fields,
            path=path,
        )
        self._require_fields(
            data,
            self._cell_fields,
            path=path,
        )

        match_number = self._require_integer(
            data["match"],
            path=f"{path}.match",
            minimum=1,
        )
        outcome = self._parse_outcome(
            data["outcome"],
            path=f"{path}.outcome",
        )

        self._validate_frame_cell(
            analysis_run,
            match_number,
            outcome,
            path=path,
        )

        return ColoredOutcomeCell(
            match_number=match_number,
            outcome=outcome,
        )

    def _parse_one_x_two(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
    ) -> OneXTwoReductionRule:
        """Parse active total outcome-count intervals."""

        path = "$.conditions.one_x_two"
        data = self._require_mapping(
            value,
            path=path,
        )
        allowed = {
            outcome.value
            for outcome in Outcome.ordered()
        }
        self._reject_unknown_fields(
            data,
            allowed,
            path=path,
        )

        if not data:
            raise ValueError(
                f"{path}: at least one outcome interval is required."
            )

        conditions: list[OutcomeCountCondition] = []

        for outcome in Outcome.ordered():
            if outcome.value not in data:
                continue

            interval_path = f"{path}.{outcome.value}"
            interval = self._parse_integer_range(
                data[outcome.value],
                path=interval_path,
            )

            if interval["max"] > analysis_run.match_count:
                raise ValueError(
                    f"{interval_path}.max exceeds the coupon's "
                    "match count."
                )

            conditions.append(
                OutcomeCountCondition(
                    outcome=outcome,
                    min_count=interval["min"],
                    max_count=interval["max"],
                )
            )

        return OneXTwoReductionRule(
            conditions=tuple(
                conditions
            )
        )

    def _parse_points(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
    ) -> PointReductionRule:
        """Parse one point-reduction rule."""

        path = "$.conditions.points"
        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._point_fields,
            path=path,
        )
        self._require_fields(
            data,
            self._point_fields,
            path=path,
        )

        assignments_data = self._require_sequence(
            data["assignments"],
            path=f"{path}.assignments",
        )

        if not assignments_data:
            raise ValueError(
                f"{path}.assignments: at least one assignment is required."
            )

        assignments = tuple(
            self._parse_assignment(
                item,
                analysis_run,
                path=f"{path}.assignments[{index}]",
            )
            for index, item in enumerate(
                assignments_data
            )
        )

        return PointReductionRule(
            assignments=assignments,
            min_points=self._require_integer(
                data["min"],
                path=f"{path}.min",
                minimum=0,
            ),
            max_points=self._require_integer(
                data["max"],
                path=f"{path}.max",
                minimum=0,
            ),
        )

    def _parse_assignment(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
        *,
        path: str,
    ) -> PointAssignment:
        """Parse and validate one frame-bound point assignment."""

        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._assignment_fields,
            path=path,
        )
        self._require_fields(
            data,
            self._assignment_fields,
            path=path,
        )

        match_number = self._require_integer(
            data["match"],
            path=f"{path}.match",
            minimum=1,
        )
        outcome = self._parse_outcome(
            data["outcome"],
            path=f"{path}.outcome",
        )

        self._validate_frame_cell(
            analysis_run,
            match_number,
            outcome,
            path=path,
        )

        return PointAssignment(
            match_number=match_number,
            outcome=outcome,
            points=self._require_integer(
                data["points"],
                path=f"{path}.points",
                minimum=1,
            ),
        )

    def _parse_odds(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
    ) -> tuple[OddsReductionRule, MarketSnapshotSelection]:
        """Parse an odds interval using imported market data."""

        path = "$.conditions.odds"
        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._market_rule_fields,
            path=path,
        )
        self._require_fields(
            data,
            self._market_rule_fields,
            path=path,
        )

        selection = self._parse_snapshot_selection(
            data["market_snapshot"],
            path=f"{path}.market_snapshot",
        )
        snapshots = self._market_snapshots(
            analysis_run,
            selection,
            path=path,
        )

        snapshot = OddsReductionSnapshot(
            captured_at=snapshots[0].captured_at,
            match_odds=tuple(
                market_snapshot.odds
                for market_snapshot in snapshots
            ),
            source=snapshots[0].source_name,
        )

        return (
            OddsReductionRule(
                snapshot=snapshot,
                min_total_odds=self._require_numeric(
                    data["min"],
                    path=f"{path}.min",
                ),
                max_total_odds=self._require_numeric(
                    data["max"],
                    path=f"{path}.max",
                ),
            ),
            selection,
        )

    def _parse_payout(
        self,
        value: object,
        analysis_run: CouponAnalysisRun,
    ) -> tuple[PayoutReductionRule, MarketSnapshotSelection]:
        """Parse a transparent payout interval using imported shares."""

        path = "$.conditions.payout"
        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._payout_fields,
            path=path,
        )
        self._require_fields(
            data,
            self._payout_fields,
            path=path,
        )

        selection = self._parse_snapshot_selection(
            data["market_snapshot"],
            path=f"{path}.market_snapshot",
        )
        snapshots = self._market_snapshots(
            analysis_run,
            selection,
            path=path,
        )

        snapshot = PayoutReductionSnapshot(
            captured_at=snapshots[0].captured_at,
            match_percentages=tuple(
                market_snapshot.public_percentages
                for market_snapshot in snapshots
            ),
            turnover=self._require_numeric(
                data["turnover"],
                path=f"{path}.turnover",
            ),
            top_prize_pool=self._require_numeric(
                data["top_prize_pool"],
                path=f"{path}.top_prize_pool",
            ),
            base_unit_stake=self._require_numeric(
                data["base_unit_stake"],
                path=f"{path}.base_unit_stake",
            ),
            source=snapshots[0].source_name,
        )

        return (
            PayoutReductionRule(
                snapshot=snapshot,
                min_estimated_payout=self._require_numeric(
                    data["min"],
                    path=f"{path}.min",
                ),
                max_estimated_payout=self._require_numeric(
                    data["max"],
                    path=f"{path}.max",
                ),
            ),
            selection,
        )

    def _market_snapshots(
        self,
        analysis_run: CouponAnalysisRun,
        selection: MarketSnapshotSelection,
        *,
        path: str,
    ) -> tuple[Any, ...]:
        """Resolve one uniform coupon-wide imported market snapshot."""

        snapshots = tuple(
            (
                match.earlier_market_snapshot
                if selection is MarketSnapshotSelection.EARLIER
                else match.later_market_snapshot
            )
            for match in analysis_run.input_document.matches
        )

        captured_times = {
            snapshot.captured_at
            for snapshot in snapshots
        }
        source_names = {
            snapshot.source_name
            for snapshot in snapshots
        }

        if len(captured_times) != 1:
            raise ValueError(
                f"{path}.market_snapshot: selected match snapshots "
                "must share one captured_at value."
            )

        if len(source_names) != 1:
            raise ValueError(
                f"{path}.market_snapshot: selected match snapshots "
                "must share one source_name."
            )

        return snapshots

    def _validate_frame_cell(
        self,
        analysis_run: CouponAnalysisRun,
        match_number: int,
        outcome: Outcome,
        *,
        path: str,
    ) -> None:
        """Ensure a marked cell belongs to the turquoise frame."""

        frame = analysis_run.reduction_frame

        if match_number > frame.match_count:
            raise ValueError(
                f"{path}.match is outside the turquoise frame."
            )

        if outcome not in frame.allowed_for_match(
            match_number
        ):
            raise ValueError(
                f"{path}: outcome {outcome.value} is outside "
                "the turquoise frame."
            )

    def _parse_integer_range(
        self,
        value: object,
        *,
        path: str,
    ) -> dict[str, int]:
        """Parse one inclusive integer MIN/MAX mapping."""

        data = self._require_mapping(
            value,
            path=path,
        )
        self._reject_unknown_fields(
            data,
            self._range_fields,
            path=path,
        )
        self._require_fields(
            data,
            self._range_fields,
            path=path,
        )

        return {
            "min": self._require_integer(
                data["min"],
                path=f"{path}.min",
                minimum=0,
            ),
            "max": self._require_integer(
                data["max"],
                path=f"{path}.max",
                minimum=0,
            ),
        }

    @staticmethod
    def _parse_snapshot_selection(
        value: object,
        *,
        path: str,
    ) -> MarketSnapshotSelection:
        """Parse earlier or later market-snapshot selection."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{path}: expected a string."
            )

        normalized = value.strip().lower()

        try:
            return MarketSnapshotSelection(
                normalized
            )
        except ValueError as error:
            raise ValueError(
                f"{path}: expected earlier or later."
            ) from error

    @staticmethod
    def _parse_outcome(
        value: object,
        *,
        path: str,
    ) -> Outcome:
        """Parse one official 1-X-2 outcome."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{path}: expected a string."
            )

        try:
            return Outcome.parse(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"{path}: expected 1, X or 2."
            ) from error

    @staticmethod
    def _require_analysis_run(
        value: object,
    ) -> None:
        """Validate the linked practical analysis run."""

        if not isinstance(
            value,
            CouponAnalysisRun,
        ):
            raise TypeError(
                "analysis_run must be a CouponAnalysisRun."
            )

    @staticmethod
    def _require_mapping(
        value: object,
        *,
        path: str,
    ) -> Mapping[str, Any]:
        """Require one JSON object mapping."""

        if not isinstance(
            value,
            Mapping,
        ):
            raise TypeError(
                f"{path}: expected an object."
            )

        for key in value:
            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    f"{path}: object field names must be strings."
                )

        return value

    @staticmethod
    def _require_sequence(
        value: object,
        *,
        path: str,
    ) -> Sequence[Any]:
        """Require one JSON array sequence."""

        if (
            isinstance(
                value,
                (str, bytes, bytearray),
            )
            or not isinstance(
                value,
                Sequence,
            )
        ):
            raise TypeError(
                f"{path}: expected an array."
            )

        return value

    @staticmethod
    def _reject_unknown_fields(
        data: Mapping[str, Any],
        allowed_fields: set[str],
        *,
        path: str,
    ) -> None:
        """Reject misspelled or unsupported JSON fields."""

        unknown = sorted(
            set(
                data
            )
            - allowed_fields
        )

        if unknown:
            raise ValueError(
                f"{path}: unknown field(s): "
                f"{', '.join(unknown)}."
            )

    @staticmethod
    def _require_fields(
        data: Mapping[str, Any],
        required_fields: set[str],
        *,
        path: str,
    ) -> None:
        """Require all mandatory JSON fields."""

        missing = sorted(
            required_fields
            - set(
                data
            )
        )

        if missing:
            raise ValueError(
                f"{path}: missing field(s): "
                f"{', '.join(missing)}."
            )

    @staticmethod
    def _require_text(
        value: object,
        *,
        path: str,
    ) -> str:
        """Require one non-empty normalized string."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{path}: expected a string."
            )

        normalized = " ".join(
            value.split()
        )

        if not normalized:
            raise ValueError(
                f"{path}: must not be empty."
            )

        return normalized

    @classmethod
    def _optional_text(
        cls,
        value: object,
        *,
        path: str,
    ) -> str | None:
        """Parse one optional normalized string."""

        if value is None:
            return None

        return cls._require_text(
            value,
            path=path,
        )

    @staticmethod
    def _require_integer(
        value: object,
        *,
        path: str,
        minimum: int,
    ) -> int:
        """Require one integer at or above a minimum."""

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            int,
        ):
            raise TypeError(
                f"{path}: expected an integer."
            )

        if value < minimum:
            raise ValueError(
                f"{path}: must be at least {minimum}."
            )

        return value

    @staticmethod
    def _require_numeric(
        value: object,
        *,
        path: str,
    ) -> Decimal:
        """Require one finite numeric value or numeric string."""

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{path}: expected a numeric value."
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
                f"{path}: expected a numeric value."
            ) from error

        if not decimal_value.is_finite():
            raise ValueError(
                f"{path}: numeric value must be finite."
            )

        return decimal_value