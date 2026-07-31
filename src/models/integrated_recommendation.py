"""Final recommendation models combining statistics and market evidence."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.models.market_recommendation import (
    RecommendationCoverage,
    RecommendationRiskLevel,
)
from src.models.match_analysis import MatchAnalysisReport
from src.models.outcome import Outcome
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
)


class IntegratedRiskFactor(str, Enum):
    """Describes one final recommendation risk factor."""

    FAVORITE_DISAGREEMENT = "favorite_disagreement"
    MEDIUM_MODEL_MARKET_CONFLICT = (
        "medium_model_market_conflict"
    )
    HIGH_MODEL_MARKET_CONFLICT = (
        "high_model_market_conflict"
    )
    CRITICAL_MARKET_ALERT = "critical_market_alert"
    HIGH_MARKET_RISK = "high_market_risk"
    EXTREME_MARKET_RISK = "extreme_market_risk"
    WEAK_COMBINED_FAVORITE = "weak_combined_favorite"
    NARROW_COMBINED_MARGIN = "narrow_combined_margin"
    MODEL_VALUE_CHALLENGER = "model_value_challenger"
    STRONG_MODEL_VALUE_CHALLENGER = (
        "strong_model_value_challenger"
    )
    GUARD_REQUIRED = "guard_required"

    @property
    def weight(self) -> int:
        """Return the risk points contributed by the factor."""

        weights = {
            IntegratedRiskFactor.FAVORITE_DISAGREEMENT: 3,
            IntegratedRiskFactor.MEDIUM_MODEL_MARKET_CONFLICT: 2,
            IntegratedRiskFactor.HIGH_MODEL_MARKET_CONFLICT: 4,
            IntegratedRiskFactor.CRITICAL_MARKET_ALERT: 4,
            IntegratedRiskFactor.HIGH_MARKET_RISK: 3,
            IntegratedRiskFactor.EXTREME_MARKET_RISK: 5,
            IntegratedRiskFactor.WEAK_COMBINED_FAVORITE: 2,
            IntegratedRiskFactor.NARROW_COMBINED_MARGIN: 1,
            IntegratedRiskFactor.MODEL_VALUE_CHALLENGER: 2,
            IntegratedRiskFactor.STRONG_MODEL_VALUE_CHALLENGER: 3,
            IntegratedRiskFactor.GUARD_REQUIRED: 1,
        }

        return weights[self]


@dataclass(frozen=True, slots=True)
class IntegratedOutcomeAssessment:
    """Contains final evidence for one 1-X-2 outcome."""

    outcome: Outcome
    statistical_probability: Decimal
    market_probability: Decimal
    public_percentage: Decimal
    combined_probability: Decimal
    combined_public_edge: Decimal

    def __post_init__(self) -> None:
        """Validate one integrated outcome assessment."""

        if not isinstance(
            self.outcome,
            Outcome,
        ):
            raise TypeError(
                "outcome must be an Outcome."
            )

        for field_name in (
            "statistical_probability",
            "market_probability",
            "public_percentage",
            "combined_probability",
            "combined_public_edge",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                Decimal,
            ):
                raise TypeError(
                    f"{field_name} must be a Decimal."
                )

            if not value.is_finite():
                raise ValueError(
                    f"{field_name} must be finite."
                )

        for field_name in (
            "statistical_probability",
            "market_probability",
            "public_percentage",
            "combined_probability",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not (
                Decimal("0")
                <= value
                <= Decimal("100")
            ):
                raise ValueError(
                    f"{field_name} must be "
                    "between 0 and 100."
                )

        expected_edge = (
            self.combined_probability
            - self.public_percentage
        )

        if (
            self.combined_public_edge
            != expected_edge
        ):
            raise ValueError(
                "combined_public_edge must equal "
                "combined probability minus "
                "public percentage."
            )

    @property
    def has_positive_combined_value(self) -> bool:
        """Return whether combined probability exceeds public support."""

        return (
            self.combined_public_edge
            > Decimal("0")
        )


@dataclass(frozen=True, slots=True)
class IntegratedMatchRecommendation:
    """Contains the final recommendation for one match."""

    match_analysis: MatchAnalysisReport
    outcome_assessments: tuple[
        IntegratedOutcomeAssessment,
        ...,
    ]
    primary_outcome: Outcome
    recommended_outcomes: tuple[Outcome, ...]
    coverage: RecommendationCoverage
    risk_level: RecommendationRiskLevel
    risk_score: int
    risk_factors: tuple[IntegratedRiskFactor, ...]

    def __post_init__(self) -> None:
        """Validate the complete integrated recommendation."""

        if not isinstance(
            self.match_analysis,
            MatchAnalysisReport,
        ):
            raise TypeError(
                "match_analysis must be "
                "a MatchAnalysisReport."
            )

        if not isinstance(
            self.outcome_assessments,
            tuple,
        ):
            raise TypeError(
                "outcome_assessments must be a tuple."
            )

        assessment_order = tuple(
            assessment.outcome
            for assessment in self.outcome_assessments
        )

        if assessment_order != Outcome.ordered():
            raise ValueError(
                "Outcome assessments must follow "
                "official 1-X-2 order."
            )

        for assessment in self.outcome_assessments:
            if not isinstance(
                assessment,
                IntegratedOutcomeAssessment,
            ):
                raise TypeError(
                    "outcome_assessments may only contain "
                    "IntegratedOutcomeAssessment objects."
                )

            statistical_probability = (
                self.match_analysis
                .statistical_analysis
                .probability_for(
                    assessment.outcome
                )
            )

            market_value = (
                self.match_analysis
                .market_analysis
                .latest_value_analysis
                .for_outcome(
                    assessment.outcome
                )
            )

            if (
                assessment.statistical_probability
                != statistical_probability
            ):
                raise ValueError(
                    "Assessment statistical probability "
                    "does not match the match analysis."
                )

            if (
                assessment.market_probability
                != market_value.market_probability
                or assessment.public_percentage
                != market_value.public_percentage
            ):
                raise ValueError(
                    "Assessment market evidence does not "
                    "match the match analysis."
                )

        combined_total = sum(
            (
                assessment.combined_probability
                for assessment in self.outcome_assessments
            ),
            Decimal("0"),
        )

        if combined_total != Decimal("100.00"):
            raise ValueError(
                "Combined probabilities must total "
                "exactly 100.00."
            )

        if not isinstance(
            self.primary_outcome,
            Outcome,
        ):
            raise TypeError(
                "primary_outcome must be an Outcome."
            )

        expected_primary = max(
            Outcome.ordered(),
            key=lambda outcome: (
                self.for_outcome(
                    outcome
                ).combined_probability
            ),
        )

        if self.primary_outcome is not expected_primary:
            raise ValueError(
                "primary_outcome must be the outcome "
                "with the highest combined probability."
            )

        if not isinstance(
            self.recommended_outcomes,
            tuple,
        ):
            raise TypeError(
                "recommended_outcomes must be a tuple."
            )

        if not self.recommended_outcomes:
            raise ValueError(
                "At least one outcome must be recommended."
            )

        if (
            len(
                set(
                    self.recommended_outcomes
                )
            )
            != len(
                self.recommended_outcomes
            )
        ):
            raise ValueError(
                "Recommended outcomes must not "
                "contain duplicates."
            )

        expected_order = tuple(
            outcome
            for outcome in Outcome.ordered()
            if outcome in self.recommended_outcomes
        )

        if (
            self.recommended_outcomes
            != expected_order
        ):
            raise ValueError(
                "Recommended outcomes must follow "
                "official 1-X-2 order."
            )

        if (
            self.primary_outcome
            not in self.recommended_outcomes
        ):
            raise ValueError(
                "Primary outcome must be included "
                "in recommended outcomes."
            )

        if not isinstance(
            self.coverage,
            RecommendationCoverage,
        ):
            raise TypeError(
                "coverage must be a "
                "RecommendationCoverage."
            )

        expected_coverage = (
            RecommendationCoverage.from_sign_count(
                len(
                    self.recommended_outcomes
                )
            )
        )

        if self.coverage is not expected_coverage:
            raise ValueError(
                "coverage does not match the number "
                "of recommended outcomes."
            )

        if not isinstance(
            self.risk_level,
            RecommendationRiskLevel,
        ):
            raise TypeError(
                "risk_level must be a "
                "RecommendationRiskLevel."
            )

        if isinstance(
            self.risk_score,
            bool,
        ) or not isinstance(
            self.risk_score,
            int,
        ):
            raise TypeError(
                "risk_score must be an integer."
            )

        if self.risk_score < 0:
            raise ValueError(
                "risk_score must not be negative."
            )

        if not isinstance(
            self.risk_factors,
            tuple,
        ):
            raise TypeError(
                "risk_factors must be a tuple."
            )

        for risk_factor in self.risk_factors:
            if not isinstance(
                risk_factor,
                IntegratedRiskFactor,
            ):
                raise TypeError(
                    "risk_factors may only contain "
                    "IntegratedRiskFactor values."
                )

        if (
            len(
                set(
                    self.risk_factors
                )
            )
            != len(
                self.risk_factors
            )
        ):
            raise ValueError(
                "Risk factors must not contain duplicates."
            )

        expected_risk_score = sum(
            risk_factor.weight
            for risk_factor in self.risk_factors
        )

        if self.risk_score != expected_risk_score:
            raise ValueError(
                "risk_score must equal the total "
                "risk-factor weight."
            )

    def for_outcome(
        self,
        outcome: Outcome,
    ) -> IntegratedOutcomeAssessment:
        """Return the assessment for one outcome."""

        resolved_outcome = Outcome.parse(
            outcome
        )

        for assessment in self.outcome_assessments:
            if assessment.outcome is resolved_outcome:
                return assessment

        raise LookupError(
            f"No integrated assessment exists for "
            f"{resolved_outcome.value}."
        )

    @property
    def combined_confidence_margin(self) -> Decimal:
        """Return the gap between the top two combined outcomes."""

        probabilities = sorted(
            (
                assessment.combined_probability
                for assessment in self.outcome_assessments
            ),
            reverse=True,
        )

        return (
            probabilities[0]
            - probabilities[1]
        )

    @property
    def recommendation_symbols(self) -> str:
        """Return compact recommended 1-X-2 signs."""

        return "".join(
            outcome.value
            for outcome in self.recommended_outcomes
        )

    @property
    def secondary_outcomes(
        self,
    ) -> tuple[Outcome, ...]:
        """Return recommended outcomes except the primary."""

        return tuple(
            outcome
            for outcome in self.recommended_outcomes
            if outcome is not self.primary_outcome
        )

    @property
    def requires_guard(self) -> bool:
        """Return whether more than one sign is required."""

        return (
            self.coverage
            is not RecommendationCoverage.SINGLE
        )

    @property
    def is_full_cover(self) -> bool:
        """Return whether all three signs are recommended."""

        return (
            self.coverage
            is RecommendationCoverage.TRIPLE
        )

    @property
    def is_spike_candidate(self) -> bool:
        """Return whether the final evidence supports a spike."""

        return (
            self.coverage
            is RecommendationCoverage.SINGLE
            and self.risk_level
            in {
                RecommendationRiskLevel.LOW,
                RecommendationRiskLevel.MEDIUM,
            }
            and self.match_analysis.full_consensus
            and self.match_analysis.conflict_level
            is ModelMarketConflictLevel.LOW
        )

    def has_risk_factor(
        self,
        risk_factor: IntegratedRiskFactor,
    ) -> bool:
        """Return whether one risk factor is present."""

        if not isinstance(
            risk_factor,
            IntegratedRiskFactor,
        ):
            raise TypeError(
                "risk_factor must be an "
                "IntegratedRiskFactor."
            )

        return risk_factor in self.risk_factors