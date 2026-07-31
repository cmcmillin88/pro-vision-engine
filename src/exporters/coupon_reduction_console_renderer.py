"""Swedish console renderer for practical coupon-reduction results."""

from src.models.coupon_reduction_run import CouponReductionRun


class CouponReductionConsoleRenderer:
    """Renders analysis, conditions, impact and surviving rows."""

    def __init__(self, *, max_rows: int = 20) -> None:
        """Create a renderer with a positive row-preview limit."""

        if isinstance(max_rows, bool) or not isinstance(max_rows, int):
            raise TypeError("max_rows must be an integer.")

        if max_rows <= 0:
            raise ValueError("max_rows must be greater than zero.")

        self._max_rows = max_rows

    @property
    def max_rows(self) -> int:
        """Return the configured preview limit."""

        return self._max_rows

    def render(self, reduction_run: CouponReductionRun) -> str:
        """Return a complete multiline Swedish console report."""

        if not isinstance(reduction_run, CouponReductionRun):
            raise TypeError(
                "CouponReductionConsoleRenderer requires "
                "a CouponReductionRun."
            )

        report = reduction_run.reduction_report

        lines = [
            reduction_run.summary_line,
            reduction_run.analysis_run.analysis_report.summary_line,
            reduction_run.configuration.summary_line,
            report.summary_line,
            report.analysis_line,
            f"Turkos ram: {reduction_run.frame_pattern}",
            f"Villkor: {reduction_run.condition_pattern}",
            (
                "Kostnad: "
                f"{reduction_run.original_cost} kr → "
                f"{reduction_run.final_cost} kr | "
                f"Besparing {reduction_run.saved_cost} kr"
            ),
            "",
            "Villkorseffekt:",
        ]

        lines.extend(
            f"- {impact.summary_line}"
            for impact in report.condition_impacts
        )

        lines.extend(
            [
                "",
                "Bortfallsmönster:",
            ]
        )

        if report.rejection_patterns:
            lines.extend(
                f"- {pattern.summary_line}"
                for pattern in report.rejection_patterns
            )
        else:
            lines.append("- Inga borttagna rader")

        lines.extend(
            [
                "",
                f"Kvarvarande rader ({reduction_run.approved_row_count}):",
            ]
        )

        if reduction_run.is_empty:
            lines.append("- Inga rader överlevde reduceringen")
            return "\n".join(lines)

        visible_rows = reduction_run.approved_symbols[: self.max_rows]

        lines.extend(
            f"{index}. {symbols}"
            for index, symbols in enumerate(visible_rows, start=1)
        )

        omitted_count = reduction_run.approved_row_count - len(visible_rows)

        if omitted_count > 0:
            lines.append(f"... ytterligare {omitted_count} rader")

        return "\n".join(lines)