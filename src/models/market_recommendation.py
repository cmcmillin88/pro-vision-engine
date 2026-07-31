"""Market-based sign recommendation models."""

from dataclasses import dataclass
from enum import Enum

from src.models.market_classification import (
    MarketClassificationReport,
)
from src.models.outcome import Outcome


class RecommendationCoverage(str, Enum):
    """Describes how many 1-X-2 signs are recommended."""

    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"

    @property
    def sign_count(self) -> int:
        """Return the number of covered outcomes."""

        counts = {
            RecommendationCoverage.SINGLE: 1,
            RecommendationCoverage.DOUBLE: 2,
            RecommendationCoverage.TRIPLE: 3,
        }

        return counts[self]

    @classmethod
    def from_sign_count(
        cls,
        sign_count: int,
    ) -> "RecommendationCoverage":
        """Resolve coverage from the number of signs."""

        if isinstance(
            sign_count,
            bool,
        ) or not isinstance(
            sign_count,
            int,
        ):
            raise TypeError(
                "Sign count must be an integer."
            )

        coverage_by_count = {
            1: cls.SINGLE,
            2: cls.DOUBLE,
            3: cls.TRIPLE,
        }

        try:
            return coverage_by_count[
                sign_count
            ]
        except KeyError as error:
            raise ValueError(
                "Sign count must be 1, 2 or 3."
            ) from error


