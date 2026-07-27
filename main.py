"""
Pro Vision Engine
Entry point for the application.
"""

from pathlib import Path
from src.models.match import Match

def print_banner() -> None:
    print("=" * 60)
    print("⚽  Pro Vision Engine")
    print("Version: 0.1.0-alpha")
    print("=" * 60)


def show_project_location() -> None:
    project_root = Path(__file__).parent.resolve()
    print(f"Project location: {project_root}")


def main() -> None:
    print_banner()
    show_project_location()

    match = Match(
        match_number=1,
        home_team="Arsenal",
        away_team="Chelsea",
    )

    print()
    print("Första matchobjektet:")
    print(match)


if __name__ == "__main__":
    main()