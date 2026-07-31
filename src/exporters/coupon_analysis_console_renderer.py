"""Human-readable console renderer for practical coupon analysis."""

from src.models.coupon_analysis_run import CouponAnalysisRun
from src.models.final_match_summary import FinalDecisionType


class CouponAnalysisConsoleRenderer:
    """Renders one complete practical analysis as Swedish text."""

    _decision_names = {
        FinalDecisionType.SPIKE: "Spik",
        FinalDecisionType.SINGLE: "Singel",
        FinalDecisionType.DOUBLE: "Halvgardering",
        FinalDecisionType.TRIPLE: "Helgardering",
    }

    def render(
        self,
        analysis_run: CouponAnalysisRun,
    ) -> str:
        """Return a complete multiline console representation."""

        if not isinstance(
            analysis_run,
            CouponAnalysisRun,
        ):
            raise TypeError(
                "CouponAnalysisConsoleRenderer requires "
                "a CouponAnalysisRun."
            )

        lines = [
            analysis_run.summary_line,
            analysis_run.analysis_report.summary_line,
            f"Turkos ram: {analysis_run.recommendation_pattern}",
            "",
        ]

        lines.extend(
            self._render_match(
                match_number,
                summary,
            )
            for match_number, summary in enumerate(
                analysis_run.analysis_report.match_summaries,
                start=1,
            )
        )

        return "\n".join(
            lines
        )

    @classmethod
    def _render_match(
        cls,
        match_number: int,
        summary,
    ) -> str:
        """Render one match on one compact line."""

        decision_name = cls._decision_names[
            summary.decision_type
        ]

        return (
            f"{match_number}. "
            f"{summary.home_team_name}–{summary.away_team_name} | "
            f"Tecken {summary.recommendation_symbols} | "
            f"Beslut {decision_name} | "
            f"Risk {summary.risk_level.value} "
            f"({summary.risk_score}) | "
            f"xG {summary.projected_home_xg}–"
            f"{summary.projected_away_xg} | "
            f"Troligast {summary.most_likely_scoreline} "
            f"({summary.most_likely_scoreline_probability}%)"
        )