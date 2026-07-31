"""Complete football match analysis orchestration service."""

from src.models.match_analysis import (
    MatchAnalysisReport,
)
from src.models.match_analysis_input import (
    MatchAnalysisInput,
)
from src.services.market_analysis_engine import (
    MarketAnalysisEngine,
)
from src.services.statistical_analysis_engine import (
    StatisticalAnalysisEngine,
)
from src.services.statistical_market_comparison_analyzer import (
    StatisticalMarketComparisonAnalyzer,
)


class MatchAnalysisEngine:
    """Runs statistical, market and evidence analysis in order."""

    def __init__(
        self,
        statistical_engine: (
            StatisticalAnalysisEngine
            | None
        ) = None,
        market_engine: MarketAnalysisEngine | None = None,
        comparison_analyzer: (
            StatisticalMarketComparisonAnalyzer
            | None
        ) = None,
    ) -> None:
        """Create the complete match-analysis engine."""

        if (
            statistical_engine is not None
            and not isinstance(
                statistical_engine,
                StatisticalAnalysisEngine,
            )
        ):
            raise TypeError(
                "statistical_engine must be a "
                "StatisticalAnalysisEngine or None."
            )

        if (
            market_engine is not None
            and not isinstance(
                market_engine,
                MarketAnalysisEngine,
            )
        ):
            raise TypeError(
                "market_engine must be a "
                "MarketAnalysisEngine or None."
            )

        if (
            comparison_analyzer is not None
            and not isinstance(
                comparison_analyzer,
                StatisticalMarketComparisonAnalyzer,
            )
        ):
            raise TypeError(
                "comparison_analyzer must be a "
                "StatisticalMarketComparisonAnalyzer "
                "or None."
            )

        self._statistical_engine = (
            statistical_engine
            or StatisticalAnalysisEngine()
        )
        self._market_engine = (
            market_engine
            or MarketAnalysisEngine()
        )
        self._comparison_analyzer = (
            comparison_analyzer
            or StatisticalMarketComparisonAnalyzer()
        )

    def analyze(
        self,
        analysis_input: MatchAnalysisInput,
    ) -> MatchAnalysisReport:
        """Run the complete match-analysis pipeline."""

        if not isinstance(
            analysis_input,
            MatchAnalysisInput,
        ):
            raise TypeError(
                "MatchAnalysisEngine requires "
                "a MatchAnalysisInput."
            )

        statistical_analysis = (
            self._statistical_engine.analyze(
                analysis_input.home_performances,
                analysis_input.away_performances,
            )
        )

        market_analysis = self._market_engine.analyze(
            analysis_input.earlier_market_snapshot,
            analysis_input.later_market_snapshot,
        )

        evidence_comparison = (
            self._comparison_analyzer.analyze(
                statistical_analysis.prediction,
                market_analysis,
            )
        )

        return MatchAnalysisReport(
            analysis_input=analysis_input,
            statistical_analysis=statistical_analysis,
            market_analysis=market_analysis,
            evidence_comparison=evidence_comparison,
        )