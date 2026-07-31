"""Market-based sign recommendation engine."""

from src.models.market_classification import (
    MarketClassificationReport,
    MarketRole,
    OutcomeMarketProfile,
)
from src.models.market_recommendation import (
    MatchRecommendation,
    RecommendationCoverage,
    RecommendationRiskFactor,
    RecommendationRiskLevel,
)
from src.models.market_recommendation_thresholds import (
    MarketRecommendationThresholds,
)
from src.models.outcome import Outcome


class MarketRecommendationEngine:
    """Creates market-based sign and risk recommendations."""

    def __init__(
        self,
        thresholds: (
            MarketRecommendationThresholds
            | None
        ) = None,
    ) -> None:
        """Create the recommendation engine."""

        self._thresholds = (
            thresholds
            or MarketRecommendationThresholds()
        )

    def recommend(
        self,
        classification_report: MarketClassificationReport,
    ) -> MatchRecommendation:
        """Create a recommendation from market classification."""

        if not isinstance(
            classification_report,
            MarketClassificationReport,
        ):
            raise TypeError(
                "MarketRecommendationEngine requires "
                "a MarketClassificationReport."
            )

        primary_profile = (
            classification_report.market_favorite
        )
        recommended_outcomes: set[Outcome] = {
            primary_profile.outcome
        }

        if not (
            classification_report.market_and_public_agree
        ):
            recommended_outcomes.add(
                classification_report
                .public_favorite
                .outcome
            )

        for profile in (
            classification_report.value_plays
        ):
            recommended_outcomes.add(
                profile.outcome
            )

        for profile in classification_report.profiles:
            if profile.has_role(
                MarketRole.CONTRARIAN_VALUE
            ):
                recommended_outcomes.add(
                    profile.outcome
                )

        if (
            primary_profile.is_public_trap
            and (
                classification_report
                .best_value
                .outcome
                is not primary_profile.outcome
            )
        ):
            recommended_outcomes.add(
                classification_report
                .best_value
                .outcome
            )

        if (
            len(recommended_outcomes) == 1
            and self._needs_additional_guard(
                primary_profile
            )
        ):
            recommended_outcomes.add(
                self._best_alternative(
                    classification_report,
                    primary_profile.outcome,
                ).outcome
            )

        ordered_outcomes = tuple(
            outcome
            for outcome in Outcome.ordered()
            if outcome in recommended_outcomes
        )
        risk_factors = (
            self._create_risk_factors(
                classification_report,
                primary_profile,
            )
        )
        risk_score = sum(
            risk_factor.weight
            for risk_factor in risk_factors
        )

        return MatchRecommendation(
            classification_report=classification_report,
            primary_outcome=primary_profile.outcome,
            recommended_outcomes=ordered_outcomes,
            coverage=(
                RecommendationCoverage.from_sign_count(
                    len(ordered_outcomes)
                )
            ),
            risk_level=self._resolve_risk_level(
                risk_score
            ),
            risk_score=risk_score,
            risk_factors=risk_factors,
        )

    def _needs_additional_guard(
        self,
        primary_profile: OutcomeMarketProfile,
    ) -> bool:
        """Return whether a single sign needs protection."""

        return (
            primary_profile.market_probability
            < (
                self._thresholds
                .confident_single_probability
            )
            or primary_profile.edge_percentage_points
            <= -(
                self._thresholds
                .single_negative_edge_limit
            )
            or primary_profile.has_role(
                MarketRole.VALUE_EROSION
            )
        )

    @staticmethod
    def _best_alternative(
        classification_report: MarketClassificationReport,
        primary_outcome: Outcome,
    ) -> OutcomeMarketProfile:
        """Return the strongest alternative to the favorite."""

        alternatives = tuple(
            profile
            for profile in classification_report.profiles
            if profile.outcome is not primary_outcome
        )

        return max(
            alternatives,
            key=lambda profile: (
                profile.edge_percentage_points,
                profile.market_probability,
            ),
        )

    def _create_risk_factors(
        self,
        classification_report: MarketClassificationReport,
        primary_profile: OutcomeMarketProfile,
    ) -> tuple[RecommendationRiskFactor, ...]:
        """Create all applicable recommendation risk factors."""

        risk_factors: list[
            RecommendationRiskFactor
        ] = []

        if primary_profile.is_public_trap:
            risk_factors.append(
                RecommendationRiskFactor.PUBLIC_TRAP
            )

        if not (
            classification_report.market_and_public_agree
        ):
            risk_factors.append(
                RecommendationRiskFactor
                .FAVORITE_DISAGREEMENT
            )

        if (
            primary_profile.market_probability
            < (
                self._thresholds
                .weak_favorite_probability
            )
        ):
            risk_factors.append(
                RecommendationRiskFactor
                .WEAK_MARKET_FAVORITE
            )

        if any(
            profile.outcome
            is not primary_profile.outcome
            for profile in (
                classification_report.value_plays
            )
        ):
            risk_factors.append(
                RecommendationRiskFactor.VALUE_CHALLENGER
            )

        if primary_profile.has_role(
            MarketRole.VALUE_EROSION
        ):
            risk_factors.append(
                RecommendationRiskFactor.VALUE_EROSION
            )

        if any(
            profile.outcome
            is not primary_profile.outcome
            and profile.has_role(
                MarketRole.CONTRARIAN_VALUE
            )
            for profile in classification_report.profiles
        ):
            risk_factors.append(
                RecommendationRiskFactor
                .CONTRARIAN_CHALLENGER
            )

        if (
            primary_profile.is_public_trap
            and primary_profile.has_role(
                MarketRole.PUBLIC_SURGE
            )
        ):
            risk_factors.append(
                RecommendationRiskFactor
                .SURGING_PUBLIC_TRAP
            )

        return tuple(
            risk_factors
        )

    def _resolve_risk_level(
        self,
        risk_score: int,
    ) -> RecommendationRiskLevel:
        """Convert total risk points into a risk level."""

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