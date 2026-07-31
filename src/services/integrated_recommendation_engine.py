"""Final recommendation engine combining statistics and market evidence."""

from decimal import Decimal, ROUND_HALF_UP

from src.models.integrated_recommendation import (
    IntegratedMatchRecommendation,
    IntegratedOutcomeAssessment,
    IntegratedRiskFactor,
)
from src.models.integrated_recommendation_thresholds import (
    IntegratedRecommendationThresholds,
)
from src.models.market_recommendation import (
    RecommendationCoverage,
    RecommendationRiskLevel,
)
from src.models.match_analysis import MatchAnalysisReport
from src.models.outcome import Outcome
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
)


class IntegratedRecommendationEngine:
    """Creates final signs from complete match evidence."""

    _quantum = Decimal("0.01")
    _hundred = Decimal("100")

    def __init__(
        self,
        thresholds: (
            IntegratedRecommendationThresholds
            | None
        ) = None,
    ) -> None:
        """Create the final recommendation engine."""

        if (
            thresholds is not None
            and not isinstance(
                thresholds,
                IntegratedRecommendationThresholds,
            )
        ):
            raise TypeError(
                "thresholds must be an "
                "IntegratedRecommendationThresholds "
                "or None."
            )

        self._thresholds = (
            thresholds
            or IntegratedRecommendationThresholds()
        )

    def recommend(
        self,
        match_analysis: MatchAnalysisReport,
    ) -> IntegratedMatchRecommendation:
        """Create the final integrated recommendation."""

        if not isinstance(
            match_analysis,
            MatchAnalysisReport,
        ):
            raise TypeError(
                "IntegratedRecommendationEngine requires "
                "a MatchAnalysisReport."
            )

        assessments = self._build_assessments(
            match_analysis
        )

        primary_outcome = max(
            Outcome.ordered(),
            key=lambda outcome: (
                self._for_outcome(
                    assessments,
                    outcome,
                ).combined_probability
            ),
        )

        recommended_outcomes = (
            self._resolve_recommended_outcomes(
                match_analysis,
                assessments,
                primary_outcome,
            )
        )

        coverage = (
            RecommendationCoverage.from_sign_count(
                len(
                    recommended_outcomes
                )
            )
        )

        risk_factors = self._resolve_risk_factors(
            match_analysis,
            assessments,
            primary_outcome,
            coverage,
        )

        risk_score = sum(
            risk_factor.weight
            for risk_factor in risk_factors
        )

        risk_level = self._resolve_risk_level(
            risk_score
        )

        return IntegratedMatchRecommendation(
            match_analysis=match_analysis,
            outcome_assessments=assessments,
            primary_outcome=primary_outcome,
            recommended_outcomes=recommended_outcomes,
            coverage=coverage,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
        )

    def _build_assessments(
        self,
        match_analysis: MatchAnalysisReport,
    ) -> tuple[
        IntegratedOutcomeAssessment,
        ...,
    ]:
        """Build normalized combined probabilities."""

        raw_probabilities: dict[
            Outcome,
            Decimal,
        ] = {}

        for outcome in Outcome.ordered():
            statistical_probability = (
                match_analysis
                .statistical_analysis
                .probability_for(
                    outcome
                )
            )

            market_value = (
                match_analysis
                .market_analysis
                .latest_value_analysis
                .for_outcome(
                    outcome
                )
            )

            raw_probabilities[outcome] = (
                statistical_probability
                * self._thresholds.statistical_weight
                + market_value.market_probability
                * self._thresholds.market_weight
            )

        rounded_probabilities = {
            outcome: self._round(
                raw_probabilities[outcome]
            )
            for outcome in Outcome.ordered()
        }

        residual = (
            self._hundred
            - sum(
                rounded_probabilities.values(),
                Decimal("0"),
            )
        )

        adjustment_outcome = max(
            Outcome.ordered(),
            key=lambda outcome: (
                raw_probabilities[outcome]
            ),
        )

        rounded_probabilities[
            adjustment_outcome
        ] = self._round(
            rounded_probabilities[
                adjustment_outcome
            ]
            + residual
        )

        return tuple(
            self._create_assessment(
                match_analysis,
                outcome,
                rounded_probabilities[outcome],
            )
            for outcome in Outcome.ordered()
        )

    def _create_assessment(
        self,
        match_analysis: MatchAnalysisReport,
        outcome: Outcome,
        combined_probability: Decimal,
    ) -> IntegratedOutcomeAssessment:
        """Create one integrated outcome assessment."""

        statistical_probability = (
            match_analysis
            .statistical_analysis
            .probability_for(
                outcome
            )
        )

        market_value = (
            match_analysis
            .market_analysis
            .latest_value_analysis
            .for_outcome(
                outcome
            )
        )

        return IntegratedOutcomeAssessment(
            outcome=outcome,
            statistical_probability=(
                statistical_probability
            ),
            market_probability=(
                market_value.market_probability
            ),
            public_percentage=(
                market_value.public_percentage
            ),
            combined_probability=combined_probability,
            combined_public_edge=self._round(
                combined_probability
                - market_value.public_percentage
            ),
        )

    def _resolve_recommended_outcomes(
        self,
        match_analysis: MatchAnalysisReport,
        assessments: tuple[
            IntegratedOutcomeAssessment,
            ...,
        ],
        primary_outcome: Outcome,
    ) -> tuple[Outcome, ...]:
        """Resolve final single, double or triple coverage."""

        if (
            match_analysis.conflict_level
            is ModelMarketConflictLevel.HIGH
            or match_analysis
            .market_analysis
            .has_critical_alerts
        ):
            return Outcome.ordered()

        if self._qualifies_for_single(
            match_analysis,
            assessments,
            primary_outcome,
        ):
            return (
                primary_outcome,
            )

        selected_outcomes = set(
            match_analysis.recommended_outcomes
        )
        selected_outcomes.add(
            primary_outcome
        )

        for comparison in (
            match_analysis
            .evidence_comparison
            .outcome_comparisons
        ):
            if (
                comparison.outcome
                is not primary_outcome
                and comparison.statistical_public_edge
                >= (
                    self._thresholds
                    .strong_model_value_guard
                )
            ):
                selected_outcomes.add(
                    comparison.outcome
                )

        if len(selected_outcomes) == 1:
            selected_outcomes.add(
                self._best_guard_outcome(
                    match_analysis,
                    assessments,
                    primary_outcome,
                )
            )

        if len(selected_outcomes) >= 3:
            return Outcome.ordered()

        return tuple(
            outcome
            for outcome in Outcome.ordered()
            if outcome in selected_outcomes
        )

    def _qualifies_for_single(
        self,
        match_analysis: MatchAnalysisReport,
        assessments: tuple[
            IntegratedOutcomeAssessment,
            ...,
        ],
        primary_outcome: Outcome,
    ) -> bool:
        """Return whether all final single-sign conditions hold."""

        primary_probability = (
            self._for_outcome(
                assessments,
                primary_outcome,
            ).combined_probability
        )

        margin = self._combined_margin(
            assessments
        )

        return (
            match_analysis
            .market_recommendation
            .coverage
            is RecommendationCoverage.SINGLE
            and primary_probability
            >= (
                self._thresholds
                .confident_single_probability
            )
            and margin
            >= self._thresholds.confident_single_margin
            and match_analysis.full_consensus
            and match_analysis.conflict_level
            is ModelMarketConflictLevel.LOW
            and not (
                match_analysis
                .market_analysis
                .has_critical_alerts
            )
            and match_analysis.statistical_favorite
            is primary_outcome
            and match_analysis.market_favorite
            is primary_outcome
        )

    def _best_guard_outcome(
        self,
        match_analysis: MatchAnalysisReport,
        assessments: tuple[
            IntegratedOutcomeAssessment,
            ...,
        ],
        primary_outcome: Outcome,
    ) -> Outcome:
        """Return the strongest non-primary guard outcome."""

        candidates = tuple(
            outcome
            for outcome in Outcome.ordered()
            if outcome is not primary_outcome
        )

        official_index = {
            outcome: index
            for index, outcome in enumerate(
                Outcome.ordered()
            )
        }

        return max(
            candidates,
            key=lambda outcome: (
                int(
                    outcome
                    in match_analysis.recommended_outcomes
                ),
                int(
                    match_analysis
                    .evidence_comparison
                    .for_outcome(
                        outcome
                    )
                    .statistical_public_edge
                    >= self._thresholds.model_value_guard
                ),
                (
                    match_analysis
                    .evidence_comparison
                    .for_outcome(
                        outcome
                    )
                    .statistical_public_edge
                ),
                self._for_outcome(
                    assessments,
                    outcome,
                ).combined_probability,
                -official_index[outcome],
            ),
        )

    def _resolve_risk_factors(
        self,
        match_analysis: MatchAnalysisReport,
        assessments: tuple[
            IntegratedOutcomeAssessment,
            ...,
        ],
        primary_outcome: Outcome,
        coverage: RecommendationCoverage,
    ) -> tuple[IntegratedRiskFactor, ...]:
        """Resolve all final risk factors."""

        risk_factors: list[
            IntegratedRiskFactor
        ] = []

        if (
            match_analysis.statistical_favorite
            is not match_analysis.market_favorite
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .FAVORITE_DISAGREEMENT
            )

        if (
            match_analysis.conflict_level
            is ModelMarketConflictLevel.MEDIUM
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .MEDIUM_MODEL_MARKET_CONFLICT
            )
        elif (
            match_analysis.conflict_level
            is ModelMarketConflictLevel.HIGH
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .HIGH_MODEL_MARKET_CONFLICT
            )

        if (
            match_analysis
            .market_analysis
            .has_critical_alerts
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .CRITICAL_MARKET_ALERT
            )

        if (
            match_analysis.risk_level
            is RecommendationRiskLevel.EXTREME
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .EXTREME_MARKET_RISK
            )
        elif (
            match_analysis.risk_level
            is RecommendationRiskLevel.HIGH
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .HIGH_MARKET_RISK
            )

        primary_probability = (
            self._for_outcome(
                assessments,
                primary_outcome,
            ).combined_probability
        )

        if (
            primary_probability
            < self._thresholds.weak_combined_favorite
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .WEAK_COMBINED_FAVORITE
            )

        if (
            self._combined_margin(
                assessments
            )
            < self._thresholds.narrow_combined_margin
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .NARROW_COMBINED_MARGIN
            )

        strongest_value = (
            match_analysis.strongest_model_value
        )

        if (
            strongest_value.outcome
            is not primary_outcome
            and strongest_value.statistical_public_edge
            >= (
                self._thresholds
                .strong_model_value_guard
            )
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .STRONG_MODEL_VALUE_CHALLENGER
            )
        elif (
            strongest_value.outcome
            is not primary_outcome
            and strongest_value.statistical_public_edge
            >= self._thresholds.model_value_guard
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .MODEL_VALUE_CHALLENGER
            )

        if (
            coverage
            is not RecommendationCoverage.SINGLE
        ):
            risk_factors.append(
                IntegratedRiskFactor
                .GUARD_REQUIRED
            )

        return tuple(
            risk_factors
        )

    def _resolve_risk_level(
        self,
        risk_score: int,
    ) -> RecommendationRiskLevel:
        """Resolve final risk level from total score."""

        if (
            risk_score
            >= self._thresholds.extreme_risk_score
        ):
            return RecommendationRiskLevel.EXTREME

        if (
            risk_score
            >= self._thresholds.high_risk_score
        ):
            return RecommendationRiskLevel.HIGH

        if (
            risk_score
            >= self._thresholds.medium_risk_score
        ):
            return RecommendationRiskLevel.MEDIUM

        return RecommendationRiskLevel.LOW

    @staticmethod
    def _for_outcome(
        assessments: tuple[
            IntegratedOutcomeAssessment,
            ...,
        ],
        outcome: Outcome,
    ) -> IntegratedOutcomeAssessment:
        """Return one assessment from a completed tuple."""

        for assessment in assessments:
            if assessment.outcome is outcome:
                return assessment

        raise LookupError(
            f"No assessment exists for {outcome.value}."
        )

    @staticmethod
    def _combined_margin(
        assessments: tuple[
            IntegratedOutcomeAssessment,
            ...,
        ],
    ) -> Decimal:
        """Return the gap between the two highest probabilities."""

        probabilities = sorted(
            (
                assessment.combined_probability
                for assessment in assessments
            ),
            reverse=True,
        )

        return (
            probabilities[0]
            - probabilities[1]
        )

    def _round(
        self,
        value: Decimal,
    ) -> Decimal:
        """Round one value to two decimal places."""

        return value.quantize(
            self._quantum,
            rounding=ROUND_HALF_UP,
        )