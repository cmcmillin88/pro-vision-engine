"""Tests for final complete reduction-report models."""

from dataclasses import replace
from decimal import Decimal
import json

import pytest

from src.models.final_reduction_report import (
    FinalReductionReport,
    ReductionConditionImpact,
    ReductionRejectionPattern,
)
from src.models.reduction_condition_set import (
    ReductionConditionType,
)
from tests.reduction_report_helpers import (
    create_report,
)


def test_condition_impact_exposes_percentages() -> None:
    impact = ReductionConditionImpact(
        condition_type=ReductionConditionType.POINT,
        original_row_count=27,
        independently_approved_count=8,
        independently_rejected_count=19,
        exclusive_rejection_count=1,
    )

    assert impact.display_name == "Poäng"
    assert impact.retained_percentage == Decimal("29.63")
    assert impact.reduction_percentage == Decimal("70.37")


def test_condition_impact_exposes_summary() -> None:
    impact = ReductionConditionImpact(
        condition_type=ReductionConditionType.ODDS,
        original_row_count=27,
        independently_approved_count=13,
        independently_rejected_count=14,
        exclusive_rejection_count=1,
    )

    assert impact.summary_line == (
        "Odds | Kvar 13 | Bort 14 | "
        "Ensamt avgörande 1 | Reducering 51.85%"
    )


def test_condition_impact_rejects_invalid_total() -> None:
    with pytest.raises(
        ValueError,
        match="equal original",
    ):
        ReductionConditionImpact(
            condition_type=ReductionConditionType.COLOR,
            original_row_count=27,
            independently_approved_count=9,
            independently_rejected_count=17,
            exclusive_rejection_count=1,
        )


def test_condition_impact_rejects_exclusive_above_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        ReductionConditionImpact(
            condition_type=ReductionConditionType.COLOR,
            original_row_count=27,
            independently_approved_count=27,
            independently_rejected_count=0,
            exclusive_rejection_count=1,
        )


def test_condition_impact_rejects_boolean_count() -> None:
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        ReductionConditionImpact(
            condition_type=ReductionConditionType.COLOR,
            original_row_count=True,  # type: ignore[arg-type]
            independently_approved_count=1,
            independently_rejected_count=0,
            exclusive_rejection_count=0,
        )


def test_rejection_pattern_exposes_text_and_percentage() -> None:
    pattern = ReductionRejectionPattern(
        condition_types=(
            ReductionConditionType.COLOR,
            ReductionConditionType.POINT,
        ),
        row_count=3,
        total_rejected_row_count=26,
    )

    assert pattern.pattern == "Färg + Poäng"
    assert pattern.percentage_of_rejected == Decimal("11.54")
    assert pattern.summary_line == (
        "Färg + Poäng | Rader 3 | "
        "Andel av borttagna 11.54%"
    )


def test_rejection_pattern_requires_official_order() -> None:
    with pytest.raises(
        ValueError,
        match="official",
    ):
        ReductionRejectionPattern(
            condition_types=(
                ReductionConditionType.POINT,
                ReductionConditionType.COLOR,
            ),
            row_count=1,
            total_rejected_row_count=1,
        )


def test_rejection_pattern_rejects_duplicates() -> None:
    with pytest.raises(
        ValueError,
        match="duplicates",
    ):
        ReductionRejectionPattern(
            condition_types=(
                ReductionConditionType.COLOR,
                ReductionConditionType.COLOR,
            ),
            row_count=1,
            total_rejected_row_count=1,
        )


def test_report_exposes_version_and_identity() -> None:
    report = create_report()

    assert report.report_version == "p13-reduction-report-v1"
    assert report.game_type.value == "topptipset"
    assert report.game_type_name == "Topptipset"
    assert report.coupon_id == "Komplett reduceringsrapport"


def test_report_exposes_frame_and_conditions() -> None:
    report = create_report()

    assert report.frame_pattern == (
        "1X2|1X2|1X2|1|1|1|1|1"
    )
    assert report.condition_count == 5
    assert report.atomic_condition_count == 8
    assert report.active_condition_types == (
        ReductionConditionType.COLOR,
        ReductionConditionType.ONE_X_TWO,
        ReductionConditionType.POINT,
        ReductionConditionType.ODDS,
        ReductionConditionType.PAYOUT,
    )


def test_report_exposes_final_counts() -> None:
    report = create_report()

    assert report.original_row_count == 27
    assert report.approved_count == 1
    assert report.rejected_count == 26
    assert report.retained_percentage == Decimal("3.70")
    assert report.reduction_percentage == Decimal("96.30")
    assert report.is_empty is False


def test_report_exposes_surviving_rows() -> None:
    report = create_report()

    assert report.approved_symbols == (
        "12X11111",
    )
    assert len(report.rejected_rows) == 26


def test_report_exposes_costs() -> None:
    report = create_report(
        row_price="1.004"
    )

    assert report.row_price == Decimal("1.00")
    assert report.original_cost == Decimal("27.00")
    assert report.final_cost == Decimal("1.00")
    assert report.saved_cost == Decimal("26.00")


def test_report_supports_unknown_row_price() -> None:
    report = create_report(
        row_price=None
    )

    assert report.row_price is None
    assert report.original_cost is None
    assert report.final_cost is None
    assert report.saved_cost is None
    assert "Kostnad" not in report.summary_line


def test_report_rejects_invalid_row_price() -> None:
    report = create_report()

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        replace(
            report,
            row_price="0",
        )


def test_report_exposes_condition_impacts() -> None:
    report = create_report()

    assert tuple(
        impact.independently_approved_count
        for impact in report.condition_impacts
    ) == (
        9,
        12,
        8,
        13,
        11,
    )

    assert tuple(
        impact.exclusive_rejection_count
        for impact in report.condition_impacts
    ) == (
        1,
        0,
        1,
        1,
        0,
    )


def test_report_identifies_strictest_condition() -> None:
    report = create_report()

    assert (
        report.strictest_condition.condition_type
        is ReductionConditionType.POINT
    )
    assert report.combination_removed_count == 7
    assert report.exclusive_rejection_total == 3


def test_report_condition_impact_lookup() -> None:
    report = create_report()

    assert report.condition_impact_for(
        ReductionConditionType.ODDS
    ).independently_approved_count == 13


def test_report_condition_impact_lookup_rejects_inactive() -> None:
    report = create_report()
    reduced_report = FinalReductionReport(
        condition_result=report.condition_result,
        condition_impacts=report.condition_impacts,
        rejection_patterns=report.rejection_patterns,
    )

    with pytest.raises(
        TypeError,
        match="ReductionConditionType",
    ):
        reduced_report.condition_impact_for(
            object()  # type: ignore[arg-type]
        )


def test_report_exposes_rejection_patterns() -> None:
    report = create_report()

    assert len(report.rejection_patterns) == 16
    assert report.rejection_patterns[0].row_count == 5
    assert report.rejection_patterns[0].condition_types == (
        ReductionConditionType.COLOR,
        ReductionConditionType.ONE_X_TWO,
        ReductionConditionType.POINT,
        ReductionConditionType.ODDS,
        ReductionConditionType.PAYOUT,
    )
    assert sum(
        pattern.row_count
        for pattern in report.rejection_patterns
    ) == 26


def test_report_exposes_frozen_market_metadata() -> None:
    report = create_report()

    assert report.uses_frozen_odds is True
    assert report.uses_estimated_payout is True
    assert report.frozen_sources == (
        "Testmarknad",
        "Testpool",
    )
    assert tuple(
        value.isoformat()
        for value in report.snapshot_times
    ) == (
        "2026-07-31T18:00:00+00:00",
        "2026-07-31T18:00:00+00:00",
    )
    assert report.payout_method_version == (
        "p13-public-share-v1"
    )


def test_report_exposes_summary_lines() -> None:
    report = create_report()

    assert report.summary_line == (
        "Topptipset | Villkor 5 | Ursprung 27 | "
        "Kvar 1 | Bort 26 | Reducering 96.30% | "
        "Kostnad 1.00 kr"
    )
    assert report.analysis_line == (
        "Striktast Poäng (8/27) | "
        "Kombinationseffekt 7 | Ensamt avgörande 3"
    )


def test_report_to_dict_is_json_safe() -> None:
    report = create_report()
    payload = report.to_dict()

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert "Komplett reduceringsrapport" in encoded
    assert payload["version"] == "p13-reduction-report-v1"
    assert payload["counts"] == {
        "original": 27,
        "approved": 1,
        "rejected": 26,
    }
    assert payload["approved_rows"] == [
        "12X11111"
    ]
    assert payload["costs"]["final_cost"] == "1.00"
    assert len(payload["snapshots"]) == 2


def test_report_rejects_changed_impact_order() -> None:
    report = create_report()

    with pytest.raises(
        ValueError,
        match="official order",
    ):
        replace(
            report,
            condition_impacts=tuple(
                reversed(
                    report.condition_impacts
                )
            ),
        )


def test_report_rejects_changed_impact_count() -> None:
    report = create_report()
    first = report.condition_impacts[0]

    changed = replace(
        first,
        independently_approved_count=(
            first.independently_approved_count - 1
        ),
        independently_rejected_count=(
            first.independently_rejected_count + 1
        ),
    )

    with pytest.raises(
        ValueError,
        match="approved count",
    ):
        replace(
            report,
            condition_impacts=(
                changed,
                *report.condition_impacts[1:],
            ),
        )


def test_report_rejects_changed_exclusive_count() -> None:
    report = create_report()
    first = report.condition_impacts[0]

    changed = replace(
        first,
        exclusive_rejection_count=0,
    )

    with pytest.raises(
        ValueError,
        match="exclusive rejection",
    ):
        replace(
            report,
            condition_impacts=(
                changed,
                *report.condition_impacts[1:],
            ),
        )


def test_report_rejects_missing_rejection_pattern() -> None:
    report = create_report()

    with pytest.raises(
        ValueError,
        match="exactly describe",
    ):
        replace(
            report,
            rejection_patterns=(
                report.rejection_patterns[:-1]
            ),
        )