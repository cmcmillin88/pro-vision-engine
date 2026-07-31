"""Tests for strict practical reduction-configuration JSON import."""

import json
from copy import deepcopy
from decimal import Decimal

import pytest

from src.importer.reduction_configuration_json_importer import (
    ReductionConfigurationJsonImporter,
)
from src.models.color_reduction_rule import ReductionColor
from src.models.game_type import GameType
from src.models.outcome import Outcome
from src.models.reduction_configuration_document import (
    MarketSnapshotSelection,
)
from tests.coupon_analysis_run_helpers import (
    create_analysis_run,
)
from tests.reduction_configuration_helpers import (
    EXAMPLE_PATH,
    create_full_payload,
    load_example_payload,
)


def test_importer_loads_complete_example_file() -> None:
    document = ReductionConfigurationJsonImporter().from_file(
        EXAMPLE_PATH,
        create_analysis_run(),
    )

    assert document.condition_count == 3
    assert document.atomic_condition_count == 5


def test_importer_records_file_source_name() -> None:
    document = ReductionConfigurationJsonImporter().from_file(
        EXAMPLE_PATH,
        create_analysis_run(),
    )

    assert document.source_name == str(
        EXAMPLE_PATH
    )


def test_importer_supports_json_text() -> None:
    text = EXAMPLE_PATH.read_text(
        encoding="utf-8"
    )

    document = ReductionConfigurationJsonImporter().from_json(
        text,
        create_analysis_run(),
        source_name="inline.json",
    )

    assert document.source_name == "inline.json"


def test_importer_supports_all_five_condition_groups() -> None:
    run = create_analysis_run()

    document = ReductionConfigurationJsonImporter().from_dict(
        create_full_payload(
            run
        ),
        run,
    )

    assert document.condition_count == 5
    assert document.atomic_condition_count == 8


def test_importer_builds_multiple_color_rules() -> None:
    run = create_analysis_run()
    document = ReductionConfigurationJsonImporter().from_dict(
        create_full_payload(
            run
        ),
        run,
    )

    assert tuple(
        rule.color
        for rule in document.condition_set.color_rules
    ) == (
        ReductionColor.RED,
        ReductionColor.YELLOW,
    )


def test_importer_builds_one_x_two_conditions_in_official_order() -> None:
    document = ReductionConfigurationJsonImporter().from_file(
        EXAMPLE_PATH,
        create_analysis_run(),
    )
    rule = document.condition_set.one_x_two_rule

    assert rule is not None
    assert rule.outcomes == Outcome.ordered()
    assert rule.condition_pattern == "1 0/8 | X 0/8 | 2 0/8"


def test_importer_builds_frame_bound_point_assignments() -> None:
    run = create_analysis_run()
    document = ReductionConfigurationJsonImporter().from_dict(
        create_full_payload(
            run
        ),
        run,
    )
    rule = document.condition_set.point_rule

    assert rule is not None
    assert rule.assignment_count == 3
    assert rule.maximum_possible_points == 12


def test_importer_freezes_later_odds_from_analysis_input() -> None:
    run = create_analysis_run()
    document = ReductionConfigurationJsonImporter().from_file(
        EXAMPLE_PATH,
        run,
    )
    rule = document.condition_set.odds_rule

    assert rule is not None
    assert rule.snapshot.match_odds == tuple(
        match.later_market_snapshot.odds
        for match in run.input_document.matches
    )
    assert rule.snapshot.captured_at == (
        run.input_document.matches[0]
        .later_market_snapshot.captured_at
    )


def test_importer_freezes_later_public_shares_for_payout() -> None:
    run = create_analysis_run()
    document = ReductionConfigurationJsonImporter().from_file(
        EXAMPLE_PATH,
        run,
    )
    rule = document.condition_set.payout_rule

    assert rule is not None
    assert rule.snapshot.match_percentages == tuple(
        match.later_market_snapshot.public_percentages
        for match in run.input_document.matches
    )
    assert rule.snapshot.method_version == "p13-public-share-v1"


def test_importer_supports_earlier_market_snapshot_selection() -> None:
    run = create_analysis_run()
    payload = load_example_payload()
    payload["conditions"]["odds"]["market_snapshot"] = "earlier"
    payload["conditions"]["payout"]["market_snapshot"] = "earlier"

    document = ReductionConfigurationJsonImporter().from_dict(
        payload,
        run,
    )

    assert (
        document.odds_snapshot_selection
        is MarketSnapshotSelection.EARLIER
    )
    assert (
        document.payout_snapshot_selection
        is MarketSnapshotSelection.EARLIER
    )
    assert (
        document.condition_set.odds_rule.snapshot.match_odds
        == tuple(
            match.earlier_market_snapshot.odds
            for match in run.input_document.matches
        )
    )


