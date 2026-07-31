"""Models for deterministic point reduction rules."""

from dataclasses import dataclass

from src.models.outcome import Outcome
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class PointAssignment:
    """Assigns 1-99 points to one match-outcome cell."""

    match_number: int
    outcome: Outcome
    points: int

    def __post_init__(self) -> None:
        """Validate one point assignment."""

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

        if not isinstance(
            self.outcome,
            Outcome,
        ):
            raise TypeError(
                "outcome must be an Outcome."
            )

        if isinstance(self.points, bool) or not isinstance(
            self.points,
            int,
        ):
            raise TypeError(
                "points must be an integer."
            )

        if not 1 <= self.points <= 99:
            raise ValueError(
                "points must be between 1 and 99."
            )

    @property
    def key(self) -> tuple[int, Outcome]:
        """Return the unique marked-cell identity."""

        return (
            self.match_number,
            self.outcome,
        )

    def __str__(self) -> str:
        """Return compact assignment text."""

        return (
            f"{self.match_number}:"
            f"{self.outcome.value}="
            f"{self.points}"
        )


@dataclass(frozen=True, slots=True)
class PointReductionRule:
    """Defines assignments and an inclusive total-points interval."""

    assignments: tuple[
        PointAssignment,
        ...,
    ]
    min_points: int
    max_points: int

    def __post_init__(self) -> None:
        """Normalize and validate the complete point rule."""

        if not isinstance(
            self.assignments,
            tuple,
        ):
            raise TypeError(
                "assignments must be a tuple."
            )

        if not self.assignments:
            raise ValueError(
                "A point-reduction rule requires at "
                "least one point assignment."
            )

        for assignment in self.assignments:
            if not isinstance(
                assignment,
                PointAssignment,
            ):
                raise TypeError(
                    "assignments may only contain "
                    "PointAssignment objects."
                )

        assignment_keys = tuple(
            assignment.key
            for assignment in self.assignments
        )

        if len(
            set(
                assignment_keys
            )
        ) != len(
            assignment_keys
        ):
            raise ValueError(
                "A point-reduction rule must not contain "
                "duplicate match-outcome cells."
            )

        for field_name in (
            "min_points",
            "max_points",
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

        if self.min_points > self.max_points:
            raise ValueError(
                "min_points must not exceed max_points."
            )

        maximum_by_match: dict[int, int] = {}

        for assignment in self.assignments:
            maximum_by_match[
                assignment.match_number
            ] = max(
                maximum_by_match.get(
                    assignment.match_number,
                    0,
                ),
                assignment.points,
            )

        maximum_possible_points = sum(
            maximum_by_match.values()
        )

        if self.max_points > maximum_possible_points:
            raise ValueError(
                "max_points must not exceed the rule's "
                "maximum possible points."
            )

        official_index = {
            outcome: index
            for index, outcome in enumerate(
                Outcome.ordered()
            )
        }

        ordered_assignments = tuple(
            sorted(
                self.assignments,
                key=lambda assignment: (
                    assignment.match_number,
                    official_index[
                        assignment.outcome
                    ],
                ),
            )
        )

        object.__setattr__(
            self,
            "assignments",
            ordered_assignments,
        )

    @property
    def assignment_count(self) -> int:
        """Return the number of point-marked cells."""

        return len(
            self.assignments
        )

    @property
    def marked_match_numbers(self) -> tuple[int, ...]:
        """Return unique point-marked matches."""

        return tuple(
            sorted(
                {
                    assignment.match_number
                    for assignment in self.assignments
                }
            )
        )

    @property
    def marked_match_count(self) -> int:
        """Return the number of point-marked matches."""

        return len(
            self.marked_match_numbers
        )

    @property
    def maximum_possible_points(self) -> int:
        """Return the highest theoretical row total."""

        return sum(
            max(
                assignment.points
                for assignment in self.assignments
                if (
                    assignment.match_number
                    == match_number
                )
            )
            for match_number in self.marked_match_numbers
        )

    @property
    def condition_text(self) -> str:
        """Return compact inclusive MIN/MAX text."""

        return (
            f"{self.min_points}/"
            f"{self.max_points}"
        )

    def assignments_for_match(
        self,
        match_number: int,
    ) -> tuple[PointAssignment, ...]:
        """Return every point assignment in one match."""

        self._validate_positive_match_number(
            match_number
        )

        return tuple(
            assignment
            for assignment in self.assignments
            if (
                assignment.match_number
                == match_number
            )
        )

    def points_for(
        self,
        match_number: int,
        outcome: Outcome,
    ) -> int:
        """Return cell points, or zero for an unmarked cell."""

        self._validate_positive_match_number(
            match_number
        )

        if not isinstance(
            outcome,
            Outcome,
        ):
            raise TypeError(
                "outcome must be an Outcome."
            )

        for assignment in self.assignments_for_match(
            match_number
        ):
            if assignment.outcome is outcome:
                return assignment.points

        return 0

    def row_points(
        self,
        row: ReductionRow,
    ) -> int:
        """Add selected point-cell values across one row."""

        if not isinstance(
            row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        if (
            self.marked_match_numbers[-1]
            > row.match_count
        ):
            raise ValueError(
                "The row does not contain every match "
                "referenced by the point rule."
            )

        return sum(
            self.points_for(
                match_number,
                row.outcome_at(
                    match_number
                ),
            )
            for match_number in self.marked_match_numbers
        )

    def is_approved(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether row points satisfy inclusive MIN/MAX."""

        total_points = self.row_points(
            row
        )

        return (
            self.min_points
            <= total_points
            <= self.max_points
        )

    @staticmethod
    def _validate_positive_match_number(
        match_number: int,
    ) -> None:
        """Validate one positive one-based match number."""

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