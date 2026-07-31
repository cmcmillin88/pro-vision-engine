"""Export the frontend TypeScript contract."""

import argparse
import json
from pathlib import Path
from typing import Any

from src.exporters.typescript_contract_exporter import (
    TypeScriptContractExporter,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = (
    PROJECT_ROOT
    / "contracts"
    / "openapi.json"
)
DEFAULT_OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "contracts"
    / "typescript"
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate frontend TypeScript types and "
            "an API client from the OpenAPI contract."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="Path to the OpenAPI JSON file.",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help=(
            "Directory for generated "
            "TypeScript files."
        ),
    )

    return parser


def load_openapi_document(
    path: Path,
) -> dict[str, Any]:
    """Read and decode an OpenAPI JSON document."""

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as error:
        raise ValueError(
            f"OpenAPI file was not found: {path}"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError(
            "OpenAPI file contains "
            f"invalid JSON: {path}"
        ) from error

    if not isinstance(payload, dict):
        raise ValueError(
            "OpenAPI root must be "
            "a JSON object."
        )

    return payload


def display_path(
    path: Path,
) -> Path:
    """Return a readable project-relative path."""

    try:
        return path.relative_to(
            PROJECT_ROOT
        )
    except ValueError:
        return path


def main() -> None:
    """Generate the frontend TypeScript contract."""

    arguments = (
        create_argument_parser()
        .parse_args()
    )
    openapi_document = (
        load_openapi_document(
            arguments.input
        )
    )

    exporter = (
        TypeScriptContractExporter()
    )
    written_paths = exporter.write(
        openapi_document,
        arguments.output_directory,
    )

    print(
        "TypeScript contract "
        "exported successfully."
    )

    for path in written_paths:
        print(
            f"Output: "
            f"{display_path(path)}"
        )


if __name__ == "__main__":
    main()