class RecommendationRiskLevel(str, Enum):
    """Describes the market-based recommendation risk."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

    @property
    def rank(self) -> int:
        """Return a sortable risk rank."""

        ranks = {
            RecommendationRiskLevel.LOW: 1,
            RecommendationRiskLevel.MEDIUM: 2,
            RecommendationRiskLevel.HIGH: 3,
            RecommendationRiskLevel.EXTREME: 4,
        }

        return ranks[self]


class RecommendationRiskFactor(str, Enum):
    """Describes one reason for recommendation risk."""

    PUBLIC_TRAP = "public_trap"
    FAVORITE_DISAGREEMENT = "favorite_disagreement"
    WEAK_MARKET_FAVORITE = "weak_market_favorite"
    VALUE_CHALLENGER = "value_challenger"
    VALUE_EROSION = "value_erosion"
    CONTRARIAN_CHALLENGER = "contrarian_challenger"
    SURGING_PUBLIC_TRAP = "surging_public_trap"

    @property
    def weight(self) -> int:
        """Return the risk points contributed by the factor."""

        weights = {
            RecommendationRiskFactor.PUBLIC_TRAP: 3,
            RecommendationRiskFactor.FAVORITE_DISAGREEMENT: 3,
            RecommendationRiskFactor.WEAK_MARKET_FAVORITE: 2,
            RecommendationRiskFactor.VALUE_CHALLENGER: 2,
            RecommendationRiskFactor.VALUE_EROSION: 2,
            RecommendationRiskFactor.CONTRARIAN_CHALLENGER: 2,
            RecommendationRiskFactor.SURGING_PUBLIC_TRAP: 1,
        }

        return weights[self]

    @property
    def display_name(self) -> str:
        """Return a human-readable risk factor."""

        names = {
            RecommendationRiskFactor.PUBLIC_TRAP: (
                "Public trap"
            ),
            RecommendationRiskFactor.FAVORITE_DISAGREEMENT: (
                "Market and public disagreement"
            ),
            RecommendationRiskFactor.WEAK_MARKET_FAVORITE: (
                "Weak market favorite"
            ),
            RecommendationRiskFactor.VALUE_CHALLENGER: (
                "Value challenger"
            ),
            RecommendationRiskFactor.VALUE_EROSION: (
                "Value erosion"
            ),
            RecommendationRiskFactor.CONTRARIAN_CHALLENGER: (
                "Contrarian challenger"
            ),
            RecommendationRiskFactor.SURGING_PUBLIC_TRAP: (
                "Surging public trap"
            ),
        }

        return names[self]


@dataclass(frozen=True, slots=True)
class MatchRecommendation:
    """Contains a market-based sign recommendation."""

    classification_report: MarketClassificationReport
    primary_outcome: Outcome
    recommended_outcomes: tuple[Outcome, ...]
    coverage: RecommendationCoverage
    risk_level: RecommendationRiskLevel
    risk_score: int
    risk_factors: tuple[RecommendationRiskFactor, ...]

    def __post_init__(self) -> None:
        """Validate the complete recommendation."""

        if not isinstance(
            self.classification_report,
            MarketClassificationReport,
        ):
            raise TypeError(
                "MatchRecommendation classification_report "
                "must be a MarketClassificationReport."
            )

        if not isinstance(
            self.primary_outcome,
            Outcome,
        ):
            raise TypeError(
                "MatchRecommendation primary_outcome "
                "must be an Outcome."
            )

        if not isinstance(
            self.recommended_outcomes,
            tuple,
        ):
            raise TypeError(
                "MatchRecommendation recommended_outcomes "
                "must be a tuple."
            )

        if not self.recommended_outcomes:
            raise ValueError(
                "At least one outcome must be recommended."
            )

        for outcome in self.recommended_outcomes:
            if not isinstance(
                outcome,
                Outcome,
            ):
                raise TypeError(
                    "Recommended outcomes may only "
                    "contain Outcome values."
                )

        if (
            len(set(self.recommended_outcomes))
            != len(self.recommended_outcomes)
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
                "in the recommended outcomes."
            )

        if not isinstance(
            self.coverage,
            RecommendationCoverage,
        ):
            raise TypeError(
                "MatchRecommendation coverage must be "
                "a RecommendationCoverage."
            )

        expected_coverage = (
            RecommendationCoverage.from_sign_count(
                len(self.recommended_outcomes)
            )
        )

        if self.coverage is not expected_coverage:
            raise ValueError(
                "Recommendation coverage does not match "
                "the number of recommended outcomes."
            )

        if not isinstance(
            self.risk_level,
            RecommendationRiskLevel,
        ):
            raise TypeError(
                "MatchRecommendation risk_level must be "
                "a RecommendationRiskLevel."
            )

        if isinstance(
            self.risk_score,
            bool,
        ) or not isinstance(
            self.risk_score,
            int,
        ):
            raise TypeError(
                "MatchRecommendation risk_score "
                "must be an integer."
            )

        if self.risk_score < 0:
            raise ValueError(
                "MatchRecommendation risk_score "
                "must not be negative."
            )

        if not isinstance(
            self.risk_factors,
            tuple,
        ):
            raise TypeError(
                "MatchRecommendation risk_factors "
                "must be a tuple."
            )

        for risk_factor in self.risk_factors:
            if not isinstance(
                risk_factor,
                RecommendationRiskFactor,
            ):
                raise TypeError(
                    "Risk factors may only contain "
                    "RecommendationRiskFactor values."
                )

        if (
            len(set(self.risk_factors))
            != len(self.risk_factors)
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
                "Risk score must equal the total weight "
                "of all risk factors."
            )

        self.classification_report.for_outcome(
            self.primary_outcome
        )

    @property
    def recommendation_symbols(self) -> str:
        """Return the recommended signs as compact symbols."""

        return "".join(
            outcome.value
            for outcome in self.recommended_outcomes
        )

    @property
    def secondary_outcomes(
        self,
    ) -> tuple[Outcome, ...]:
        """Return recommended outcomes except the primary one."""

        return tuple(
            outcome
            for outcome in self.recommended_outcomes
            if outcome is not self.primary_outcome
        )

    @property
    def requires_guard(self) -> bool:
        """Return whether more than one sign is recommended."""

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
        """Return whether the market case supports a single sign."""

        return (
            self.coverage
            is RecommendationCoverage.SINGLE
            and self.risk_level
            in {
                RecommendationRiskLevel.LOW,
                RecommendationRiskLevel.MEDIUM,
            }
        )

    def has_risk_factor(
        self,
        risk_factor: RecommendationRiskFactor,
    ) -> bool:
        """Return whether one risk factor is present."""

        if not isinstance(
            risk_factor,
            RecommendationRiskFactor,
        ):
            raise TypeError(
                "Risk factor must be a "
                "RecommendationRiskFactor."
            )

        return risk_factor in self.risk_factors