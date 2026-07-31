"""Comparison models for statistical, market and public probabilities."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.models.market_analysis import MarketAnalysisReport
from src.models.outcome import Outcome
from src.models.statistical_match_prediction import (
    StatisticalMatchPrediction,
)


class ProbabilityEvidenceDirection(str, Enum):
    """Describes the relationship between model and market."""

    AGREEMENT = "agreement"
    STATISTICAL_HIGHER = "statistical_higher"
    MARKET_HIGHER = "market_higher"

    @property
    def display_name(self) -> str:
        """Return a human-readable direction."""

        names = {
            ProbabilityEvidenceDirection.AGREEMENT: (
                "Model and market agreement"
            ),
            ProbabilityEvidenceDirection.STATISTICAL_HIGHER: (
                "Statistical model higher"
            ),
            ProbabilityEvidenceDirection.MARKET_HIGHER: (
                "Odds market higher"
            ),
        }

        return names[self]


class ModelValueLevel(str, Enum):
    """Describes statistical probability versus public support."""

    NONE = "none"
    VALUE = "value"
    STRONG_VALUE = "strong_value"

    @property
    def rank(self) -> int:
        """Return a sortable model-value rank."""

        ranks = {
            ModelValueLevel.NONE: 0,
            ModelValueLevel.VALUE: 1,
            ModelValueLevel.STRONG_VALUE: 2,
        }

        return ranks[self]


class ModelMarketConflictLevel(str, Enum):
    """Describes disagreement between model and odds market."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        """Return a sortable conflict rank."""

        ranks = {
            ModelMarketConflictLevel.LOW: 1,
            ModelMarketConflictLevel.MEDIUM: 2,
            ModelMarketConflictLevel.HIGH: 3,
        }

        return ranks[self]


@dataclass(frozen=True, slots=True)
class OutcomeProbabilityComparison:
    """Compares one outcome across model, market and public."""

    outcome: Outcome
    statistical_probability: Decimal
    market_probability: Decimal
    public_percentage: Decimal
    statistical_market_gap: Decimal
    statistical_public_edge: Decimal
    evidence_direction: ProbabilityEvidenceDirection
    model_value_level: ModelValueLevel

    def __post_init__(self) -> None:
        """Validate one outcome comparison."""

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
            "statistical_market_gap",
            "statistical_public_edge",
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

        expected_market_gap = (
            self.statistical_probability
            - self.market_probability
        )

        if (
            self.statistical_market_gap
            != expected_market_gap
        ):
            raise ValueError(
                "statistical_market_gap must equal "
                "statistical probability minus "
                "market probability."
            )

        expected_public_edge = (
            self.statistical_probability
            - self.public_percentage
        )

        if (
            self.statistical_public_edge
            != expected_public_edge
        ):
            raise ValueError(
                "statistical_public_edge must equal "
                "statistical probability minus "
                "public percentage."
            )

        if not isinstance(
            self.evidence_direction,
            ProbabilityEvidenceDirection,
        ):
            raise TypeError(
                "evidence_direction must be a "
                "ProbabilityEvidenceDirection."
            )

        if (
            self.evidence_direction
            is ProbabilityEvidenceDirection
            .STATISTICAL_HIGHER
            and self.statistical_market_gap
            <= Decimal("0")
        ):
            raise ValueError(
                "Statistical-higher direction requires "
                "a positive statistical-market gap."
            )

        if (
            self.evidence_direction
            is ProbabilityEvidenceDirection
            .MARKET_HIGHER
            and self.statistical_market_gap
            >= Decimal("0")
        ):
            raise ValueError(
                "Market-higher direction requires "
                "a negative statistical-market gap."
            )

        if not isinstance(
            self.model_value_level,
            ModelValueLevel,
        ):
            raise TypeError(
                "model_value_level must be "
                "a ModelValueLevel."
            )

        if (
            self.model_value_level
            is not ModelValueLevel.NONE
            and self.statistical_public_edge
            <= Decimal("0")
        ):
            raise ValueError(
                "Model value requires a positive "
                "statistical-public edge."
            )

    @property
    def absolute_statistical_market_gap(
        self,
    ) -> Decimal:
        """Return absolute model-versus-market difference."""

        return abs(
            self.statistical_market_gap
        )

    @property
    def has_model_value(self) -> bool:
        """Return whether the outcome has statistical value."""

        return (
            self.model_value_level
            is not ModelValueLevel.NONE
        )

    @property
    def has_strong_model_value(self) -> bool:
        """Return whether the statistical value is strong."""

        return (
            self.model_value_level
            is ModelValueLevel.STRONG_VALUE
        )

    @property
    def model_and_market_agree(self) -> bool:
        """Return whether model and market are close."""

        return (
            self.evidence_direction
            is ProbabilityEvidenceDirection.AGREEMENT
        )


@dataclass(frozen=True, slots=True)
class StatisticalMarketComparisonReport:
    """Contains the complete model-market-public comparison."""

    statistical_prediction: StatisticalMatchPrediction
    market_analysis: MarketAnalysisReport
    outcome_comparisons: tuple[
        OutcomeProbabilityComparison,
        ...,
    ]
    conflict_level: ModelMarketConflictLevel

    def __post_init__(self) -> None:
        """Validate the complete comparison report."""

        if not isinstance(
            self.statistical_prediction,
            StatisticalMatchPrediction,
        ):
            raise TypeError(
                "statistical_prediction must be a "
                "StatisticalMatchPrediction."
            )

        if not isinstance(
            self.market_analysis,
            MarketAnalysisReport,
        ):
            raise TypeError(
                "market_analysis must be "
                "a MarketAnalysisReport."
            )

        if not isinstance(
            self.outcome_comparisons,
            tuple,
        ):
            raise TypeError(
                "outcome_comparisons must be a tuple."
            )

        outcome_order = tuple(
            comparison.outcome
            for comparison in self.outcome_comparisons
        )

        if outcome_order != Outcome.ordered():
            raise ValueError(
                "Outcome comparisons must follow "
                "official 1-X-2 order."
            )

        for comparison in self.outcome_comparisons:
            if not isinstance(
                comparison,
                OutcomeProbabilityComparison,
            ):
                raise TypeError(
                    "outcome_comparisons may only contain "
                    "OutcomeProbabilityComparison objects."
                )

            statistical_probability = (
                self.statistical_prediction
                .probability_for(
                    comparison.outcome
                )
            )
            market_value = (
                self.market_analysis
                .latest_value_analysis
                .for_outcome(
                    comparison.outcome
                )
            )

            if (
                comparison.statistical_probability
                != statistical_probability
            ):
                raise ValueError(
                    "Outcome statistical probability "
                    "does not match the prediction."
                )

            if (
                comparison.market_probability
                != market_value.market_probability
                or comparison.public_percentage
                != market_value.public_percentage
            ):
                raise ValueError(
                    "Outcome market values do not match "
                    "the market analysis."
                )

        if not isinstance(
            self.conflict_level,
            ModelMarketConflictLevel,
        ):
            raise TypeError(
                "conflict_level must be a "
                "ModelMarketConflictLevel."
            )

    def for_outcome(
        self,
        outcome: Outcome,
    ) -> OutcomeProbabilityComparison:
        """Return the comparison for one outcome."""

        resolved_outcome = Outcome.parse(
            outcome
        )

        for comparison in self.outcome_comparisons:
            if comparison.outcome is resolved_outcome:
                return comparison

        raise LookupError(
            f"No comparison exists for "
            f"{resolved_outcome.value}."
        )

    @property
    def statistical_favorite(self) -> Outcome:
        """Return the statistical model favorite."""

        return (
            self.statistical_prediction
            .favorite_outcome
        )

    @property
    def market_favorite(self) -> Outcome:
        """Return the odds-market favorite."""

        return (
            self.market_analysis
            .market_favorite
            .outcome
        )

    @property
    def public_favorite(self) -> Outcome:
        """Return the public favorite."""

        return (
            self.market_analysis
            .public_favorite
            .outcome
        )

    @property
    def statistical_market_agree(self) -> bool:
        """Return whether model and market favorites agree."""

        return (
            self.statistical_favorite
            is self.market_favorite
        )

    @property
    def full_consensus(self) -> bool:
        """Return whether model, market and public agree."""

        return (
            self.statistical_favorite
            is self.market_favorite
            is self.public_favorite
        )

    @property
    def model_value_outcomes(
        self,
    ) -> tuple[OutcomeProbabilityComparison, ...]:
        """Return outcomes with statistical value versus public."""

        return tuple(
            comparison
            for comparison in self.outcome_comparisons
            if comparison.has_model_value
        )

    @property
    def strong_model_value_outcomes(
        self,
    ) -> tuple[OutcomeProbabilityComparison, ...]:
        """Return outcomes with strong statistical value."""

        return tuple(
            comparison
            for comparison in self.outcome_comparisons
            if comparison.has_strong_model_value
        )

    @property
    def strongest_model_value(
        self,
    ) -> OutcomeProbabilityComparison:
        """Return the strongest statistical-public edge."""

        return max(
            self.outcome_comparisons,
            key=lambda comparison: (
                comparison.statistical_public_edge
            ),
        )

    @property
    def strongest_market_disagreement(
        self,
    ) -> OutcomeProbabilityComparison:
        """Return the largest absolute model-market gap."""

        return max(
            self.outcome_comparisons,
            key=lambda comparison: (
                comparison
                .absolute_statistical_market_gap
            ),
        )

    @property
    def has_high_conflict(self) -> bool:
        """Return whether model-market conflict is high."""

        return (
            self.conflict_level
            is ModelMarketConflictLevel.HIGH
        )