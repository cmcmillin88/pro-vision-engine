"""Tests for the practical coupon-analysis command line."""

import json
from argparse import Namespace
from pathlib import Path

import pytest

from analyze_coupon import (
    create_argument_parser,
    execute,
    main,
)
from tests.coupon_analysis_run_helpers import EXAMPLE_PATH


def test_parser_uses_console_defaults() -> None:
    arguments = create_argument_parser().parse_args(
        [
            str(EXAMPLE_PATH),
        ]
    )

    assert arguments.input_path == EXAMPLE_PATH
    assert arguments.output_format == "console"
    assert arguments.output_path is None
    assert arguments.compact is False


def test_parser_supports_json_output() -> None:
    arguments = create_argument_parser().parse_args(
        [
            str(EXAMPLE_PATH),
            "--format",
            "json",
            "--compact",
        ]
    )

    assert arguments.output_format == "json"
    assert arguments.compact is True


def test_execute_returns_console_text(
    capsys,
) -> None:
    arguments = create_argument_parser().parse_args(
        [
            str(EXAMPLE_PATH),
        ]
    )

    output_text = execute(
        arguments
    )
    captured = capsys.readouterr()

    assert output_text in captured.out
    assert "Turkos ram:" in output_text


def test_execute_returns_json_text(
    capsys,
) -> None:
    arguments = create_argument_parser().parse_args(
        [
            str(EXAMPLE_PATH),
            "--format",
            "json",
            "--compact",
        ]
    )

    output_text = execute(
        arguments
    )
    captured = capsys.readouterr()

    assert output_text in captured.out
    assert json.loads(
        output_text
    )["schema_version"] == "p13-analysis-result-v1"


def test_execute_writes_utf8_output_file(
    tmp_path: Path,
    capsys,
) -> None:
    output_path = tmp_path / "nested" / "analysis-result.json"
    arguments = create_argument_parser().parse_args(
        [
            str(EXAMPLE_PATH),
            "--format",
            "json",
            "--output",
            str(output_path),
        ]
    )

    output_text = execute(
        arguments
    )
    captured = capsys.readouterr()

    assert captured.out == ""
    assert output_path.read_text(
        encoding="utf-8"
    ) == output_text + "\n"


def test_main_returns_success_for_example(
    capsys,
) -> None:
    exit_code = main(
        [
            str(EXAMPLE_PATH),
            "--format",
            "json",
            "--compact",
        ]
    )
    capsys.readouterr()

    assert exit_code == 0


def test_main_returns_error_for_missing_file(
    capsys,
) -> None:
    exit_code = main(
        [
            "examples/missing-analysis-input.json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Fel:" in captured.err


def test_execute_rejects_invalid_namespace() -> None:
    with pytest.raises(
        TypeError,
        match="Namespace",
    ):
        execute(
            object()  # type: ignore[arg-type]
        )


def test_execute_rejects_invalid_runner() -> None:
    arguments = Namespace(
        input_path=EXAMPLE_PATH,
        output_format="console",
        output_path=None,
        compact=False,
    )

    with pytest.raises(
        TypeError,
        match="CouponAnalysisFileRunner",
    ):
        execute(
            arguments,
            runner=object(),  # type: ignore[arg-type]
        )