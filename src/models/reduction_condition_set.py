"""Models for combining deterministic reduction conditions."""

from dataclasses import dataclass
from enum import Enum

from src.models.color_reduction_rule import (
    ColorReductionRule,
)
from src.models.color_reduction_rule_set import (
    ColorReductionRuleSet,
)
from src.models.odds_reduction_rule import (
    OddsReductionRule,
)
from src.models.one_x_two_reduction_rule import (
    OneXTwoReductionRule,
)
from src.models.payout_reduction_rule import (
    PayoutReductionRule,
)
from src.models.point_reduction_rule import (
    PointReductionRule,
)
from src.models.reduction_row import ReductionRow


class ReductionConditionType(str, Enum):
    """Represents one supported reduction-condition group."""

    COLOR = "color"
    ONE_X_TWO = "one_x_two"
    POINT = "point"
    ODDS = "odds"
    PAYOUT = "payout"

    @classmethod
    def ordered(
        cls,
    ) -> tuple["ReductionConditionType", ...]:
        """Return condition groups in deterministic order."""

        return (
            cls.COLOR,
            cls.ONE_X_TWO,
            cls.POINT,
            cls.ODDS,
            cls.PAYOUT,
        )

    @property
    def display_name(self) -> str:
        """Return the Swedish display name."""

        return {
            ReductionConditionType.COLOR: "Färg",
            ReductionConditionType.ONE_X_TWO: "1X2",
            ReductionConditionType.POINT: "Poäng",
            ReductionConditionType.ODDS: "Odds",
            ReductionConditionType.PAYOUT: "Utdelning",
        }[self]


@dataclass(frozen=True, slots=True)
class ReductionConditionSet:
    """Contains all active deterministic reduction conditions."""

    color_rule: ColorReductionRule | None = None
    color_rule_set: ColorReductionRuleSet | None = None
    one_x_two_rule: OneXTwoReductionRule | None = None
    point_rule: PointReductionRule | None = None
    odds_rule: OddsReductionRule | None = None
    payout_rule: PayoutReductionRule | None = None

    def __post_init__(self) -> None:
        """Validate the complete condition set."""

        if (
            self.color_rule is not None
            and not isinstance(
                self.color_rule,
                ColorReductionRule,
            )
        ):
            raise TypeError(
                "color_rule must be a ColorReductionRule."
            )

        if (
            self.color_rule_set is not None
            and not isinstance(
                self.color_rule_set,
                ColorReductionRuleSet,
            )
        ):
            raise TypeError(
                "color_rule_set must be a "
                "ColorReductionRuleSet."
            )

        if (
            self.one_x_two_rule is not None
            and not isinstance(
                self.one_x_two_rule,
                OneXTwoReductionRule,
            )
        ):
            raise TypeError(
                "one_x_two_rule must be a "
                "OneXTwoReductionRule."
            )

        if (
            self.point_rule is not None
            and not isinstance(
                self.point_rule,
                PointReductionRule,
            )
        ):
            raise TypeError(
                "point_rule must be a PointReductionRule."
            )

        if (
            self.odds_rule is not None
            and not isinstance(
                self.odds_rule,
                OddsReductionRule,
            )
        ):
            raise TypeError(
                "odds_rule must be an OddsReductionRule."
            )

        if (
            self.payout_rule is not None
            and not isinstance(
                self.payout_rule,
                PayoutReductionRule,
            )
        ):
            raise TypeError(
                "payout_rule must be a PayoutReductionRule."
            )

        if (
            self.color_rule is not None
            and self.color_rule_set is not None
        ):
            raise ValueError(
                "Use either color_rule or color_rule_set, "
                "not both."
            )

        if not self.condition_types:
            raise ValueError(
                "A reduction condition set requires at "
                "least one active condition."
            )

    @property
    def condition_types(
        self,
    ) -> tuple[ReductionConditionType, ...]:
        """Return active condition groups in official order."""

        active: list[ReductionConditionType] = []

        if self.has_color_condition:
            active.append(
                ReductionConditionType.COLOR
            )

        if self.one_x_two_rule is not None:
            active.append(
                ReductionConditionType.ONE_X_TWO
            )

        if self.point_rule is not None:
            active.append(
                ReductionConditionType.POINT
            )

        if self.odds_rule is not None:
            active.append(
                ReductionConditionType.ODDS
            )

        if self.payout_rule is not None:
            active.append(
                ReductionConditionType.PAYOUT
            )

        return tuple(
            active
        )

    @property
    def condition_count(self) -> int:
        """Return the number of active condition groups."""

        return len(
            self.condition_types
        )

    @property
    def has_color_condition(self) -> bool:
        """Return whether one or more color rules are active."""

        return (
            self.color_rule is not None
            or self.color_rule_set is not None
        )

    @property
    def color_rules(
        self,
    ) -> tuple[ColorReductionRule, ...]:
        """Return active color rules in deterministic order."""

        if self.color_rule is not None:
            return (
                self.color_rule,
            )

        if self.color_rule_set is not None:
            return self.color_rule_set.rules

        return ()

    @property
    def color_rule_count(self) -> int:
        """Return the number of active color rules."""

        return len(
            self.color_rules
        )

    @property
    def atomic_condition_count(self) -> int:
        """Return all independently checked conditions."""

        total = self.color_rule_count

        if self.one_x_two_rule is not None:
            total += (
                self.one_x_two_rule.condition_count
            )

        if self.point_rule is not None:
            total += 1

        if self.odds_rule is not None:
            total += 1

        if self.payout_rule is not None:
            total += 1

        return total

    @property
    def condition_pattern(self) -> str:
        """Return a compact description of every condition."""

        sections: list[str] = []

        if self.color_rules:
            color_text = " + ".join(
                (
                    f"{rule.color.display_name} "
                    f"{rule.condition_text}"
                )
                for rule in self.color_rules
            )

            sections.append(
                f"Färg {color_text}"
            )

        if self.one_x_two_rule is not None:
            sections.append(
                f"1X2 "
                f"{self.one_x_two_rule.condition_pattern}"
            )

        if self.point_rule is not None:
            sections.append(
                f"Poäng {self.point_rule.condition_text}"
            )

        if self.odds_rule is not None:
            sections.append(
                f"Odds {self.odds_rule.condition_text}"
            )

        if self.payout_rule is not None:
            sections.append(
                "Utdelning "
                f"{self.payout_rule.condition_text}"
            )

        return " | ".join(
            sections
        )

    def is_approved(
        self,
        row: ReductionRow,
    ) -> bool:
        """Return whether every active condition approves."""

        if not isinstance(
            row,
            ReductionRow,
        ):
            raise TypeError(
                "row must be a ReductionRow."
            )

        approval_states: list[bool] = []

        if self.color_rules:
            approval_states.append(
                all(
                    rule.is_approved(
                        row
                    )
                    for rule in self.color_rules
                )
            )

        if self.one_x_two_rule is not None:
            approval_states.append(
                self.one_x_two_rule.is_approved(
                    row
                )
            )

        if self.point_rule is not None:
            approval_states.append(
                self.point_rule.is_approved(
                    row
                )
            )

        if self.odds_rule is not None:
            approval_states.append(
                self.odds_rule.is_approved(
                    row
                )
            )

        if self.payout_rule is not None:
            approval_states.append(
                self.payout_rule.is_approved(
                    row
                )
            )

        return all(
            approval_states
        )