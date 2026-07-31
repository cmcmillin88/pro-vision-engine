"""Final end-to-end analysis report for one football match."""

from dataclasses import dataclass
from decimal import Decimal

from src.models.final_match_summary import (
    FinalDecisionType,
    FinalMatchSummary,
)
from src.models.integrated_recommendation import (
    IntegratedMatchRecommendation,
    IntegratedRiskFactor,
)
from src.models.market_recommendation import (
    RecommendationCoverage,
    RecommendationRiskLevel,
)
from src.models.match_analysis import MatchAnalysisReport
from src.models.match_analysis_input import MatchAnalysisInput
from src.models.outcome import Outcome
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
)


@dataclass(frozen=True, slots=True)
class FinalMatchAnalysisReport:
    """Contains every completed analysis stage for one match."""

    analysis_input: MatchAnalysisInput
    match_analysis: MatchAnalysisReport
    recommendation: IntegratedMatchRecommendation

    def __post_init__(self) -> None:
        """Validate the complete final-analysis chain."""

        if not isinstance(
            self.analysis_input,
            MatchAnalysisInput,
        ):
            raise TypeError(
                "analysis_input must be "
                "a MatchAnalysisInput."
            )

        if not isinstance(
            self.match_analysis,
            MatchAnalysisReport,
        ):
            raise TypeError(
                "match_analysis must be "
                "a MatchAnalysisReport."
            )

        if (
            self.match_analysis.analysis_input
            != self.analysis_input
        ):
            raise ValueError(
                "match_analysis must use the same "
                "MatchAnalysisInput."
            )

        if not isinstance(
            self.recommendation,
            IntegratedMatchRecommendation,
        ):
            raise TypeError(
                "recommendation must be an "
                "IntegratedMatchRecommendation."
            )

        if (
            self.recommendation.match_analysis
            != self.match_analysis
        ):
            raise ValueError(
                "recommendation must use the supplied "
                "MatchAnalysisReport."
            )

    @property
    def match_reference(self) -> str | None:
        """Return the optional match reference."""

        return self.analysis_input.match_reference

    @property
    def home_team_name(self) -> str:
        """Return the home-team name."""

        return self.analysis_input.home_team_name

    @property
    def away_team_name(self) -> str:
        """Return the away-team name."""

        return self.analysis_input.away_team_name

    @property
    def projected_home_xg(self) -> Decimal:
        """Return projected home expected goals."""

        return (
            self.match_analysis
            .statistical_analysis
            .projected_home_xg
        )

    @property
    def projected_away_xg(self) -> Decimal:
        """Return projected away expected goals."""

        return (
            self.match_analysis
            .statistical_analysis
            .projected_away_xg
        )

    @property
    def projected_scoreline(self) -> str:
        """Return the projected xG scoreline."""

        return self.match_analysis.projected_scoreline

    @property
    def primary_outcome(self) -> Outcome:
        """Return the final primary outcome."""

        return self.recommendation.primary_outcome

    @property
    def recommended_outcomes(
        self,
    ) -> tuple[Outcome, ...]:
        """Return final recommended outcomes."""

        return self.recommendation.recommended_outcomes

    @property
    def recommendation_symbols(self) -> str:
        """Return compact final signs."""

        return self.recommendation.recommendation_symbols

    @property
    def coverage(self) -> RecommendationCoverage:
        """Return final recommendation coverage."""

        return self.recommendation.coverage

    @property
    def risk_level(self) -> RecommendationRiskLevel:
        """Return final integrated risk level."""

        return self.recommendation.risk_level

    @property
    def risk_score(self) -> int:
        """Return final integrated risk score."""

        return self.recommendation.risk_score

    @property
    def risk_factors(
        self,
    ) -> tuple[IntegratedRiskFactor, ...]:
        """Return final integrated risk factors."""

        return self.recommendation.risk_factors

    @property
    def full_consensus(self) -> bool:
        """Return whether statistics, market and public agree."""

        return self.match_analysis.full_consensus

    @property
    def conflict_level(
        self,
    ) -> ModelMarketConflictLevel:
        """Return model-market conflict level."""

        return self.match_analysis.conflict_level

    @property
    def is_spike_candidate(self) -> bool:
        """Return whether final evidence supports a spike."""

        return self.recommendation.is_spike_candidate

    @property
    def requires_guard(self) -> bool:
        """Return whether multiple signs are required."""

        return self.recommendation.requires_guard

    @property
    def requires_extended_review(self) -> bool:
        """Return whether the final result needs extra review."""

        return (
            self.match_analysis.requires_extended_review
            or self.risk_level
            in {
                RecommendationRiskLevel.HIGH,
                RecommendationRiskLevel.EXTREME,
            }
            or self.coverage
            is RecommendationCoverage.TRIPLE
        )

    @property
    def final_decision_type(self) -> FinalDecisionType:
        """Return the final decision classification."""

        return FinalDecisionType.resolve(
            self.coverage,
            is_spike_candidate=self.is_spike_candidate,
        )

    def statistical_probability_for(
        self,
        outcome: Outcome,
    ) -> Decimal:
        """Return statistical probability for one outcome."""

        return (
            self.match_analysis
            .statistical_analysis
            .probability_for(
                outcome
            )
        )

    def combined_probability_for(
        self,
        outcome: Outcome,
    ) -> Decimal:
        """Return combined probability for one outcome."""

        return (
            self.recommendation
            .for_outcome(
                outcome
            )
            .combined_probability
        )

    def to_summary(self) -> FinalMatchSummary:
        """Create an export-ready flat summary."""

        most_likely_scoreline = (
            self.match_analysis
            .most_likely_scoreline
        )

        return FinalMatchSummary(
            match_reference=self.match_reference,
            home_team_name=self.home_team_name,
            away_team_name=self.away_team_name,
            projected_home_xg=self.projected_home_xg,
            projected_away_xg=self.projected_away_xg,
            statistical_home_probability=(
                self.statistical_probability_for(
                    Outcome.HOME
                )
            ),
            statistical_draw_probability=(
                self.statistical_probability_for(
                    Outcome.DRAW
                )
            ),
            statistical_away_probability=(
                self.statistical_probability_for(
                    Outcome.AWAY
                )
            ),
            combined_home_probability=(
                self.combined_probability_for(
                    Outcome.HOME
                )
            ),
            combined_draw_probability=(
                self.combined_probability_for(
                    Outcome.DRAW
                )
            ),
            combined_away_probability=(
                self.combined_probability_for(
                    Outcome.AWAY
                )
            ),
            primary_outcome=self.primary_outcome,
            recommended_outcomes=(
                self.recommended_outcomes
            ),
            coverage=self.coverage,
            risk_level=self.risk_level,
            risk_score=self.risk_score,
            risk_factors=self.risk_factors,
            most_likely_scoreline=(
                most_likely_scoreline.scoreline
            ),
            most_likely_scoreline_probability=(
                most_likely_scoreline.probability
            ),
            full_consensus=self.full_consensus,
            conflict_level=self.conflict_level,
            is_spike_candidate=(
                self.is_spike_candidate
            ),
            requires_extended_review=(
                self.requires_extended_review
            ),
            decision_type=self.final_decision_type,
        )

    @property
    def summary_line(self) -> str:
        """Return a compact human-readable final summary."""

        return (
            f"{self.home_team_name}-"
            f"{self.away_team_name} | "
            f"xG {self.projected_scoreline} | "
            f"1 "
            f"{self.combined_probability_for(Outcome.HOME)}% | "
            f"X "
            f"{self.combined_probability_for(Outcome.DRAW)}% | "
            f"2 "
            f"{self.combined_probability_for(Outcome.AWAY)}% | "
            f"Tecken {self.recommendation_symbols} | "
            f"Beslut {self.final_decision_type.value} | "
            f"Risk {self.risk_level.value} "
            f"({self.risk_score}) | "
            f"Granskning "
            f"{self.requires_extended_review}"
        )