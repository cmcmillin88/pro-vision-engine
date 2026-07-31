"""Flat final-analysis summary for one football match."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.models.integrated_recommendation import (
    IntegratedRiskFactor,
)
from src.models.market_recommendation import (
    RecommendationCoverage,
    RecommendationRiskLevel,
)
from src.models.outcome import Outcome
from src.models.statistical_market_comparison import (
    ModelMarketConflictLevel,
)


class FinalDecisionType(str, Enum):
    """Describes the final Project 13 match decision."""

    SPIKE = "spike"
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"

    @classmethod
    def resolve(
        cls,
        coverage: RecommendationCoverage,
        *,
        is_spike_candidate: bool,
    ) -> "FinalDecisionType":
        """Resolve the final decision from coverage and spike status."""

        if not isinstance(
            coverage,
            RecommendationCoverage,
        ):
            raise TypeError(
                "coverage must be a "
                "RecommendationCoverage."
            )

        if not isinstance(
            is_spike_candidate,
            bool,
        ):
            raise TypeError(
                "is_spike_candidate must be a boolean."
            )

        if is_spike_candidate:
            if coverage is not RecommendationCoverage.SINGLE:
                raise ValueError(
                    "A spike candidate must have "
                    "single coverage."
                )

            return cls.SPIKE

        decisions = {
            RecommendationCoverage.SINGLE: cls.SINGLE,
            RecommendationCoverage.DOUBLE: cls.DOUBLE,
            RecommendationCoverage.TRIPLE: cls.TRIPLE,
        }

        return decisions[
            coverage
        ]


@dataclass(frozen=True, slots=True)
class FinalMatchSummary:
    """Contains an export-ready summary of the final analysis."""

    match_reference: str | None
    home_team_name: str
    away_team_name: str

    projected_home_xg: Decimal
    projected_away_xg: Decimal

    statistical_home_probability: Decimal
    statistical_draw_probability: Decimal
    statistical_away_probability: Decimal

    combined_home_probability: Decimal
    combined_draw_probability: Decimal
    combined_away_probability: Decimal

    primary_outcome: Outcome
    recommended_outcomes: tuple[Outcome, ...]
    coverage: RecommendationCoverage

    risk_level: RecommendationRiskLevel
    risk_score: int
    risk_factors: tuple[
        IntegratedRiskFactor,
        ...,
    ]

    most_likely_scoreline: str
    most_likely_scoreline_probability: Decimal

    full_consensus: bool
    conflict_level: ModelMarketConflictLevel
    is_spike_candidate: bool
    requires_extended_review: bool
    decision_type: FinalDecisionType

    def __post_init__(self) -> None:
        """Normalize and validate the complete summary."""

        home_team_name = self._normalize_text(
            self.home_team_name,
            field_name="home_team_name",
        )
        away_team_name = self._normalize_text(
            self.away_team_name,
            field_name="away_team_name",
        )

        if (
            home_team_name.casefold()
            == away_team_name.casefold()
        ):
            raise ValueError(
                "Home and away teams must be different."
            )

        object.__setattr__(
            self,
            "home_team_name",
            home_team_name,
        )
        object.__setattr__(
            self,
            "away_team_name",
            away_team_name,
        )

        scoreline = self._normalize_text(
            self.most_likely_scoreline,
            field_name="most_likely_scoreline",
        )

        object.__setattr__(
            self,
            "most_likely_scoreline",
            scoreline,
        )

        if self.match_reference is not None:
            match_reference = self._normalize_text(
                self.match_reference,
                field_name="match_reference",
            )

            object.__setattr__(
                self,
                "match_reference",
                match_reference,
            )

        for field_name in (
            "projected_home_xg",
            "projected_away_xg",
        ):
            value = self._validate_decimal(
                getattr(
                    self,
                    field_name,
                ),
                field_name=field_name,
            )

            if value < Decimal("0"):
                raise ValueError(
                    f"{field_name} must not be negative."
                )

        probability_fields = (
            "statistical_home_probability",
            "statistical_draw_probability",
            "statistical_away_probability",
            "combined_home_probability",
            "combined_draw_probability",
            "combined_away_probability",
            "most_likely_scoreline_probability",
        )

        for field_name in probability_fields:
            value = self._validate_decimal(
                getattr(
                    self,
                    field_name,
                ),
                field_name=field_name,
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

        statistical_total = (
            self.statistical_home_probability
            + self.statistical_draw_probability
            + self.statistical_away_probability
        )

        if statistical_total != Decimal("100.00"):
            raise ValueError(
                "Statistical probabilities must total "
                "exactly 100.00."
            )

        combined_total = (
            self.combined_home_probability
            + self.combined_draw_probability
            + self.combined_away_probability
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
            key=self.combined_probability_for,
        )

        if self.primary_outcome is not expected_primary:
            raise ValueError(
                "primary_outcome must have the highest "
                "combined probability."
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

        for outcome in self.recommended_outcomes:
            if not isinstance(
                outcome,
                Outcome,
            ):
                raise TypeError(
                    "recommended_outcomes may only "
                    "contain Outcome values."
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
                "recommended_outcomes must not "
                "contain duplicates."
            )

        expected_order = tuple(
            outcome
            for outcome in Outcome.ordered()
            if outcome in self.recommended_outcomes
        )

        if self.recommended_outcomes != expected_order:
            raise ValueError(
                "recommended_outcomes must follow "
                "official 1-X-2 order."
            )

        if (
            self.primary_outcome
            not in self.recommended_outcomes
        ):
            raise ValueError(
                "primary_outcome must be included "
                "in recommended_outcomes."
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
                "risk_factors must not contain duplicates."
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

        for field_name in (
            "full_consensus",
            "is_spike_candidate",
            "requires_extended_review",
        ):
            if not isinstance(
                getattr(
                    self,
                    field_name,
                ),
                bool,
            ):
                raise TypeError(
                    f"{field_name} must be a boolean."
                )

        if not isinstance(
            self.conflict_level,
            ModelMarketConflictLevel,
        ):
            raise TypeError(
                "conflict_level must be a "
                "ModelMarketConflictLevel."
            )

        if not isinstance(
            self.decision_type,
            FinalDecisionType,
        ):
            raise TypeError(
                "decision_type must be a "
                "FinalDecisionType."
            )

        expected_decision = FinalDecisionType.resolve(
            self.coverage,
            is_spike_candidate=self.is_spike_candidate,
        )

        if self.decision_type is not expected_decision:
            raise ValueError(
                "decision_type does not match "
                "coverage and spike status."
            )

    @property
    def recommendation_symbols(self) -> str:
        """Return compact final 1-X-2 signs."""

        return "".join(
            outcome.value
            for outcome in self.recommended_outcomes
        )

    @property
    def requires_guard(self) -> bool:
        """Return whether the recommendation uses multiple signs."""

        return (
            self.coverage
            is not RecommendationCoverage.SINGLE
        )

    @property
    def is_full_cover(self) -> bool:
        """Return whether all three outcomes are included."""

        return (
            self.coverage
            is RecommendationCoverage.TRIPLE
        )

    def statistical_probability_for(
        self,
        outcome: Outcome,
    ) -> Decimal:
        """Return statistical probability for one outcome."""

        resolved_outcome = Outcome.parse(
            outcome
        )

        values = {
            Outcome.HOME: self.statistical_home_probability,
            Outcome.DRAW: self.statistical_draw_probability,
            Outcome.AWAY: self.statistical_away_probability,
        }

        return values[
            resolved_outcome
        ]

    def combined_probability_for(
        self,
        outcome: Outcome,
    ) -> Decimal:
        """Return combined probability for one outcome."""

        resolved_outcome = Outcome.parse(
            outcome
        )

        values = {
            Outcome.HOME: self.combined_home_probability,
            Outcome.DRAW: self.combined_draw_probability,
            Outcome.AWAY: self.combined_away_probability,
        }

        return values[
            resolved_outcome
        ]

    @staticmethod
    def _validate_decimal(
        value: object,
        *,
        field_name: str,
    ) -> Decimal:
        """Validate one finite Decimal."""

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

        return value

    @staticmethod
    def _normalize_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """Normalize one required text value."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string."
            )

        normalized_value = " ".join(
            value.split()
        )

        if not normalized_value:
            raise ValueError(
                f"{field_name} must not be empty."
            )

        return normalized_value