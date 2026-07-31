"""Tests for the practical coupon-reduction command-line interface."""

import json
from argparse import Namespace

import pytest

import reduce_coupon
from tests.coupon_reduction_run_helpers import (
    ANALYSIS_PATH,
    REDUCTION_PATH,
)


def create_arguments(**overrides) -> Namespace:
    """Create one complete CLI argument namespace."""

    values = {
        "analysis_path": ANALYSIS_PATH,
        "reduction_path": REDUCTION_PATH,
        "output_format": "console",
        "output_path": None,
        "compact": False,
        "max_rows": 20,
    }
    values.update(overrides)
    return Namespace(**values)


def test_parser_accepts_required_files() -> None:
    arguments = reduce_coupon.create_argument_parser().parse_args(
        [str(ANALYSIS_PATH), str(REDUCTION_PATH)]
    )

    assert arguments.analysis_path == ANALYSIS_PATH
    assert arguments.reduction_path == REDUCTION_PATH


def test_execute_creates_console_output(capsys) -> None:
    output = reduce_coupon.execute(create_arguments(max_rows=2))
    captured = capsys.readouterr()

    assert "Turkos ram:" in output
    assert output in captured.out


def test_execute_creates_json_output(capsys) -> None:
    output = reduce_coupon.execute(
        create_arguments(output_format="json")
    )
    captured = capsys.readouterr()

    assert json.loads(output)["schema_version"] == (
        "p13-reduction-result-v1"
    )
    assert output in captured.out


def test_execute_supports_compact_json() -> None:
    output = reduce_coupon.execute(
        create_arguments(
            output_format="json",
            compact=True,
        )
    )

    assert "\n" not in output


def test_execute_writes_utf8_output_file(tmp_path) -> None:
    output_path = tmp_path / "result" / "reduction.json"

    output = reduce_coupon.execute(
        create_arguments(
            output_format="json",
            output_path=output_path,
        )
    )

    assert output_path.read_text(encoding="utf-8") == output + "\n"


def test_main_returns_zero_for_valid_files(capsys) -> None:
    exit_code = reduce_coupon.main(
        [
            str(ANALYSIS_PATH),
            str(REDUCTION_PATH),
            "--max-rows",
            "1",
        ]
    )
    capsys.readouterr()

    assert exit_code == 0


def test_main_returns_one_for_missing_analysis_file(capsys) -> None:
    exit_code = reduce_coupon.main(
        [
            "examples/missing-analysis.json",
            str(REDUCTION_PATH),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Fel:" in captured.err


def test_main_returns_one_for_missing_reduction_file(capsys) -> None:
    exit_code = reduce_coupon.main(
        [
            str(ANALYSIS_PATH),
            "examples/missing-reduction.json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Fel:" in captured.err


def test_execute_rejects_invalid_namespace() -> None:
    with pytest.raises(TypeError, match="Namespace"):
        reduce_coupon.execute(
            object()  # type: ignore[arg-type]
        )


def test_execute_rejects_invalid_runner() -> None:
    with pytest.raises(TypeError, match="CouponReductionFileRunner"):
        reduce_coupon.execute(
            create_arguments(),
            runner=object(),  # type: ignore[arg-type]
        )