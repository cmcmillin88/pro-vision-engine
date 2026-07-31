"""Versioned JSON exporter for complete coupon-analysis results."""

import json
from decimal import Decimal
from typing import Any

from src.models.coupon_analysis_run import CouponAnalysisRun
from src.models.final_match_summary import FinalMatchSummary


class CouponAnalysisResultJsonExporter:
    """Exports a practical analysis run as stable JSON data."""

    schema_version = CouponAnalysisRun.CURRENT_SCHEMA_VERSION

    def to_dict(
        self,
        analysis_run: CouponAnalysisRun,
    ) -> dict[str, Any]:
        """Convert one complete run into JSON-compatible data."""

        self._validate_run(
            analysis_run
        )

        report = analysis_run.analysis_report

        return {
            "schema_version": self.schema_version,
            "analysis": {
                "analyzed_at": analysis_run.analyzed_at.isoformat(),
                "input_schema_version": (
                    analysis_run.input_document.schema_version
                ),
                "source_name": analysis_run.source_name,
            },
            "coupon": {
                "id": analysis_run.coupon_id,
                "game_type": analysis_run.game_type.value,
                "game_type_display": (
                    analysis_run.game_type.display_name
                ),
                "match_count": analysis_run.match_count,
                "recommendation_pattern": (
                    analysis_run.recommendation_pattern
                ),
                "base_row_count": analysis_run.base_row_count,
                "spike_count": report.spike_count,
                "single_count": report.single_count,
                "double_count": report.double_count,
                "triple_count": report.triple_count,
                "review_count": report.review_count,
                "total_risk_score": report.total_risk_score,
                "average_risk_score": self._decimal_text(
                    report.average_risk_score
                ),
            },
            "frame": {
                "pattern": analysis_run.recommendation_pattern,
                "match_count": analysis_run.reduction_frame.match_count,
                "row_count": analysis_run.base_system.row_count,
                "first_row": analysis_run.base_system.first_row.symbols,
                "last_row": analysis_run.base_system.last_row.symbols,
            },
            "matches": [
                self._serialize_match(
                    match_number,
                    summary,
                )
                for match_number, summary in enumerate(
                    report.match_summaries,
                    start=1,
                )
            ],
        }

    def to_json(
        self,
        analysis_run: CouponAnalysisRun,
        *,
        indent: int | None = 2,
    ) -> str:
        """Convert one complete run into UTF-8-safe JSON text."""

        if (
            indent is not None
            and (
                isinstance(indent, bool)
                or not isinstance(indent, int)
            )
        ):
            raise TypeError(
                "indent must be an integer or None."
            )

        if indent is not None and indent < 0:
            raise ValueError(
                "indent must not be negative."
            )

        return json.dumps(
            self.to_dict(
                analysis_run
            ),
            ensure_ascii=False,
            indent=indent,
        )

    @classmethod
    def _serialize_match(
        cls,
        match_number: int,
        summary: FinalMatchSummary,
    ) -> dict[str, Any]:
        """Serialize one final match summary."""

        return {
            "number": match_number,
            "reference": summary.match_reference,
            "home_team": summary.home_team_name,
            "away_team": summary.away_team_name,
            "projected_xg": {
                "home": cls._decimal_text(
                    summary.projected_home_xg
                ),
                "away": cls._decimal_text(
                    summary.projected_away_xg
                ),
            },
            "statistical_probabilities": {
                "1": cls._decimal_text(
                    summary.statistical_home_probability
                ),
                "X": cls._decimal_text(
                    summary.statistical_draw_probability
                ),
                "2": cls._decimal_text(
                    summary.statistical_away_probability
                ),
            },
            "combined_probabilities": {
                "1": cls._decimal_text(
                    summary.combined_home_probability
                ),
                "X": cls._decimal_text(
                    summary.combined_draw_probability
                ),
                "2": cls._decimal_text(
                    summary.combined_away_probability
                ),
            },
            "recommendation": {
                "primary_outcome": summary.primary_outcome.value,
                "outcomes": [
                    outcome.value
                    for outcome in summary.recommended_outcomes
                ],
                "symbols": summary.recommendation_symbols,
                "coverage": summary.coverage.value,
                "decision_type": summary.decision_type.value,
                "is_spike_candidate": summary.is_spike_candidate,
            },
            "risk": {
                "level": summary.risk_level.value,
                "score": summary.risk_score,
                "factors": [
                    factor.value
                    for factor in summary.risk_factors
                ],
            },
            "scoreline": {
                "most_likely": summary.most_likely_scoreline,
                "probability": cls._decimal_text(
                    summary.most_likely_scoreline_probability
                ),
            },
            "signals": {
                "full_consensus": summary.full_consensus,
                "conflict_level": summary.conflict_level.value,
                "requires_extended_review": (
                    summary.requires_extended_review
                ),
            },
        }

    @staticmethod
    def _decimal_text(
        value: Decimal,
    ) -> str:
        """Serialize one exact finite Decimal without float conversion."""

        if not isinstance(
            value,
            Decimal,
        ):
            raise TypeError(
                "value must be a Decimal."
            )

        if not value.is_finite():
            raise ValueError(
                "value must be finite."
            )

        return format(
            value,
            "f",
        )

    @staticmethod
    def _validate_run(
        analysis_run: object,
    ) -> None:
        """Validate the exporter input type."""

        if not isinstance(
            analysis_run,
            CouponAnalysisRun,
        ):
            raise TypeError(
                "CouponAnalysisResultJsonExporter requires "
                "a CouponAnalysisRun."
            )