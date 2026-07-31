"""Complete market analysis orchestration service."""

from src.models.market_analysis import (
    MarketAnalysisReport,
)
from src.models.market_snapshot import MarketSnapshot
from src.services.market_alert_analyzer import (
    MarketAlertAnalyzer,
)
from src.services.market_classifier import (
    MarketClassifier,
)
from src.services.market_movement_analyzer import (
    MarketMovementAnalyzer,
)
from src.services.market_recommendation_engine import (
    MarketRecommendationEngine,
)


class MarketAnalysisEngine:
    """Runs the complete market analysis pipeline."""

    def __init__(
        self,
        movement_analyzer: MarketMovementAnalyzer | None = None,
        alert_analyzer: MarketAlertAnalyzer | None = None,
        classifier: MarketClassifier | None = None,
        recommendation_engine: (
            MarketRecommendationEngine
            | None
        ) = None,
    ) -> None:
        """Create the complete market analysis engine."""

        self._movement_analyzer = (
            movement_analyzer
            or MarketMovementAnalyzer()
        )
        self._alert_analyzer = (
            alert_analyzer
            or MarketAlertAnalyzer()
        )
        self._classifier = (
            classifier
            or MarketClassifier()
        )
        self._recommendation_engine = (
            recommendation_engine
            or MarketRecommendationEngine()
        )

    def analyze(
        self,
        earlier_snapshot: MarketSnapshot,
        later_snapshot: MarketSnapshot,
    ) -> MarketAnalysisReport:
        """Run all market-analysis stages in order."""

        movement_analysis = (
            self._movement_analyzer.analyze(
                earlier_snapshot,
                later_snapshot,
            )
        )

        alert_report = (
            self._alert_analyzer.analyze(
                movement_analysis
            )
        )

        classification_report = (
            self._classifier.classify(
                movement_analysis
                .later_value_analysis,
                alert_report,
            )
        )

        recommendation = (
            self._recommendation_engine.recommend(
                classification_report
            )
        )

        return MarketAnalysisReport(
            movement_analysis=movement_analysis,
            alert_report=alert_report,
            classification_report=(
                classification_report
            ),
            recommendation=recommendation,
        )