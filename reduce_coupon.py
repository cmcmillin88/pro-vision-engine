"""Command-line entry point for practical coupon analysis and reduction."""

import argparse
import sys
from pathlib import Path
from typing import Sequence

from src.exporters.coupon_reduction_console_renderer import (
    CouponReductionConsoleRenderer,
)
from src.exporters.coupon_reduction_result_json_exporter import (
    CouponReductionResultJsonExporter,
)
from src.services.coupon_reduction_file_runner import (
    CouponReductionFileRunner,
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the practical coupon-reduction argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Analyze one Project 13 coupon JSON file, import a practical "
            "reduction configuration and create the final surviving rows."
        )
    )

    parser.add_argument(
        "analysis_path",
        type=Path,
        help="Path to a p13-analysis-input-v1 JSON file.",
    )
    parser.add_argument(
        "reduction_path",
        type=Path,
        help="Path to a p13-reduction-input-v1 JSON file.",
    )
    parser.add_argument(
        "--format",
        choices=("console", "json"),
        default="console",
        dest="output_format",
        help="Select Swedish console output or versioned JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        dest="output_path",
        help="Optional UTF-8 output file. Defaults to standard output.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON when --format json is selected.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=20,
        help="Maximum number of surviving rows shown in console output.",
    )

    return parser


def execute(
    arguments: argparse.Namespace,
    *,
    runner: CouponReductionFileRunner | None = None,
) -> str:
    """Execute one parsed practical reduction command."""

    if not isinstance(arguments, argparse.Namespace):
        raise TypeError("arguments must be an argparse.Namespace.")

    if runner is not None and not isinstance(
        runner,
        CouponReductionFileRunner,
    ):
        raise TypeError(
            "runner must be a CouponReductionFileRunner or None."
        )

    resolved_runner = runner or CouponReductionFileRunner()
    reduction_run = resolved_runner.run_files(
        arguments.analysis_path,
        arguments.reduction_path,
    )

    if arguments.output_format == "json":
        indent = None if arguments.compact else 2
        output_text = CouponReductionResultJsonExporter().to_json(
            reduction_run,
            indent=indent,
        )
    else:
        output_text = CouponReductionConsoleRenderer(
            max_rows=arguments.max_rows
        ).render(reduction_run)

    if arguments.output_path is not None:
        arguments.output_path.parent.mkdir(parents=True, exist_ok=True)
        arguments.output_path.write_text(
            output_text + "\n",
            encoding="utf-8",
        )
    else:
        print(output_text)

    return output_text


def main(argv: Sequence[str] | None = None) -> int:
    """Run the practical reduction command and return an exit code."""

    parser = create_argument_parser()
    arguments = parser.parse_args(argv)

    try:
        execute(arguments)
    except (
        FileNotFoundError,
        IndexError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(f"Fel: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())