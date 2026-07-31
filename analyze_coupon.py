"""Command-line entry point for practical coupon analysis."""

import argparse
import sys
from pathlib import Path
from typing import Sequence

from src.exporters.coupon_analysis_console_renderer import (
    CouponAnalysisConsoleRenderer,
)
from src.exporters.coupon_analysis_result_json_exporter import (
    CouponAnalysisResultJsonExporter,
)
from src.services.coupon_analysis_file_runner import (
    CouponAnalysisFileRunner,
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the practical coupon-analysis argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Import a Project 13 coupon-analysis JSON file, "
            "run the complete engine and create the turquoise frame."
        )
    )

    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to a p13-analysis-input-v1 JSON file.",
    )
    parser.add_argument(
        "--format",
        choices=(
            "console",
            "json",
        ),
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

    return parser


def execute(
    arguments: argparse.Namespace,
    *,
    runner: CouponAnalysisFileRunner | None = None,
) -> str:
    """Execute one parsed practical analysis command."""

    if not isinstance(
        arguments,
        argparse.Namespace,
    ):
        raise TypeError(
            "arguments must be an argparse.Namespace."
        )

    if (
        runner is not None
        and not isinstance(
            runner,
            CouponAnalysisFileRunner,
        )
    ):
        raise TypeError(
            "runner must be a CouponAnalysisFileRunner or None."
        )

    resolved_runner = runner or CouponAnalysisFileRunner()
    analysis_run = resolved_runner.run_file(
        arguments.input_path
    )

    if arguments.output_format == "json":
        indent = (
            None
            if arguments.compact
            else 2
        )
        output_text = (
            CouponAnalysisResultJsonExporter().to_json(
                analysis_run,
                indent=indent,
            )
        )
    else:
        output_text = CouponAnalysisConsoleRenderer().render(
            analysis_run
        )

    if arguments.output_path is not None:
        arguments.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        arguments.output_path.write_text(
            output_text + "\n",
            encoding="utf-8",
        )
    else:
        print(
            output_text
        )

    return output_text


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Run the practical command and return a process exit code."""

    parser = create_argument_parser()
    arguments = parser.parse_args(
        argv
    )

    try:
        execute(
            arguments
        )
    except (
        FileNotFoundError,
        TypeError,
        ValueError,
    ) as error:
        print(
            f"Fel: {error}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )