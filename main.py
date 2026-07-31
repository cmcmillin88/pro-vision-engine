"""Command-line entry point for Pro Vision Engine."""

from pathlib import Path

from src.importer.text_importer import TextImporter
from src.models.game_type import GameType
from src.validators.coupon_validator import CouponValidator


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


def load_demo_coupon():
    """Load the Topptipset demonstration coupon."""

    coupon_file = PROJECT_ROOT / "examples" / "kupong.txt"

    importer = TextImporter()

    return importer.load_coupon(
        coupon_file,
        game_type=GameType.TOPPTIPSET,
        coupon_id="DEMO-TT-001",
    )


def main() -> None:
    """Run the Pro Vision Engine demonstration."""

    show_banner()
    show_project_location()

    coupon = load_demo_coupon()

    validator = CouponValidator()
    validator.validate(coupon)

    print()
    print("Coupon validation: PASSED")
    print()
    print(coupon)


if __name__ == "__main__":
    main()