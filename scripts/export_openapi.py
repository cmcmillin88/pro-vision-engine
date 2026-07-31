"""Export the current Pro Vision Engine OpenAPI contract."""

import argparse
from pathlib import Path

from src.api.app import app
from src.exporters.openapi_json_exporter import (
    OpenApiJsonExporter,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = Path(
    "contracts"
) / "openapi.json"


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Export the current Pro Vision Engine "
            "OpenAPI contract to a JSON file."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=(
            "Destination for the generated OpenAPI JSON file. "
            "Relative paths are resolved from the project root."
        ),
    )

    return parser


def resolve_output_path(
    output_path: Path,
) -> Path:
    """Resolve an output path against the project root."""

    if output_path.is_absolute():
        return output_path

    return PROJECT_ROOT / output_path


def display_output_path(
    output_path: Path,
) -> Path:
    """Return a readable path for terminal output."""

    try:
        return output_path.relative_to(
            PROJECT_ROOT
        )
    except ValueError:
        return output_path


def main() -> None:
    """Export the application's current OpenAPI contract."""

    arguments = create_argument_parser().parse_args()

    output_path = resolve_output_path(
        arguments.output
    )

    exporter = OpenApiJsonExporter()

    written_path = exporter.write(
        app,
        output_path,
    )

    print("OpenAPI contract exported successfully.")
    print(
        f"Output: "
        f"{display_output_path(written_path)}"
    )


if __name__ == "__main__":
    main()