def test_importer_preserves_exact_decimal_values() -> None:
    document = ReductionConfigurationJsonImporter().from_file(
        EXAMPLE_PATH,
        create_analysis_run(),
    )

    assert document.row_price == Decimal("1.00")
    assert (
        document.condition_set.odds_rule.min_total_odds
        == Decimal("1.00")
    )
    assert (
        document.condition_set.payout_rule.snapshot.turnover
        == Decimal("1000000.00")
    )


def test_importer_accepts_numeric_json_values() -> None:
    payload = load_example_payload()
    payload["row_price"] = 2
    payload["conditions"]["odds"]["min"] = 1
    payload["conditions"]["payout"]["turnover"] = 1000000

    document = ReductionConfigurationJsonImporter().from_dict(
        payload,
        create_analysis_run(),
    )

    assert document.row_price == Decimal("2.00")


def test_importer_accepts_optional_target_fields_as_null() -> None:
    payload = load_example_payload()
    payload["target"]["coupon_id"] = None
    payload["target"]["frame_pattern"] = None

    document = ReductionConfigurationJsonImporter().from_dict(
        payload,
        create_analysis_run(),
    )

    assert document.target_coupon_id is None
    assert document.expected_frame_pattern is None


def test_importer_rejects_missing_file() -> None:
    with pytest.raises(
        FileNotFoundError,
    ):
        ReductionConfigurationJsonImporter().from_file(
            "examples/missing-reduction-config.json",
            create_analysis_run(),
        )


def test_importer_rejects_invalid_analysis_run_type() -> None:
    with pytest.raises(
        TypeError,
        match="CouponAnalysisRun",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            load_example_payload(),
            object(),  # type: ignore[arg-type]
        )


def test_importer_rejects_empty_json_text() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        ReductionConfigurationJsonImporter().from_json(
            "   ",
            create_analysis_run(),
        )


def test_importer_rejects_invalid_json_text() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid reduction-configuration JSON",
    ):
        ReductionConfigurationJsonImporter().from_json(
            "{invalid",
            create_analysis_run(),
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "parent_key",
    ),
    (
        (
            "extra",
            None,
        ),
        (
            "extra",
            "target",
        ),
        (
            "extra",
            "conditions",
        ),
    ),
)
def test_importer_rejects_unknown_fields(
    field_name: str,
    parent_key: str | None,
) -> None:
    payload = load_example_payload()

    if parent_key is None:
        payload[field_name] = True
    else:
        payload[parent_key][field_name] = True

    with pytest.raises(
        ValueError,
        match="unknown field",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "schema_version",
        "target",
        "row_price",
        "conditions",
    ),
)
def test_importer_rejects_missing_top_level_fields(
    field_name: str,
) -> None:
    payload = load_example_payload()
    del payload[field_name]

    with pytest.raises(
        ValueError,
        match="missing field",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_empty_condition_object() -> None:
    payload = load_example_payload()
    payload["conditions"] = {}

    with pytest.raises(
        ValueError,
        match="at least one condition group",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_wrong_target_game_type() -> None:
    payload = load_example_payload()
    payload["target"]["game_type"] = "stryktipset"

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_wrong_target_coupon_id() -> None:
    payload = load_example_payload()
    payload["target"]["coupon_id"] = "WRONG"

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_wrong_frame_pattern() -> None:
    payload = load_example_payload()
    payload["target"]["frame_pattern"] = "INVALID-FRAME-PATTERN"

    with pytest.raises(
        ValueError,
        match="turquoise frame",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_unsupported_schema_version() -> None:
    payload = load_example_payload()
    payload["schema_version"] = "p13-reduction-input-v2"

    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_duplicate_colors() -> None:
    run = create_analysis_run()
    payload = create_full_payload(
        run
    )
    payload["conditions"]["colors"][1]["color"] = "red"

    with pytest.raises(
        ValueError,
        match="each color",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            run,
        )


def test_importer_rejects_unknown_color() -> None:
    run = create_analysis_run()
    payload = create_full_payload(
        run
    )
    payload["conditions"]["colors"][0]["color"] = "turquoise"

    with pytest.raises(
        ValueError,
        match="expected one of",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            run,
        )


def test_importer_rejects_cell_outside_match_count() -> None:
    run = create_analysis_run()
    payload = create_full_payload(
        run
    )
    payload["conditions"]["colors"][0]["cells"][0]["match"] = 9

    with pytest.raises(
        ValueError,
        match="outside the turquoise frame",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            run,
        )


def test_importer_rejects_outcome_outside_frame() -> None:
    run = create_analysis_run()
    target_match = None
    missing_outcome = None

    for match_number in range(
        1,
        run.match_count + 1,
    ):
        allowed = set(
            run.reduction_frame.allowed_for_match(
                match_number
            )
        )
        for outcome in Outcome.ordered():
            if outcome not in allowed:
                target_match = match_number
                missing_outcome = outcome
                break
        if target_match is not None:
            break

    if target_match is None or missing_outcome is None:
        pytest.skip(
            "Example frame contains all outcomes in every match."
        )

    payload = create_full_payload(
        run
    )
    payload["conditions"]["colors"][0]["cells"][0] = {
        "match": target_match,
        "outcome": missing_outcome.value,
    }

    with pytest.raises(
        ValueError,
        match="outside the turquoise frame",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            run,
        )


def test_importer_rejects_invalid_outcome_symbol() -> None:
    run = create_analysis_run()
    payload = create_full_payload(
        run
    )
    payload["conditions"]["points"]["assignments"][0][
        "outcome"
    ] = "A"

    with pytest.raises(
        ValueError,
        match="expected 1, X or 2",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            run,
        )


def test_importer_rejects_one_x_two_max_above_match_count() -> None:
    payload = load_example_payload()
    payload["conditions"]["one_x_two"]["1"]["max"] = 9

    with pytest.raises(
        ValueError,
        match="exceeds",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_empty_one_x_two_rule() -> None:
    payload = load_example_payload()
    payload["conditions"]["one_x_two"] = {}

    with pytest.raises(
        ValueError,
        match="at least one outcome interval",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_empty_color_rules() -> None:
    payload = load_example_payload()
    payload["conditions"]["colors"] = []

    with pytest.raises(
        ValueError,
        match="at least one color rule",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_empty_point_assignments() -> None:
    run = create_analysis_run()
    payload = create_full_payload(
        run
    )
    payload["conditions"]["points"]["assignments"] = []

    with pytest.raises(
        ValueError,
        match="at least one assignment",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            run,
        )


@pytest.mark.parametrize(
    "selection",
    (
        "current",
        "latest",
        "",
    ),
)
def test_importer_rejects_invalid_market_snapshot_selection(
    selection: str,
) -> None:
    payload = load_example_payload()
    payload["conditions"]["odds"]["market_snapshot"] = selection

    with pytest.raises(
        (ValueError, TypeError),
        match="earlier or later",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_non_numeric_row_price() -> None:
    payload = load_example_payload()
    payload["row_price"] = "one krona"

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_boolean_numeric_value() -> None:
    payload = load_example_payload()
    payload["conditions"]["odds"]["min"] = True

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_point_value_above_99() -> None:
    run = create_analysis_run()
    payload = create_full_payload(
        run
    )
    payload["conditions"]["points"]["assignments"][0][
        "points"
    ] = 100

    with pytest.raises(
        ValueError,
        match="between 1 and 99",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            run,
        )


def test_importer_rejects_duplicate_point_cells() -> None:
    run = create_analysis_run()
    payload = create_full_payload(
        run
    )
    duplicate = deepcopy(
        payload["conditions"]["points"]["assignments"][0]
    )
    payload["conditions"]["points"]["assignments"].append(
        duplicate
    )

    with pytest.raises(
        ValueError,
        match="duplicate",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            run,
        )


def test_importer_rejects_invalid_odds_interval() -> None:
    payload = load_example_payload()
    payload["conditions"]["odds"]["min"] = "10"
    payload["conditions"]["odds"]["max"] = "10"

    with pytest.raises(
        ValueError,
        match="greater than",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )


def test_importer_rejects_invalid_payout_interval() -> None:
    payload = load_example_payload()
    payload["conditions"]["payout"]["min"] = "500"
    payload["conditions"]["payout"]["max"] = "400"

    with pytest.raises(
        ValueError,
        match="greater than",
    ):
        ReductionConfigurationJsonImporter().from_dict(
            payload,
            create_analysis_run(),
        )