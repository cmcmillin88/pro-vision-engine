"""Classification service for football pool market roles."""

from src.models.market_alert import (
    MarketAlertReport,
    MarketAlertType,
)
from src.models.market_classification import (
    MarketClassificationReport,
    MarketRole,
    OutcomeMarketProfile,
)
from src.models.market_classification_thresholds import (
    MarketClassificationThresholds,
)
from src.models.market_value import (
    MarketValueAnalysis,
    OutcomeValue,
)
from src.models.outcome import Outcome


class MarketClassifier:
    """Classifies outcomes as favorites, value plays and traps."""

    _alert_role_mapping = {
        MarketAlertType.ODDS_STEAM: (
            MarketRole.ODDS_STEAM
        ),
        MarketAlertType.PUBLIC_SURGE: (
            MarketRole.PUBLIC_SURGE
        ),
        MarketAlertType.VALUE_EROSION: (
            MarketRole.VALUE_EROSION
        ),
        MarketAlertType.CONTRARIAN_VALUE: (
            MarketRole.CONTRARIAN_VALUE
        ),
    }

    def __init__(
        self,
        thresholds: (
            MarketClassificationThresholds
            | None
        ) = None,
    ) -> None:
        """Create the classifier."""

        self._thresholds = (
            thresholds
            or MarketClassificationThresholds()
        )

    def classify(
        self,
        value_analysis: MarketValueAnalysis,
        alert_report: MarketAlertReport | None = None,
    ) -> MarketClassificationReport:
        """Classify all outcomes in one market analysis."""

        self._validate_inputs(
            value_analysis,
            alert_report,
        )

        market_favorite = max(
            Outcome.ordered(),
            key=lambda outcome: (
                value_analysis
                .for_outcome(outcome)
                .market_probability
            ),
        )
        public_favorite = max(
            Outcome.ordered(),
            key=lambda outcome: (
                value_analysis
                .for_outcome(outcome)
                .public_percentage
            ),
        )

        profiles = tuple(
            self._create_profile(
                outcome_value=(
                    value_analysis.for_outcome(
                        outcome
                    )
                ),
                market_favorite=market_favorite,
                public_favorite=public_favorite,
                alert_report=alert_report,
            )
            for outcome in Outcome.ordered()
        )

        return MarketClassificationReport(
            value_analysis=value_analysis,
            alert_report=alert_report,
            profiles=profiles,
        )

    def _create_profile(
        self,
        *,
        outcome_value: OutcomeValue,
        market_favorite: Outcome,
        public_favorite: Outcome,
        alert_report: MarketAlertReport | None,
    ) -> OutcomeMarketProfile:
        """Create one classified outcome profile."""

        roles: list[MarketRole] = []

        if (
            outcome_value.outcome
            is market_favorite
        ):
            roles.append(
                MarketRole.MARKET_FAVORITE
            )

        if (
            outcome_value.outcome
            is public_favorite
        ):
            roles.append(
                MarketRole.PUBLIC_FAVORITE
            )

        if (
            outcome_value.edge_percentage_points
            >= self._thresholds.value_play_edge
        ):
            roles.append(
                MarketRole.VALUE_PLAY
            )

        if (
            outcome_value.public_percentage
            >= (
                self._thresholds
                .public_trap_public_minimum
            )
            and outcome_value.edge_percentage_points
            <= -(
                self._thresholds
                .public_trap_negative_edge
            )
        ):
            roles.append(
                MarketRole.PUBLIC_TRAP
            )

        if alert_report is not None:
            outcome_alerts = alert_report.for_outcome(
                outcome_value.outcome
            )
            alert_types = {
                alert.alert_type
                for alert in outcome_alerts
            }

            for (
                alert_type,
                market_role,
            ) in self._alert_role_mapping.items():
                if alert_type in alert_types:
                    roles.append(
                        market_role
                    )

        return OutcomeMarketProfile(
            outcome=outcome_value.outcome,
            market_probability=(
                outcome_value.market_probability
            ),
            public_percentage=(
                outcome_value.public_percentage
            ),
            edge_percentage_points=(
                outcome_value.edge_percentage_points
            ),
            value_index=outcome_value.value_index,
            roles=tuple(roles),
        )

    @staticmethod
    def _validate_inputs(
        value_analysis: MarketValueAnalysis,
        alert_report: MarketAlertReport | None,
    ) -> None:
        """Validate classifier input objects."""

        if not isinstance(
            value_analysis,
            MarketValueAnalysis,
        ):
            raise TypeError(
                "MarketClassifier requires "
                "a MarketValueAnalysis."
            )

        if (
            alert_report is not None
            and not isinstance(
                alert_report,
                MarketAlertReport,
            )
        ):
            raise TypeError(
                "MarketClassifier alert_report "
                "must be a MarketAlertReport or None."
            )

        if (
            alert_report is not None
            and (
                alert_report
                .movement_analysis
                .later_value_analysis
                != value_analysis
            )
        ):
            raise ValueError(
                "Alert report and value analysis "
                "must describe the same latest market."
            )