"""Complete final analysis report for one football coupon."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from math import prod

from src.models.coupon_analysis_input import (
    CouponAnalysisInput,
)
from src.models.final_match_analysis import (
    FinalMatchAnalysisReport,
)
from src.models.final_match_summary import (
    FinalDecisionType,
    FinalMatchSummary,
)
from src.models.game_type import GameType


@dataclass(frozen=True, slots=True)
class FinalCouponAnalysisReport:
    """Contains final analysis for every match in a coupon."""

    analysis_input: CouponAnalysisInput
    match_reports: tuple[
        FinalMatchAnalysisReport,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete coupon-analysis chain."""

        if not isinstance(
            self.analysis_input,
            CouponAnalysisInput,
        ):
            raise TypeError(
                "analysis_input must be a "
                "CouponAnalysisInput."
            )

        if not isinstance(
            self.match_reports,
            tuple,
        ):
            raise TypeError(
                "match_reports must be a tuple."
            )

        if (
            len(self.match_reports)
            != self.analysis_input.match_count
        ):
            raise ValueError(
                "match_reports must contain one report "
                "for every coupon match."
            )

        for index, match_report in enumerate(
            self.match_reports
        ):
            if not isinstance(
                match_report,
                FinalMatchAnalysisReport,
            ):
                raise TypeError(
                    "match_reports may only contain "
                    "FinalMatchAnalysisReport objects."
                )

            expected_match_input = (
                self.analysis_input.matches[index]
            )

            if (
                match_report.analysis_input
                != expected_match_input
            ):
                raise ValueError(
                    "Each match report must use the same "
                    "MatchAnalysisInput and coupon order."
                )

    @property
    def game_type(self) -> GameType:
        """Return the coupon game type."""

        return self.analysis_input.game_type

    @property
    def coupon_id(self) -> str | None:
        """Return the optional coupon identifier."""

        return self.analysis_input.coupon_id

    @property
    def match_count(self) -> int:
        """Return the number of analyzed matches."""

        return len(
            self.match_reports
        )

    @property
    def match_summaries(
        self,
    ) -> tuple[FinalMatchSummary, ...]:
        """Return flat summaries for every match."""

        return tuple(
            match_report.to_summary()
            for match_report in self.match_reports
        )

    @property
    def spike_candidates(
        self,
    ) -> tuple[FinalMatchAnalysisReport, ...]:
        """Return matches classified as final spikes."""

        return tuple(
            match_report
            for match_report in self.match_reports
            if (
                match_report.final_decision_type
                is FinalDecisionType.SPIKE
            )
        )

    @property
    def single_recommendations(
        self,
    ) -> tuple[FinalMatchAnalysisReport, ...]:
        """Return non-spike single-sign matches."""

        return tuple(
            match_report
            for match_report in self.match_reports
            if (
                match_report.final_decision_type
                is FinalDecisionType.SINGLE
            )
        )

    @property
    def double_recommendations(
        self,
    ) -> tuple[FinalMatchAnalysisReport, ...]:
        """Return half-guarded matches."""

        return tuple(
            match_report
            for match_report in self.match_reports
            if (
                match_report.final_decision_type
                is FinalDecisionType.DOUBLE
            )
        )

    @property
    def triple_recommendations(
        self,
    ) -> tuple[FinalMatchAnalysisReport, ...]:
        """Return fully guarded matches."""

        return tuple(
            match_report
            for match_report in self.match_reports
            if (
                match_report.final_decision_type
                is FinalDecisionType.TRIPLE
            )
        )

    @property
    def review_matches(
        self,
    ) -> tuple[FinalMatchAnalysisReport, ...]:
        """Return matches requiring extended review."""

        return tuple(
            match_report
            for match_report in self.match_reports
            if match_report.requires_extended_review
        )

    @property
    def spike_count(self) -> int:
        """Return final spike count."""

        return len(
            self.spike_candidates
        )

    @property
    def single_count(self) -> int:
        """Return non-spike single count."""

        return len(
            self.single_recommendations
        )

    @property
    def double_count(self) -> int:
        """Return half-guard count."""

        return len(
            self.double_recommendations
        )

    @property
    def triple_count(self) -> int:
        """Return full-guard count."""

        return len(
            self.triple_recommendations
        )

    @property
    def review_count(self) -> int:
        """Return extended-review match count."""

        return len(
            self.review_matches
        )

    @property
    def base_row_count(self) -> int:
        """Return the mathematical row count before reduction."""

        return prod(
            match_report.coverage.sign_count
            for match_report in self.match_reports
        )

    @property
    def total_risk_score(self) -> int:
        """Return total integrated risk across the coupon."""

        return sum(
            match_report.risk_score
            for match_report in self.match_reports
        )

    @property
    def average_risk_score(self) -> Decimal:
        """Return average integrated risk per match."""

        return (
            Decimal(
                self.total_risk_score
            )
            / Decimal(
                self.match_count
            )
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def recommendation_pattern(self) -> str:
        """Return the ordered recommendation pattern."""

        return "|".join(
            match_report.recommendation_symbols
            for match_report in self.match_reports
        )

    @property
    def has_full_cover(self) -> bool:
        """Return whether the coupon contains a full guard."""

        return self.triple_count > 0

    @property
    def summary_line(self) -> str:
        """Return a compact coupon-analysis summary."""

        return (
            f"{self.game_type.display_name} | "
            f"Matcher {self.match_count} | "
            f"Spikar {self.spike_count} | "
            f"Singlar {self.single_count} | "
            f"Halvgarderingar {self.double_count} | "
            f"Helgarderingar {self.triple_count} | "
            f"Rader {self.base_row_count} | "
            f"Granskning {self.review_count} | "
            f"Snittrisk {self.average_risk_score}"
        )