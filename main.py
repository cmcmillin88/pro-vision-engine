"""Command-line entry point for Pro Vision Engine."""

import argparse
from pathlib import Path

from src.exporters.coupon_json_exporter import (
    CouponJsonExporter,
)
from src.models.coupon import Coupon
from src.services.demo_coupon_catalog import (
    DemoCouponCatalog,
)


VERSION = "0.1.0-alpha"
PROJECT_ROOT = Path(__file__).resolve().parent
DEMO_COUPON_DIRECTORY = (
    PROJECT_ROOT
    / "examples"
    / "svenska_spel"
)


def create_argument_parser(
    available_game_types: tuple[str, ...],
) -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Import and validate a local Svenska Spel "
            "demonstration coupon."
        )
    )

    parser.add_argument(
        "game_type",
        nargs="?",
        default="topptipset",
        choices=available_game_types,
        help=(
            "Demo coupon to load. "
            "Defaults to topptipset."
        ),
    )

    parser.add_argument(
        "--output",
        choices=("console", "json"),
        default="console",
        help=(
            "Select human-readable console output "
            "or machine-readable JSON."
        ),
    )

    return parser


def show_banner() -> None:
    """Display the Pro Vision Engine banner."""

    print("=" * 60)
    print("⚽ Pro Vision Engine")
    print(f"Version: {VERSION}")
    print("=" * 60)


def show_project_location() -> None:
    """Display the project directory."""

    print(f"Project location: {PROJECT_ROOT}")


def show_console_output(
    coupon: Coupon,
) -> None:
    """Display a coupon in a human-readable format."""

    show_banner()
    show_project_location()

    print()
    print(
        f"Selected demo: "
        f"{coupon.game_type.display_name}"
    )
    print(
        "Local Svenska Spel JSON import "
        "and validation: PASSED"
    )
    print()
    print(coupon)


def show_json_output(
    coupon: Coupon,
) -> None:
    """Display a coupon as machine-readable JSON."""

    exporter = CouponJsonExporter()

    print(exporter.to_json(coupon))


def main() -> None:
    """Run the Pro Vision Engine demonstration."""

    catalog = DemoCouponCatalog(
        DEMO_COUPON_DIRECTORY
    )

    arguments = create_argument_parser(
        catalog.available_game_types
    ).parse_args()

    coupon = catalog.load(
        arguments.game_type
    )

    if arguments.output == "json":
        show_json_output(coupon)
        return

    show_console_output(coupon)


if __name__ == "__main__":
    main()