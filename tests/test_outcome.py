"""Tests for 1-X-2 outcomes."""

import pytest

from src.models.outcome import Outcome


def test_outcomes_follow_official_order() -> None:
    assert Outcome.ordered() == (
        Outcome.HOME,
        Outcome.DRAW,
        Outcome.AWAY,
    )


@pytest.mark.parametrize(
    ("outcome", "display_name"),
    [
        (Outcome.HOME, "Home win"),
        (Outcome.DRAW, "Draw"),
        (Outcome.AWAY, "Away win"),
    ],
)
def test_outcomes_have_display_names(
    outcome: Outcome,
    display_name: str,
) -> None:
    assert outcome.display_name == display_name


@pytest.mark.parametrize(
    ("raw_value", "expected_outcome"),
    [
        ("1", Outcome.HOME),
        ("x", Outcome.DRAW),
        (" 2 ", Outcome.AWAY),
        (Outcome.DRAW, Outcome.DRAW),
    ],
)
def test_outcome_parse_normalizes_values(
    raw_value: str | Outcome,
    expected_outcome: Outcome,
) -> None:
    assert Outcome.parse(raw_value) is expected_outcome


def test_outcome_parse_rejects_unknown_symbol() -> None:
    with pytest.raises(
        ValueError,
        match="Unknown 1-X-2 outcome",
    ):
        Outcome.parse("H")