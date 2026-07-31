"""Command-line entry point for Pro Vision Engine."""

import argparse
from pathlib import Path

from src.exporters.coupon_json_exporter import (
    CouponJsonExporter,
)
from src.importer.svenska_spel_importer import (
    SvenskaSpelImporter,
)
from src.models.coupon import Coupon
from src.providers.svenska_spel.json_client import (
    SvenskaSpelJsonClient,
)
from src.services.coupon_import_service import (
    CouponImportService,
)


VERSION = "0.1.0-alpha"
PROJECT_ROOT = Path(__file__).resolve().parent

DEMO_COUPON_FILES = {
    "topptipset": "topptipset.json",
    "stryktipset": "stryktipset.json",
    "europatipset": "europatipset.json",
}


def create_argument_parser() -> argparse.ArgumentParser:
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
        choices=tuple(DEMO_COUPON_FILES),
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


def load_demo_coupon(
    game_type_name: str,
) -> Coupon:
    """Import and validate the selected Svenska Spel JSON coupon."""

    filename = DEMO_COUPON_FILES[game_type_name]

    coupon_file = (
        PROJECT_ROOT
        / "examples"
        / "svenska_spel"
        / filename
    )

    client = SvenskaSpelJsonClient()
    importer = SvenskaSpelImporter(client)
    import_service = CouponImportService(importer)

    return import_service.import_coupon(
        coupon_file
    )


def show_console_output(
    coupon: Coupon,
) -> None:
    """Display a coupon in a human-readable format."""

    show_banner()
    show_project_location()

    print()
    print(f"Selected demo: {coupon.game_type.display_name}")
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

    arguments = create_argument_parser().parse_args()

    coupon = load_demo_coupon(
        arguments.game_type
    )

    if arguments.output == "json":
        show_json_output(coupon)
        return

    show_console_output(coupon)


if __name__ == "__main__":
    main()