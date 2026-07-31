"""Final end-to-end football match analysis orchestration."""

from src.models.final_match_analysis import (
    FinalMatchAnalysisReport,
)
from src.models.final_match_summary import (
    FinalMatchSummary,
)
from src.models.match_analysis_input import MatchAnalysisInput
from src.services.integrated_recommendation_engine import (
    IntegratedRecommendationEngine,
)
from src.services.match_analysis_engine import (
    MatchAnalysisEngine,
)


class FinalMatchAnalysisEngine:
    """Runs the complete Project 13 match-analysis pipeline."""

    def __init__(
        self,
        match_analysis_engine: (
            MatchAnalysisEngine
            | None
        ) = None,
        recommendation_engine: (
            IntegratedRecommendationEngine
            | None
        ) = None,
    ) -> None:
        """Create the final end-to-end analysis engine."""

        if (
            match_analysis_engine is not None
            and not isinstance(
                match_analysis_engine,
                MatchAnalysisEngine,
            )
        ):
            raise TypeError(
                "match_analysis_engine must be a "
                "MatchAnalysisEngine or None."
            )

        if (
            recommendation_engine is not None
            and not isinstance(
                recommendation_engine,
                IntegratedRecommendationEngine,
            )
        ):
            raise TypeError(
                "recommendation_engine must be an "
                "IntegratedRecommendationEngine "
                "or None."
            )

        self._match_analysis_engine = (
            match_analysis_engine
            or MatchAnalysisEngine()
        )
        self._recommendation_engine = (
            recommendation_engine
            or IntegratedRecommendationEngine()
        )

    def analyze(
        self,
        analysis_input: MatchAnalysisInput,
    ) -> FinalMatchAnalysisReport:
        """Run the complete final analysis."""

        if not isinstance(
            analysis_input,
            MatchAnalysisInput,
        ):
            raise TypeError(
                "FinalMatchAnalysisEngine requires "
                "a MatchAnalysisInput."
            )

        match_analysis = (
            self._match_analysis_engine.analyze(
                analysis_input
            )
        )

        recommendation = (
            self._recommendation_engine.recommend(
                match_analysis
            )
        )

        return FinalMatchAnalysisReport(
            analysis_input=analysis_input,
            match_analysis=match_analysis,
            recommendation=recommendation,
        )

    def analyze_summary(
        self,
        analysis_input: MatchAnalysisInput,
    ) -> FinalMatchSummary:
        """Run the analysis and return its flat summary."""

        return self.analyze(
            analysis_input
        ).to_summary()