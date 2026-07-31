"""Complete statistical football analysis orchestration service."""

from collections.abc import Iterable

from src.models.statistical_analysis import (
    StatisticalAnalysisReport,
)
from src.models.statistical_analysis_settings import (
    StatisticalAnalysisSettings,
)
from src.models.team_match_performance import (
    MatchVenue,
    TeamMatchPerformance,
)
from src.services.poisson_match_predictor import (
    PoissonMatchPredictor,
)
from src.services.team_form_analyzer import (
    TeamFormAnalyzer,
)
from src.services.team_form_comparison_analyzer import (
    TeamFormComparisonAnalyzer,
)


class StatisticalAnalysisEngine:
    """Runs the complete statistical analysis pipeline."""

    def __init__(
        self,
        settings: StatisticalAnalysisSettings | None = None,
        form_analyzer: TeamFormAnalyzer | None = None,
        comparison_analyzer: (
            TeamFormComparisonAnalyzer
            | None
        ) = None,
        predictor: PoissonMatchPredictor | None = None,
    ) -> None:
        """Create the complete statistical analysis engine."""

        if (
            settings is not None
            and not isinstance(
                settings,
                StatisticalAnalysisSettings,
            )
        ):
            raise TypeError(
                "settings must be a "
                "StatisticalAnalysisSettings or None."
            )

        if (
            form_analyzer is not None
            and not isinstance(
                form_analyzer,
                TeamFormAnalyzer,
            )
        ):
            raise TypeError(
                "form_analyzer must be a "
                "TeamFormAnalyzer or None."
            )

        if (
            comparison_analyzer is not None
            and not isinstance(
                comparison_analyzer,
                TeamFormComparisonAnalyzer,
            )
        ):
            raise TypeError(
                "comparison_analyzer must be a "
                "TeamFormComparisonAnalyzer or None."
            )

        if (
            predictor is not None
            and not isinstance(
                predictor,
                PoissonMatchPredictor,
            )
        ):
            raise TypeError(
                "predictor must be a "
                "PoissonMatchPredictor or None."
            )

        self._settings = (
            settings
            or StatisticalAnalysisSettings()
        )
        self._form_analyzer = (
            form_analyzer
            or TeamFormAnalyzer()
        )
        self._comparison_analyzer = (
            comparison_analyzer
            or TeamFormComparisonAnalyzer()
        )
        self._predictor = (
            predictor
            or PoissonMatchPredictor()
        )

    def analyze(
        self,
        home_performances: Iterable[
            TeamMatchPerformance
        ],
        away_performances: Iterable[
            TeamMatchPerformance
        ],
    ) -> StatisticalAnalysisReport:
        """Run all statistical analysis stages in order."""

        home_form = self._form_analyzer.analyze(
            home_performances,
            limit=self._settings.home_match_limit,
            venue=MatchVenue.HOME,
            competition=self._settings.competition,
        )

        away_form = self._form_analyzer.analyze(
            away_performances,
            limit=self._settings.away_match_limit,
            venue=MatchVenue.AWAY,
            competition=self._settings.competition,
        )

        form_comparison = (
            self._comparison_analyzer.analyze(
                home_form,
                away_form,
            )
        )

        prediction = self._predictor.predict(
            form_comparison
        )

        return StatisticalAnalysisReport(
            home_form=home_form,
            away_form=away_form,
            form_comparison=form_comparison,
            prediction=prediction,
        )