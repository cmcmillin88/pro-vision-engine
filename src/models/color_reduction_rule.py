"""Models for one color-based MIN/MAX reduction rule."""

from dataclasses import dataclass
from enum import Enum

from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow


class ReductionColor(str, Enum):
    """Represents one supported reduction color."""

    RED = "red"
    YELLOW = "yellow"
    BLUE = "blue"
    PINK = "pink"
    PURPLE = "purple"
    GREEN = "green"

    @property
    def display_name(self) -> str:
        """Return the Swedish display name."""

        names = {
            ReductionColor.RED: "Röd",
            ReductionColor.YELLOW: "Gul",
            ReductionColor.BLUE: "Blå",
            ReductionColor.PINK: "Rosa",
            ReductionColor.PURPLE: "Lila",
            ReductionColor.GREEN: "Grön",
        }

        return names[self]


@dataclass(frozen=True, slots=True)
class ColoredOutcomeCell:
    """Represents one color-marked match and outcome cell."""

    match_number: int
    outcome: Outcome

    def __post_init__(self) -> None:
        """Validate one marked outcome cell."""

        if isinstance(self.match_number, bool) or not isinstance(
            self.match_number,
            int,
        ):
            raise TypeError(
                "match_number must be an integer."
            )

        if self.match_number <= 0:
            raise ValueError(
                "match_number must be greater than zero."
            )

        if not isinstance(self.outcome, Outcome):
            raise TypeError(
                "outcome must be an Outcome."
            )

    @property
    def key(self) -> tuple[int, Outcome]:
        """Return the unique cell identity."""

        return (
            self.match_number,
            self.outcome,
        )

    def __str__(self) -> str:
        """Return a compact cell representation."""

        return (
            f"{self.match_number}:"
            f"{self.outcome.value}"
        )


@dataclass(frozen=True, slots=True)
class ColorReductionRule:
    """Defines one independent color MIN/MAX condition."""

    color: ReductionColor
    cells: tuple[ColoredOutcomeCell, ...]
    min_hits: int
    max_hits: int

    def __post_init__(self) -> None:
        """Normalize and validate the complete color rule."""

        if not isinstance(self.color, ReductionColor):
            raise TypeError(
                "color must be a ReductionColor."
            )

        if not isinstance(self.cells, tuple):
            raise TypeError(
                "cells must be a tuple."
            )

        if not self.cells:
            raise ValueError(
                "A color rule must contain at least "
                "one marked cell."
            )

        for cell in self.cells:
            if not isinstance(cell, ColoredOutcomeCell):
                raise TypeError(
                    "cells may only contain "
                    "ColoredOutcomeCell objects."
                )

        cell_keys = tuple(
            cell.key
            for cell in self.cells
        )

        if len(set(cell_keys)) != len(cell_keys):
            raise ValueError(
                "A color rule must not contain "
                "duplicate marked cells."
            )

        for field_name in (
            "min_hits",
            "max_hits",
        ):
            value = getattr(
                self,
                field_name,
            )

            if isinstance(value, bool) or not isinstance(
                value,
                int,
            ):
                raise TypeError(
                    f"{field_name} must be an integer."
                )

            if value < 0:
                raise ValueError(
                    f"{field_name} must not be negative."
                )

        if self.min_hits > self.max_hits:
            raise ValueError(
                "min_hits must not exceed max_hits."
            )

        marked_match_count = len(
            {
                cell.match_number
                for cell in self.cells
            }
        )

        if self.max_hits > marked_match_count:
            raise ValueError(
                "max_hits must not exceed the number "
                "of distinct marked matches."
            )

        official_index = {
            outcome: index
            for index, outcome in enumerate(
                Outcome.ordered()
            )
        }

        ordered_cells = tuple(
            sorted(
                self.cells,
                key=lambda cell: (
                    cell.match_number,
                    official_index[cell.outcome],
                ),
            )
        )

        object.__setattr__(
            self,
            "cells",
            ordered_cells,
        )

    @property
    def cell_count(self) -> int:
        """Return the number of marked cells."""

        return len(self.cells)

    @property
    def marked_match_numbers(self) -> tuple[int, ...]:
        """Return unique marked matches in coupon order."""

        return tuple(
            sorted(
                {
                    cell.match_number
                    for cell in self.cells
                }
            )
        )

    @property
    def marked_match_count(self) -> int:
        """Return the number of distinct marked matches."""

        return len(
            self.marked_match_numbers
        )

    @property
    def maximum_possible_hits(self) -> int:
        """Return the maximum hits one row can receive."""

        return self.marked_match_count

    @property
    def condition_text(self) -> str:
        """Return compact inclusive MIN/MAX text."""

        return (
            f"{self.min_hits}/"
            f"{self.max_hits}"
        )

    def cells_for_match(
        self,
        match_number: int,
    ) -> tuple[Outcome, ...]:
        """Return all marked outcomes in one match."""

        self._validate_positive_match_number(
            match_number
        )

        return tuple(
            cell.outcome
            for cell in self.cells
            if cell.match_number == match_number
        )

    def hit_count(
        self,
        row: ReductionRow,
    ) -> int:
        """Count this color's hits across one complete row."""

        if not isinstance(row, ReductionRow):
            raise TypeError(
                "row must be a ReductionRow."
            )

        if self.marked_match_numbers[-1] > row.match_count:
            raise ValueError(
                "The row does not contain every match "
                "referenced by the color rule."
            )

        return sum(
            row.outcome_at(match_number)
            in self.cells_for_match(match_number)
            for match_number in self.marked_match_numbers
        )

    def is_approved(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether one row satisfies inclusive MIN/MAX."""

        hits = self.hit_count(row)

        return (
            self.min_hits
            <= hits
            <= self.max_hits
        )

    @staticmethod
    def _validate_positive_match_number(
        match_number: int,
    ) -> None:
        """Validate a positive one-based match number."""

        if isinstance(match_number, bool) or not isinstance(
            match_number,
            int,
        ):
            raise TypeError(
                "match_number must be an integer."
            )

        if match_number <= 0:
            raise ValueError(
                "match_number must be greater than zero."
            )