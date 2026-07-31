"""Complete statistical and market analysis for one match."""

from dataclasses import dataclass
from decimal import Decimal

from src.models.market_analysis import MarketAnalysisReport
from src.models.market_recommendation import (
    MatchRecommendation,
    RecommendationRiskLevel,
)
from src.models.match_analysis_input import (
    MatchAnalysisInput,
)
from src.models.outcome import Outcome
from src.models.statistical_analysis import (
    StatisticalAnalysisReport,
)
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
    OutcomeProbabilityComparison,
    StatisticalMarketComparisonReport,
)
from src.models.statistical_match_prediction import (
    ScorelineProbability,
)


@dataclass(frozen=True, slots=True)
class MatchAnalysisReport:
    """Contains the complete analysis for one football match."""

    analysis_input: MatchAnalysisInput
    statistical_analysis: StatisticalAnalysisReport
    market_analysis: MarketAnalysisReport
    evidence_comparison: StatisticalMarketComparisonReport

    def __post_init__(self) -> None:
        """Validate all relationships in the analysis chain."""

        if not isinstance(
            self.analysis_input,
            MatchAnalysisInput,
        ):
            raise TypeError(
                "analysis_input must be "
                "a MatchAnalysisInput."
            )

        if not isinstance(
            self.statistical_analysis,
            StatisticalAnalysisReport,
        ):
            raise TypeError(
                "statistical_analysis must be a "
                "StatisticalAnalysisReport."
            )

        if (
            self.statistical_analysis
            .home_team_name.casefold()
            != self.analysis_input
            .home_team_name.casefold()
            or self.statistical_analysis
            .away_team_name.casefold()
            != self.analysis_input
            .away_team_name.casefold()
        ):
            raise ValueError(
                "Statistical analysis team names must "
                "match the analysis input."
            )

        if not isinstance(
            self.market_analysis,
            MarketAnalysisReport,
        ):
            raise TypeError(
                "market_analysis must be "
                "a MarketAnalysisReport."
            )

        if (
            self.market_analysis.earlier_snapshot
            != (
                self.analysis_input
                .earlier_market_snapshot
            )
            or self.market_analysis.latest_snapshot
            != (
                self.analysis_input
                .later_market_snapshot
            )
        ):
            raise ValueError(
                "Market analysis snapshots must match "
                "the analysis input."
            )

        if not isinstance(
            self.evidence_comparison,
            StatisticalMarketComparisonReport,
        ):
            raise TypeError(
                "evidence_comparison must be a "
                "StatisticalMarketComparisonReport."
            )

        if (
            self.evidence_comparison
            .statistical_prediction
            != self.statistical_analysis.prediction
        ):
            raise ValueError(
                "Evidence comparison must use the supplied "
                "statistical prediction."
            )

        if (
            self.evidence_comparison.market_analysis
            != self.market_analysis
        ):
            raise ValueError(
                "Evidence comparison must use the supplied "
                "market analysis."
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
    def projected_scoreline(self) -> str:
        """Return the projected expected-goals score."""

        return (
            self.statistical_analysis
            .projected_scoreline
        )

    @property
    def most_likely_scoreline(
        self,
    ) -> ScorelineProbability:
        """Return the most probable exact scoreline."""

        return (
            self.statistical_analysis
            .most_likely_scoreline
        )

    @property
    def statistical_favorite(self) -> Outcome:
        """Return the statistical favorite."""

        return (
            self.evidence_comparison
            .statistical_favorite
        )

    @property
    def market_favorite(self) -> Outcome:
        """Return the odds-market favorite."""

        return (
            self.evidence_comparison
            .market_favorite
        )

    @property
    def public_favorite(self) -> Outcome:
        """Return the public favorite."""

        return (
            self.evidence_comparison
            .public_favorite
        )

    @property
    def statistical_confidence_margin(
        self,
    ) -> Decimal:
        """Return the statistical favorite margin."""

        return (
            self.statistical_analysis
            .confidence_margin
        )

    @property
    def full_consensus(self) -> bool:
        """Return whether statistics, market and public agree."""

        return (
            self.evidence_comparison
            .full_consensus
        )

    @property
    def statistical_market_agree(self) -> bool:
        """Return whether statistical and market favorites agree."""

        return (
            self.evidence_comparison
            .statistical_market_agree
        )

    @property
    def conflict_level(
        self,
    ) -> ModelMarketConflictLevel:
        """Return the statistical-market conflict level."""

        return (
            self.evidence_comparison
            .conflict_level
        )

    @property
    def strongest_model_value(
        self,
    ) -> OutcomeProbabilityComparison:
        """Return the strongest statistical-public edge."""

        return (
            self.evidence_comparison
            .strongest_model_value
        )

    @property
    def model_value_outcomes(
        self,
    ) -> tuple[OutcomeProbabilityComparison, ...]:
        """Return all statistical model-value outcomes."""

        return (
            self.evidence_comparison
            .model_value_outcomes
        )

    @property
    def has_model_value(self) -> bool:
        """Return whether any outcome has model value."""

        return bool(
            self.model_value_outcomes
        )

    @property
    def has_strong_model_value(self) -> bool:
        """Return whether any strong model value exists."""

        return bool(
            self.evidence_comparison
            .strong_model_value_outcomes
        )

    @property
    def market_recommendation(
        self,
    ) -> MatchRecommendation:
        """Return the market-based recommendation."""

        return self.market_analysis.recommendation

    @property
    def primary_outcome(self) -> Outcome:
        """Return the market recommendation's primary outcome."""

        return self.market_analysis.primary_outcome

    @property
    def recommended_outcomes(
        self,
    ) -> tuple[Outcome, ...]:
        """Return all market-recommended outcomes."""

        return (
            self.market_analysis
            .recommended_outcomes
        )

    @property
    def recommendation_symbols(self) -> str:
        """Return compact market-recommended signs."""

        return (
            self.market_analysis
            .recommendation_symbols
        )

    @property
    def risk_level(
        self,
    ) -> RecommendationRiskLevel:
        """Return the market recommendation risk level."""

        return self.market_analysis.risk_level

    @property
    def risk_score(self) -> int:
        """Return the market recommendation risk score."""

        return self.market_analysis.risk_score

    @property
    def market_spike_candidate(self) -> bool:
        """Return whether the market analysis supports a spike."""

        return (
            self.market_analysis
            .is_spike_candidate
        )

    @property
    def is_joint_spike_candidate(self) -> bool:
        """Return whether market and statistics jointly support a spike."""

        return (
            self.market_spike_candidate
            and self.full_consensus
            and self.statistical_favorite
            is self.primary_outcome
            and self.conflict_level
            is ModelMarketConflictLevel.LOW
        )

    @property
    def requires_extended_review(self) -> bool:
        """Return whether conflicting evidence needs more analysis."""

        return (
            self.conflict_level
            is not ModelMarketConflictLevel.LOW
            or self.market_analysis.has_critical_alerts
        )