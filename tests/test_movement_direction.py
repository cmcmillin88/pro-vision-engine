"""Tests for market movement directions."""

from decimal import Decimal

import pytest

from src.models.movement_direction import (
    MovementDirection,
)


@pytest.mark.parametrize(
    ("delta", "expected_direction"),
    [
        (
            Decimal("1.00"),
            MovementDirection.INCREASED,
        ),
        (
            Decimal("-1.00"),
            MovementDirection.DECREASED,
        ),
        (
            Decimal("0.00"),
            MovementDirection.UNCHANGED,
        ),
    ],
)
def test_direction_is_resolved_from_delta(
    delta: Decimal,
    expected_direction: MovementDirection,
) -> None:
    assert (
        MovementDirection.from_delta(delta)
        is expected_direction
    )