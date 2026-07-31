"""Complete market analysis result for one football match."""

from dataclasses import dataclass
from datetime import timedelta

from src.models.market_alert import (
    MarketAlert,
    MarketAlertReport,
)
from src.models.market_classification import (
    MarketClassificationReport,
    OutcomeMarketProfile,
)
from src.models.market_movement import (
    MarketMovementAnalysis,
)
from src.models.market_recommendation import (
    MatchRecommendation,
    RecommendationRiskLevel,
)
from src.models.market_snapshot import MarketSnapshot
from src.models.market_value import MarketValueAnalysis
from src.models.outcome import Outcome


@dataclass(frozen=True, slots=True)
class MarketAnalysisReport:
    """Contains the complete market analysis pipeline result."""

    movement_analysis: MarketMovementAnalysis
    alert_report: MarketAlertReport
    classification_report: MarketClassificationReport
    recommendation: MatchRecommendation

    def __post_init__(self) -> None:
        """Validate all relationships in the analysis chain."""

        if not isinstance(
            self.movement_analysis,
            MarketMovementAnalysis,
        ):
            raise TypeError(
                "MarketAnalysisReport movement_analysis "
                "must be a MarketMovementAnalysis."
            )

        if not isinstance(
            self.alert_report,
            MarketAlertReport,
        ):
            raise TypeError(
                "MarketAnalysisReport alert_report "
                "must be a MarketAlertReport."
            )

        if not isinstance(
            self.classification_report,
            MarketClassificationReport,
        ):
            raise TypeError(
                "MarketAnalysisReport classification_report "
                "must be a MarketClassificationReport."
            )

        if not isinstance(
            self.recommendation,
            MatchRecommendation,
        ):
            raise TypeError(
                "MarketAnalysisReport recommendation "
                "must be a MatchRecommendation."
            )

        if (
            self.alert_report.movement_analysis
            != self.movement_analysis
        ):
            raise ValueError(
                "Alert report must describe the same "
                "movement analysis."
            )

        if (
            self.classification_report.value_analysis
            != self.movement_analysis.later_value_analysis
        ):
            raise ValueError(
                "Classification report must describe "
                "the latest value analysis."
            )

        if (
            self.classification_report.alert_report
            != self.alert_report
        ):
            raise ValueError(
                "Classification report must use "
                "the supplied alert report."
            )

        if (
            self.recommendation.classification_report
            != self.classification_report
        ):
            raise ValueError(
                "Recommendation must use the supplied "
                "classification report."
            )

    @property
    def earlier_snapshot(self) -> MarketSnapshot:
        """Return the earlier market snapshot."""

        return self.movement_analysis.earlier_snapshot

    @property
    def latest_snapshot(self) -> MarketSnapshot:
        """Return the latest market snapshot."""

        return self.movement_analysis.later_snapshot

    @property
    def earlier_value_analysis(
        self,
    ) -> MarketValueAnalysis:
        """Return the value analysis for the earlier market."""

        return (
            self.movement_analysis
            .earlier_value_analysis
        )

    @property
    def latest_value_analysis(
        self,
    ) -> MarketValueAnalysis:
        """Return the value analysis for the latest market."""

        return (
            self.movement_analysis
            .later_value_analysis
        )

    @property
    def elapsed_time(self) -> timedelta:
        """Return the time between market snapshots."""

        return self.movement_analysis.elapsed_time

    @property
    def alerts(self) -> tuple[MarketAlert, ...]:
        """Return all generated market alerts."""

        return self.alert_report.alerts

    @property
    def profiles(
        self,
    ) -> tuple[OutcomeMarketProfile, ...]:
        """Return all classified outcome profiles."""

        return self.classification_report.profiles

    @property
    def market_favorite(
        self,
    ) -> OutcomeMarketProfile:
        """Return the odds market favorite."""

        return self.classification_report.market_favorite

    @property
    def public_favorite(
        self,
    ) -> OutcomeMarketProfile:
        """Return the public favorite."""

        return self.classification_report.public_favorite

    @property
    def best_value(
        self,
    ) -> OutcomeMarketProfile:
        """Return the strongest current value outcome."""

        return self.classification_report.best_value

    @property
    def public_traps(
        self,
    ) -> tuple[OutcomeMarketProfile, ...]:
        """Return all detected public traps."""

        return self.classification_report.public_traps

    @property
    def value_plays(
        self,
    ) -> tuple[OutcomeMarketProfile, ...]:
        """Return all detected value plays."""

        return self.classification_report.value_plays

    @property
    def primary_outcome(self) -> Outcome:
        """Return the recommendation's primary outcome."""

        return self.recommendation.primary_outcome

    @property
    def recommended_outcomes(
        self,
    ) -> tuple[Outcome, ...]:
        """Return all recommended outcomes."""

        return self.recommendation.recommended_outcomes

    @property
    def recommendation_symbols(self) -> str:
        """Return compact recommended 1-X-2 signs."""

        return self.recommendation.recommendation_symbols

    @property
    def risk_level(
        self,
    ) -> RecommendationRiskLevel:
        """Return the recommendation risk level."""

        return self.recommendation.risk_level

    @property
    def risk_score(self) -> int:
        """Return the total recommendation risk score."""

        return self.recommendation.risk_score

    @property
    def has_alerts(self) -> bool:
        """Return whether market alerts were generated."""

        return self.alert_report.has_alerts

    @property
    def has_critical_alerts(self) -> bool:
        """Return whether any critical alert exists."""

        return bool(
            self.alert_report.critical_alerts
        )

    @property
    def is_spike_candidate(self) -> bool:
        """Return whether the market supports a spike."""

        return self.recommendation.is_spike_candidate