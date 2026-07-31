"""Command-line entry point for Pro Vision Engine."""

from pathlib import Path

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


def show_banner() -> None:
    """Display the Pro Vision Engine banner."""

    print("=" * 60)
    print("⚽ Pro Vision Engine")
    print(f"Version: {VERSION}")
    print("=" * 60)


def show_project_location() -> None:
    """Display the project directory."""

    print(f"Project location: {PROJECT_ROOT}")


def load_demo_coupon() -> Coupon:
    """Import and validate the local Svenska Spel JSON coupon."""

    coupon_file = (
        PROJECT_ROOT
        / "examples"
        / "svenska_spel"
        / "topptipset.json"
    )

    client = SvenskaSpelJsonClient()
    importer = SvenskaSpelImporter(client)
    import_service = CouponImportService(importer)

    return import_service.import_coupon(
        coupon_file
    )


def main() -> None:
    """Run the Pro Vision Engine demonstration."""

    show_banner()
    show_project_location()

    coupon = load_demo_coupon()

    print()
    print(
        "Local Svenska Spel JSON import "
        "and validation: PASSED"
    )
    print()
    print(coupon)


if __name__ == "__main__":
    main()