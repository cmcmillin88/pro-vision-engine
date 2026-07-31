"""Versioned JSON exporter for practical coupon-reduction results."""

import json
from decimal import Decimal
from typing import Any

from src.exporters.coupon_analysis_result_json_exporter import (
    CouponAnalysisResultJsonExporter,
)
from src.models.coupon_reduction_run import CouponReductionRun


class CouponReductionResultJsonExporter:
    """Exports one complete practical reduction run as stable JSON."""

    schema_version = CouponReductionRun.CURRENT_SCHEMA_VERSION

    def to_dict(
        self,
        reduction_run: CouponReductionRun,
    ) -> dict[str, Any]:
        """Convert a complete reduction run into JSON-compatible data."""

        self._validate_run(reduction_run)

        configuration = reduction_run.configuration
        report = reduction_run.reduction_report

        return {
            "schema_version": self.schema_version,
            "reduction": {
                "reduced_at": reduction_run.reduced_at.isoformat(),
                "configuration_schema_version": (
                    configuration.schema_version
                ),
                "configuration_source": configuration.source_name,
                "report_schema_version": report.report_version,
            },
            "coupon": {
                "id": reduction_run.coupon_id,
                "game_type": reduction_run.game_type.value,
                "game_type_display": reduction_run.game_type.display_name,
                "match_count": reduction_run.match_count,
                "frame_pattern": reduction_run.frame_pattern,
            },
            "configuration": {
                "row_price": self._decimal_text(reduction_run.row_price),
                "condition_count": reduction_run.condition_count,
                "atomic_condition_count": (
                    reduction_run.atomic_condition_count
                ),
                "condition_pattern": reduction_run.condition_pattern,
                "odds_snapshot_selection": self._selection_value(
                    configuration.odds_snapshot_selection
                ),
                "payout_snapshot_selection": self._selection_value(
                    configuration.payout_snapshot_selection
                ),
                "frozen_sources": list(configuration.frozen_sources),
            },
            "result": report.to_dict(),
            "rows": {
                "original_count": reduction_run.original_row_count,
                "approved_count": reduction_run.approved_row_count,
                "rejected_count": reduction_run.rejected_row_count,
                "approved": list(reduction_run.approved_symbols),
            },
            "cost": {
                "original": self._decimal_text(
                    reduction_run.original_cost
                ),
                "final": self._decimal_text(reduction_run.final_cost),
                "savings": self._decimal_text(reduction_run.saved_cost),
            },
            "analysis": CouponAnalysisResultJsonExporter().to_dict(
                reduction_run.analysis_run
            ),
        }

    def to_json(
        self,
        reduction_run: CouponReductionRun,
        *,
        indent: int | None = 2,
    ) -> str:
        """Convert one practical reduction run into UTF-8-safe JSON."""

        if (
            indent is not None
            and (
                isinstance(indent, bool)
                or not isinstance(indent, int)
            )
        ):
            raise TypeError("indent must be an integer or None.")

        if indent is not None and indent < 0:
            raise ValueError("indent must not be negative.")

        return json.dumps(
            self.to_dict(reduction_run),
            ensure_ascii=False,
            indent=indent,
        )

    @staticmethod
    def _selection_value(selection) -> str | None:
        """Serialize an optional market-snapshot selection."""

        if selection is None:
            return None

        return selection.value

    @staticmethod
    def _decimal_text(value: Decimal) -> str:
        """Serialize one exact finite Decimal without float conversion."""

        if not isinstance(value, Decimal):
            raise TypeError("value must be a Decimal.")

        if not value.is_finite():
            raise ValueError("value must be finite.")

        return format(value, "f")

    @staticmethod
    def _validate_run(reduction_run: object) -> None:
        """Validate the exporter input type."""

        if not isinstance(reduction_run, CouponReductionRun):
            raise TypeError(
                "CouponReductionResultJsonExporter requires "
                "a CouponReductionRun."
            )