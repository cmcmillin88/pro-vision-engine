"""Models for multiple independent color-reduction rules."""

from dataclasses import dataclass

from src.models.color_reduction_rule import (
    ColorReductionRule,
    ReductionColor,
)
from src.models.reduction_row import ReductionRow


@dataclass(frozen=True, slots=True)
class ColorReductionRuleSet:
    """Contains multiple unique color rules applied together."""

    rules: tuple[
        ColorReductionRule,
        ...,
    ]

    def __post_init__(self) -> None:
        """Normalize and validate the complete rule set."""

        if not isinstance(
            self.rules,
            tuple,
        ):
            raise TypeError(
                "rules must be a tuple."
            )

        if len(self.rules) < 2:
            raise ValueError(
                "A multi-color rule set requires "
                "at least two color rules."
            )

        if len(self.rules) > len(
            ReductionColor
        ):
            raise ValueError(
                "A rule set may not contain more "
                "rules than supported colors."
            )

        for rule in self.rules:
            if not isinstance(
                rule,
                ColorReductionRule,
            ):
                raise TypeError(
                    "rules may only contain "
                    "ColorReductionRule objects."
                )

        colors = tuple(
            rule.color
            for rule in self.rules
        )

        if len(
            set(
                colors
            )
        ) != len(
            colors
        ):
            raise ValueError(
                "Each reduction color may only appear "
                "once in a rule set."
            )

        color_order = {
            color: index
            for index, color in enumerate(
                ReductionColor
            )
        }

        ordered_rules = tuple(
            sorted(
                self.rules,
                key=lambda rule: color_order[
                    rule.color
                ],
            )
        )

        object.__setattr__(
            self,
            "rules",
            ordered_rules,
        )

    @property
    def rule_count(self) -> int:
        """Return the number of active color rules."""

        return len(
            self.rules
        )

    @property
    def colors(self) -> tuple[ReductionColor, ...]:
        """Return active colors in deterministic order."""

        return tuple(
            rule.color
            for rule in self.rules
        )

    @property
    def condition_pattern(self) -> str:
        """Return a compact description of all conditions."""

        return " | ".join(
            (
                f"{rule.color.display_name} "
                f"{rule.min_hits}/{rule.max_hits}"
            )
            for rule in self.rules
        )

    def rule_for_color(
        self,
        color: ReductionColor,
    ) -> ColorReductionRule:
        """Return the rule for one active color."""

        self._validate_color(
            color
        )

        for rule in self.rules:
            if rule.color is color:
                return rule

        raise KeyError(
            f"No rule exists for color {color.value}."
        )

    def hit_counts(
        self,
        row: ReductionRow,
    ) -> tuple[int, ...]:
        """Return each color's independent hit count."""

        self._validate_row(
            row
        )

        return tuple(
            rule.hit_count(
                row
            )
            for rule in self.rules
        )

    def approval_states(
        self,
        row: ReductionRow,
    ) -> tuple[bool, ...]:
        """Return each color's independent approval state."""

        self._validate_row(
            row
        )

        return tuple(
            rule.is_approved(
                row
            )
            for rule in self.rules
        )

    def is_approved(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether every active color approves the row."""

        return all(
            self.approval_states(
                row
            )
        )

    @staticmethod
    def _validate_color(
        color: object,
    ) -> None:
        """Validate one reduction color."""

        if not isinstance(
            color,
            ReductionColor,
        ):
            raise TypeError(
                "color must be a ReductionColor."
            )

    @staticmethod
    def _validate_row(
        row: object,
    ) -> None:
        """Validate one reduction row."""

        if not isinstance(
            row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )