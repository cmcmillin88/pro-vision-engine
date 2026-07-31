"""One mathematical 1-X-2 row in a reduction system."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.outcome import Outcome


@dataclass(frozen=True, slots=True)
class ReductionRow:
    """Represents one complete football-pool result row."""

    outcomes: tuple[
        Outcome,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate the complete immutable row."""

        if not isinstance(
            self.outcomes,
            tuple,
        ):
            raise TypeError(
                "outcomes must be a tuple."
            )

        if not self.outcomes:
            raise ValueError(
                "A reduction row must contain "
                "at least one outcome."
            )

        for outcome in self.outcomes:
            if not isinstance(
                outcome,
                Outcome,
            ):
                raise TypeError(
                    "outcomes may only contain "
                    "Outcome values."
                )

    @classmethod
    def from_symbols(
        cls,
        symbols: str,
    ) -> "ReductionRow":
        """Create a row from compact 1-X-2 symbols."""

        if not isinstance(
            symbols,
            str,
        ):
            raise TypeError(
                "symbols must be a string."
            )

        normalized_symbols = "".join(
            symbols.split()
        ).upper()

        if not normalized_symbols:
            raise ValueError(
                "symbols must not be empty."
            )

        return cls(
            outcomes=tuple(
                Outcome.parse(
                    symbol
                )
                for symbol in normalized_symbols
            )
        )

    @property
    def match_count(self) -> int:
        """Return the number of matches in the row."""

        return len(
            self.outcomes
        )

    @property
    def symbols(self) -> str:
        """Return the row as compact 1-X-2 symbols."""

        return "".join(
            outcome.value
            for outcome in self.outcomes
        )

    def outcome_at(
        self,
        match_number: int,
    ) -> Outcome:
        """Return the outcome at a one-based match number."""

        self._validate_match_number(
            match_number
        )

        return self.outcomes[
            match_number - 1
        ]

    def count(
        self,
        outcome: Outcome | str,
    ) -> int:
        """Return how often one outcome occurs."""

        resolved_outcome = Outcome.parse(
            outcome
        )

        return self.outcomes.count(
            resolved_outcome
        )

    def hamming_distance(
        self,
        other: "ReductionRow",
    ) -> int:
        """Return the number of differing match positions."""

        if not isinstance(
            other,
            ReductionRow,
        ):
            raise TypeError(
                "other must be a ReductionRow."
            )

        if self.match_count != other.match_count:
            raise ValueError(
                "Rows must contain the same number "
                "of matches."
            )

        return sum(
            own_outcome is not other_outcome
            for own_outcome, other_outcome in zip(
                self.outcomes,
                other.outcomes,
                strict=True,
            )
        )

    def _validate_match_number(
        self,
        match_number: int,
    ) -> None:
        """Validate a one-based match number."""

        if isinstance(
            match_number,
            bool,
        ) or not isinstance(
            match_number,
            int,
        ):
            raise TypeError(
                "match_number must be an integer."
            )

        if not (
            1
            <= match_number
            <= self.match_count
        ):
            raise IndexError(
                "match_number is outside the row."
            )

    def __str__(self) -> str:
        """Return compact row symbols."""

        return self.symbols