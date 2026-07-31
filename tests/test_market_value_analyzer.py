"""Tests for odds-versus-public market value analysis."""

from decimal import Decimal

import pytest

from src.models.outcome import Outcome
from src.models.three_way_odds import ThreeWayOdds
from src.models.three_way_percentages import (
    ThreeWayPercentages,
)
from src.services.market_value_analyzer import (
    MarketValueAnalyzer,
)


def create_odds() -> ThreeWayOdds:
    """Create representative football odds."""

    return ThreeWayOdds(
        home=Decimal("2.00"),
        draw=Decimal("3.50"),
        away=Decimal("4.00"),
    )


def create_public_percentages() -> ThreeWayPercentages:
    """Create representative public percentages."""

    return ThreeWayPercentages(
        home=Decimal("55"),
        draw=Decimal("25"),
        away=Decimal("20"),
    )


def test_analysis_normalizes_market_probabilities() -> None:
    analysis = MarketValueAnalyzer().analyze(
        create_odds(),
        create_public_percentages(),
    )

    assert (
        analysis.market_probabilities.home
        == Decimal("48.28")
    )
    assert (
        analysis.market_probabilities.draw
        == Decimal("27.59")
    )
    assert (
        analysis.market_probabilities.away
        == Decimal("24.14")
    )
    assert (
        analysis.market_probabilities.total
        == Decimal("100.01")
    )


def test_analysis_calculates_bookmaker_overround() -> None:
    analysis = MarketValueAnalyzer().analyze(
        create_odds(),
        create_public_percentages(),
    )

    assert (
        analysis.overround_percentage_points
        == Decimal("3.57")
    )


def test_analysis_preserves_official_outcome_order() -> None:
    analysis = MarketValueAnalyzer().analyze(
        create_odds(),
        create_public_percentages(),
    )

    assert tuple(
        value.outcome
        for value in analysis.outcome_values
    ) == Outcome.ordered()


def test_analysis_calculates_percentage_point_edges() -> None:
    analysis = MarketValueAnalyzer().analyze(
        create_odds(),
        create_public_percentages(),
    )

    assert (
        analysis.for_outcome(
            Outcome.HOME
        ).edge_percentage_points
        == Decimal("-6.72")
    )
    assert (
        analysis.for_outcome(
            Outcome.DRAW
        ).edge_percentage_points
        == Decimal("2.59")
    )
    assert (
        analysis.for_outcome(
            Outcome.AWAY
        ).edge_percentage_points
        == Decimal("4.14")
    )


def test_analysis_identifies_positive_value_outcomes() -> None:
    analysis = MarketValueAnalyzer().analyze(
        create_odds(),
        create_public_percentages(),
    )

    assert tuple(
        value.outcome
        for value in analysis.positive_value_outcomes
    ) == (
        Outcome.DRAW,
        Outcome.AWAY,
    )


def test_analysis_identifies_best_value_outcome() -> None:
    analysis = MarketValueAnalyzer().analyze(
        create_odds(),
        create_public_percentages(),
    )

    assert (
        analysis.best_value.outcome
        is Outcome.AWAY
    )
    assert (
        analysis.best_value.value_index
        == Decimal("120.70")
    )


def test_analysis_uses_none_when_public_percentage_is_zero() -> None:
    public_percentages = ThreeWayPercentages(
        home=Decimal("80"),
        draw=Decimal("20"),
        away=Decimal("0"),
    )

    analysis = MarketValueAnalyzer().analyze(
        create_odds(),
        public_percentages,
    )

    away_value = analysis.for_outcome(
        Outcome.AWAY
    )

    assert away_value.value_index is None
    assert away_value.has_positive_value is True


def test_analyzer_rejects_invalid_odds_type() -> None:
    with pytest.raises(
        TypeError,
        match="requires ThreeWayOdds",
    ):
        MarketValueAnalyzer().analyze(
            object(),  # type: ignore[arg-type]
            create_public_percentages(),
        )


def test_analyzer_rejects_invalid_percentage_type() -> None:
    with pytest.raises(
        TypeError,
        match="requires ThreeWayPercentages",
    ):
        MarketValueAnalyzer().analyze(
            create_odds(),
            object(),  # type: ignore[arg-type]
        )