"""Tests for football market classification models."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.models.market_classification import (
    MarketClassificationReport,
    MarketRole,
    OutcomeMarketProfile,
)
from src.models.market_snapshot import MarketSnapshot
from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.market_value_analyzer import (
    MarketValueAnalyzer,
)


def create_value_analysis():
    """Create a representative value analysis."""

    snapshot = MarketSnapshot(
        captured_at=datetime(
            2026,
            8,
            1,
            14,
            0,
            tzinfo=timezone.utc,
        ),
        odds=ThreeWayOdds(
            Decimal("1.80"),
            Decimal("3.80"),
            Decimal("4.50"),
        ),
        public_percentages=ThreeWayPercentages(
            Decimal("60"),
            Decimal("23"),
            Decimal("17"),
        ),
    )

    return MarketValueAnalyzer().analyze(
        snapshot.odds,
        snapshot.public_percentages,
    )


def create_profile(
    outcome: Outcome,
    *,
    roles: tuple[MarketRole, ...],
) -> OutcomeMarketProfile:
    """Create one profile matching the test analysis."""

    value = create_value_analysis().for_outcome(
        outcome
    )

    return OutcomeMarketProfile(
        outcome=outcome,
        market_probability=value.market_probability,
        public_percentage=value.public_percentage,
        edge_percentage_points=(
            value.edge_percentage_points
        ),
        value_index=value.value_index,
        roles=roles,
    )


def create_report() -> MarketClassificationReport:
    """Create one valid classification report."""

    return MarketClassificationReport(
        value_analysis=create_value_analysis(),
        alert_report=None,
        profiles=(
            create_profile(
                Outcome.HOME,
                roles=(
                    MarketRole.MARKET_FAVORITE,
                    MarketRole.PUBLIC_FAVORITE,
                    MarketRole.PUBLIC_TRAP,
                ),
            ),
            create_profile(
                Outcome.DRAW,
                roles=(),
            ),
            create_profile(
                Outcome.AWAY,
                roles=(
                    MarketRole.VALUE_PLAY,
                ),
            ),
        ),
    )


def test_profile_exposes_role_helpers() -> None:
    profile = create_profile(
        Outcome.AWAY,
        roles=(
            MarketRole.VALUE_PLAY,
            MarketRole.CONTRARIAN_VALUE,
        ),
    )

    assert profile.is_value_play is True
    assert profile.is_public_trap is False
    assert profile.has_role(
        MarketRole.CONTRARIAN_VALUE
    ) is True


def test_profile_rejects_duplicate_roles() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain duplicates",
    ):
        create_profile(
            Outcome.HOME,
            roles=(
                MarketRole.PUBLIC_FAVORITE,
                MarketRole.PUBLIC_FAVORITE,
            ),
        )


def test_profile_rejects_invalid_role() -> None:
    with pytest.raises(
        TypeError,
        match="MarketRole values",
    ):
        create_profile(
            Outcome.HOME,
            roles=(
                "invalid",  # type: ignore[arg-type]
            ),
        )


def test_report_exposes_summary_properties() -> None:
    report = create_report()

    assert (
        report.market_favorite.outcome
        is Outcome.HOME
    )
    assert (
        report.public_favorite.outcome
        is Outcome.HOME
    )
    assert (
        report.best_value.outcome
        is Outcome.AWAY
    )
    assert report.market_and_public_agree is True


def test_report_filters_profiles() -> None:
    report = create_report()

    assert tuple(
        profile.outcome
        for profile in report.value_plays
    ) == (
        Outcome.AWAY,
    )
    assert tuple(
        profile.outcome
        for profile in report.public_traps
    ) == (
        Outcome.HOME,
    )