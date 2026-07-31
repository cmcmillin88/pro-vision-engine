"""Analyzer comparing statistical, market and public probabilities."""

from decimal import Decimal, ROUND_HALF_UP

from src.models.market_analysis import MarketAnalysisReport
from src.models.outcome import Outcome
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
    ModelValueLevel,
    OutcomeProbabilityComparison,
    ProbabilityEvidenceDirection,
    StatisticalMarketComparisonReport,
)
from src.models.statistical_market_comparison_thresholds import (
    StatisticalMarketComparisonThresholds,
)
from src.models.statistical_match_prediction import (
    StatisticalMatchPrediction,
)


class StatisticalMarketComparisonAnalyzer:
    """Compares statistical probabilities with market evidence."""

    _quantum = Decimal("0.01")

    def __init__(
        self,
        thresholds: (
            StatisticalMarketComparisonThresholds
            | None
        ) = None,
    ) -> None:
        """Create the comparison analyzer."""

        self._thresholds = (
            thresholds
            or StatisticalMarketComparisonThresholds()
        )

    def analyze(
        self,
        statistical_prediction: StatisticalMatchPrediction,
        market_analysis: MarketAnalysisReport,
    ) -> StatisticalMarketComparisonReport:
        """Create a complete model-market-public comparison."""

        self._validate_inputs(
            statistical_prediction,
            market_analysis,
        )

        comparisons = tuple(
            self._compare_outcome(
                outcome,
                statistical_prediction,
                market_analysis,
            )
            for outcome in Outcome.ordered()
        )

        conflict_level = self._resolve_conflict_level(
            statistical_prediction,
            market_analysis,
            comparisons,
        )

        return StatisticalMarketComparisonReport(
            statistical_prediction=statistical_prediction,
            market_analysis=market_analysis,
            outcome_comparisons=comparisons,
            conflict_level=conflict_level,
        )

    def _compare_outcome(
        self,
        outcome: Outcome,
        statistical_prediction: StatisticalMatchPrediction,
        market_analysis: MarketAnalysisReport,
    ) -> OutcomeProbabilityComparison:
        """Compare one outcome across all evidence sources."""

        statistical_probability = (
            statistical_prediction
            .probability_for(
                outcome
            )
        )
        market_value = (
            market_analysis
            .latest_value_analysis
            .for_outcome(
                outcome
            )
        )
        market_probability = (
            market_value.market_probability
        )
        public_percentage = (
            market_value.public_percentage
        )
        statistical_market_gap = self._round(
            statistical_probability
            - market_probability
        )
        statistical_public_edge = self._round(
            statistical_probability
            - public_percentage
        )

        return OutcomeProbabilityComparison(
            outcome=outcome,
            statistical_probability=(
                statistical_probability
            ),
            market_probability=market_probability,
            public_percentage=public_percentage,
            statistical_market_gap=(
                statistical_market_gap
            ),
            statistical_public_edge=(
                statistical_public_edge
            ),
            evidence_direction=(
                self._resolve_direction(
                    statistical_market_gap
                )
            ),
            model_value_level=(
                self._resolve_model_value_level(
                    statistical_public_edge
                )
            ),
        )

    def _resolve_direction(
        self,
        statistical_market_gap: Decimal,
    ) -> ProbabilityEvidenceDirection:
        """Classify model-versus-market direction."""

        if (
            abs(statistical_market_gap)
            <= self._thresholds.agreement_margin
        ):
            return (
                ProbabilityEvidenceDirection
                .AGREEMENT
            )

        if statistical_market_gap > Decimal("0"):
            return (
                ProbabilityEvidenceDirection
                .STATISTICAL_HIGHER
            )

        return (
            ProbabilityEvidenceDirection
            .MARKET_HIGHER
        )

    def _resolve_model_value_level(
        self,
        statistical_public_edge: Decimal,
    ) -> ModelValueLevel:
        """Classify statistical value versus public support."""

        if (
            statistical_public_edge
            >= (
                self._thresholds
                .strong_model_value_threshold
            )
        ):
            return ModelValueLevel.STRONG_VALUE

        if (
            statistical_public_edge
            >= self._thresholds.model_value_threshold
        ):
            return ModelValueLevel.VALUE

        return ModelValueLevel.NONE

    def _resolve_conflict_level(
        self,
        statistical_prediction: StatisticalMatchPrediction,
        market_analysis: MarketAnalysisReport,
        comparisons: tuple[
            OutcomeProbabilityComparison,
            ...,
        ],
    ) -> ModelMarketConflictLevel:
        """Resolve overall statistical-versus-market conflict."""

        favorites_disagree = (
            statistical_prediction.favorite_outcome
            is not (
                market_analysis
                .market_favorite
                .outcome
            )
        )
        largest_gap = max(
            comparison.absolute_statistical_market_gap
            for comparison in comparisons
        )

        if (
            favorites_disagree
            and largest_gap
            >= self._thresholds.disagreement_strong
        ):
            return ModelMarketConflictLevel.HIGH

        if (
            favorites_disagree
            or largest_gap
            >= self._thresholds.disagreement_warning
        ):
            return ModelMarketConflictLevel.MEDIUM

        return ModelMarketConflictLevel.LOW

    @staticmethod
    def _validate_inputs(
        statistical_prediction: StatisticalMatchPrediction,
        market_analysis: MarketAnalysisReport,
    ) -> None:
        """Validate supplied analysis objects."""

        if not isinstance(
            statistical_prediction,
            StatisticalMatchPrediction,
        ):
            raise TypeError(
                "statistical_prediction must be a "
                "StatisticalMatchPrediction."
            )

        if not isinstance(
            market_analysis,
            MarketAnalysisReport,
        ):
            raise TypeError(
                "market_analysis must be "
                "a MarketAnalysisReport."
            )

    def _round(
        self,
        value: Decimal,
    ) -> Decimal:
        """Round one comparison value to two decimals."""

        return value.quantize(
            self._quantum,
            rounding=ROUND_HALF_UP,
        )